import asyncio
import unittest
from unittest.mock import patch
from weaver_framework.microservice.base_microservice import BaseMicroservice
from weaver_framework.microservice.runner import (EXIT_FAILURE,
                                                  EXIT_INTERRUPTED,
                                                  EXIT_SUCCESS,
                                                  run_microservice)


class OneShotService(BaseMicroservice):
    """Runs a single short task, optionally failing."""

    SERVICE_NAME = "one-shot"

    def __init__(self, initialise_ok=True, task_fails=False):
        super().__init__()
        self._initialise_ok = initialise_ok
        self._task_fails = task_fails

    async def _initialise(self) -> bool:
        return self._initialise_ok

    async def _create_tasks(self):
        async def work():
            if self._task_fails:
                raise RuntimeError("task failed")

        return [asyncio.create_task(work())]

    async def _shutdown(self):
        return None

    def install_signal_handlers(self):
        # Record the call without touching real process signal handlers.
        self.signal_handlers_installed = True


class TestRunMicroservice(unittest.TestCase):
    """Plain TestCase: run_microservice starts its own event loop."""

    def test_clean_run_returns_success(self):
        service = OneShotService()

        self.assertEqual(EXIT_SUCCESS, run_microservice(service))
        self.assertTrue(service.signal_handlers_installed)

    def test_initialise_failure_returns_failure(self):
        service = OneShotService(initialise_ok=False)

        with self.assertLogs(service.logger, level="ERROR"):
            self.assertEqual(EXIT_FAILURE, run_microservice(service))

    def test_task_failure_returns_failure(self):
        service = OneShotService(task_fails=True)

        with self.assertLogs(service.logger, level="ERROR"):
            self.assertEqual(EXIT_FAILURE, run_microservice(service))

    def test_keyboard_interrupt_returns_interrupted(self):
        def interrupted(coroutine):
            coroutine.close()
            raise KeyboardInterrupt

        with patch("weaver_framework.microservice.runner.asyncio.run",
                   side_effect=interrupted):
            self.assertEqual(EXIT_INTERRUPTED,
                             run_microservice(OneShotService()))
