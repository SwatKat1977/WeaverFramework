import asyncio
import signal
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from weaver_framework.microservice.base_microservice import BaseMicroservice


class LifecycleService(BaseMicroservice):

    SERVICE_NAME = "lifecycle-service"

    def __init__(self, tasks=None):
        super().__init__()
        self.task_factories = tasks or []

    async def _create_tasks(self):
        return [asyncio.create_task(factory()) for factory in self.task_factories]

    async def _shutdown(self):
        return None


class TestBaseMicroserviceLifecycle(unittest.IsolatedAsyncioTestCase):

    def test_failed_defaults_to_false(self):
        self.assertFalse(LifecycleService().failed)

    async def test_initialise_failure_marks_service_failed(self):
        service = LifecycleService()
        service._initialise = AsyncMock(return_value=False)

        self.assertFalse(await service.initialise())
        self.assertTrue(service.failed)

    async def test_failing_task_stops_other_tasks(self):
        """Fail fast: one task crashing stops the whole service."""
        blocker_cancelled = asyncio.Event()

        async def blocker():
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                blocker_cancelled.set()
                raise

        async def crasher():
            await asyncio.sleep(0.01)
            raise RuntimeError("boom")

        service = LifecycleService([blocker, crasher])
        await service.initialise()

        with self.assertLogs(service.logger, level="ERROR") as logs:
            await asyncio.wait_for(service.run(), timeout=5)

        self.assertTrue(service.failed)
        self.assertTrue(blocker_cancelled.is_set())
        self.assertTrue(service.shutdown_complete.is_set())
        self.assertIn("Task terminated with exception", logs.output[0])

    async def test_finished_task_does_not_stop_others(self):
        finished = []

        async def quick():
            finished.append("quick")

        async def slower():
            await asyncio.sleep(0.05)
            finished.append("slower")

        service = LifecycleService([quick, slower])
        await service.initialise()
        await asyncio.wait_for(service.run(), timeout=5)

        self.assertEqual(["quick", "slower"], finished)
        self.assertFalse(service.failed)

    async def test_cancelled_task_is_not_a_failure(self):
        async def cancels_itself():
            raise asyncio.CancelledError

        service = LifecycleService([cancels_itself])
        await service.initialise()
        await asyncio.wait_for(service.run(), timeout=5)

        self.assertFalse(service.failed)

    async def test_shutdown_request_stops_run(self):
        async def forever():
            await asyncio.sleep(60)

        service = LifecycleService([forever])
        await service.initialise()
        runner = asyncio.create_task(service.run())
        await asyncio.sleep(0.01)

        service.shutdown_event.set()
        await asyncio.wait_for(runner, timeout=5)

        self.assertFalse(service.failed)
        self.assertTrue(service.shutdown_complete.is_set())

    async def test_external_stop_waits_for_shutdown_to_complete(self):
        """run() must not return until a concurrent stop() has finished."""
        async def forever():
            await asyncio.sleep(60)

        shutdown_started = asyncio.Event()
        release_shutdown = asyncio.Event()

        async def slow_shutdown():
            shutdown_started.set()
            await release_shutdown.wait()

        service = LifecycleService([forever])
        service._shutdown = slow_shutdown
        await service.initialise()
        runner = asyncio.create_task(service.run())
        await asyncio.sleep(0.01)

        stopper = asyncio.create_task(service.stop())
        await shutdown_started.wait()
        await asyncio.sleep(0.05)
        self.assertFalse(runner.done())  # still waiting for shutdown

        release_shutdown.set()
        await asyncio.wait_for(asyncio.gather(runner, stopper), timeout=5)
        self.assertTrue(service.shutdown_complete.is_set())

    async def test_grace_period_lets_tasks_finish(self):
        finished_cleanly = asyncio.Event()

        class GracefulService(LifecycleService):
            SHUTDOWN_GRACE_PERIOD = 2.0

        service = GracefulService()

        async def watches_shutdown():
            await service.shutdown_event.wait()
            await asyncio.sleep(0.05)
            finished_cleanly.set()

        service.task_factories = [watches_shutdown]
        await service.initialise()
        runner = asyncio.create_task(service.run())
        await asyncio.sleep(0.01)

        await service.stop()
        await asyncio.wait_for(runner, timeout=5)

        self.assertTrue(finished_cleanly.is_set())

    async def test_without_grace_period_tasks_are_cancelled(self):
        service = LifecycleService()

        async def watches_shutdown():
            await service.shutdown_event.wait()
            await asyncio.sleep(60)

        service.task_factories = [watches_shutdown]
        await service.initialise()
        runner = asyncio.create_task(service.run())
        await asyncio.sleep(0.01)

        await asyncio.wait_for(service.stop(), timeout=5)
        await asyncio.wait_for(runner, timeout=5)

        self.assertTrue(service._tasks[0].cancelled())

    async def test_handle_signal_requests_shutdown(self):
        service = LifecycleService()

        with self.assertLogs(service.logger, level="INFO") as logs:
            service._handle_signal(signal.SIGTERM)

        self.assertTrue(service.shutdown_event.is_set())
        self.assertIn("SIGTERM", logs.output[0])

    async def test_install_signal_handlers_uses_event_loop(self):
        service = LifecycleService()
        loop = MagicMock()

        with patch("asyncio.get_running_loop", return_value=loop):
            service.install_signal_handlers()

        loop.add_signal_handler.assert_any_call(
            signal.SIGINT, service._handle_signal, signal.SIGINT)
        loop.add_signal_handler.assert_any_call(
            signal.SIGTERM, service._handle_signal, signal.SIGTERM)

    async def test_install_signal_handlers_falls_back_on_windows(self):
        """Without loop signal support, signal.signal is used instead."""
        service = LifecycleService()
        loop = asyncio.get_running_loop()
        installed = {}

        with patch.object(loop, "add_signal_handler",
                          side_effect=NotImplementedError), \
                patch("signal.signal",
                      side_effect=lambda sig, handler: installed.update({sig: handler})):
            service.install_signal_handlers()

        self.assertEqual({signal.SIGINT, signal.SIGTERM}, set(installed))

        installed[signal.SIGTERM](signal.SIGTERM, None)
        await asyncio.sleep(0)  # let call_soon_threadsafe run the handler

        self.assertTrue(service.shutdown_event.is_set())
