import asyncio
import logging
import os
import unittest
from unittest.mock import AsyncMock, patch

from weaver_framework.microservice.base_microservice import (
    BaseMicroservice
)


class TestMicroservice(BaseMicroservice):

    async def _create_tasks(self):
        return []

    async def _shutdown(self):
        return None


class TestMicroserviceBaseMicroservice(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self._service = TestMicroservice()

    def test_logger_property(self):
        self.assertIsInstance(
            self._service.logger,
            logging.Logger
        )

    def test_shutdown_event_property(self):
        self.assertIsInstance(
            self._service.shutdown_event,
            asyncio.Event
        )

    def test_shutdown_complete_property(self):
        self.assertIsInstance(
            self._service.shutdown_complete,
            asyncio.Event
        )

    def test_is_initialised_defaults_to_false(self):
        self.assertFalse(
            self._service.is_initialised
        )

    def test_is_stopping_defaults_to_false(self):
        self.assertFalse(
            self._service.is_stopping
        )

    async def test_initialise_success(self):
        self._service._initialise = AsyncMock(return_value=True)

        result = await self._service.initialise()

        self.assertTrue(result)
        self.assertTrue(self._service.is_initialised)

    async def test_initialise_failure_calls_stop(self):
        self._service._initialise = AsyncMock(return_value=False)
        self._service.stop = AsyncMock()

        result = await self._service.initialise()

        self.assertFalse(result)

        self._service.stop.assert_awaited_once()

    async def test_run_without_initialisation_returns_early(self):
        with self.assertLogs(
                self._service.logger,
                level="WARNING") as logs:

            await self._service.run()

        self.assertIn(
            "Microservice is not initialised",
            logs.output[0]
        )

    async def test_run_executes_tasks(self):
        self._service._is_initialised = True

        async def task():
            return "done"

        mock_task = asyncio.create_task(task())

        self._service._create_tasks = AsyncMock(
            return_value=[mock_task]
        )

        self._service.stop = AsyncMock()

        await self._service.run()

        self._service.stop.assert_awaited_once()

    async def test_run_logs_task_exception(self):
        self._service._is_initialised = True

        async def failing_task():
            raise RuntimeError("Task failure")

        mock_task = asyncio.create_task(failing_task())

        self._service._create_tasks = AsyncMock(
            return_value=[mock_task]
        )

        self._service.stop = AsyncMock()

        with self.assertLogs(
                self._service.logger,
                level="ERROR") as logs:

            await self._service.run()

        self.assertIn(
            "Task terminated with exception",
            logs.output[0]
        )

    async def test_run_handles_cancelled_error(self):
        self._service._is_initialised = True

        self._service._create_tasks = AsyncMock(
            side_effect=asyncio.CancelledError
        )

        self._service.stop = AsyncMock()

        with self.assertRaises(asyncio.CancelledError):
            await self._service.run()

    async def test_stop_sets_shutdown_flags(self):
        self._service._tasks = []

        self._service._shutdown = AsyncMock()

        await self._service.stop()

        self.assertTrue(
            self._service.is_stopping
        )

        self.assertTrue(
            self._service.shutdown_event.is_set()
        )

        self.assertTrue(
            self._service.shutdown_complete.is_set()
        )

        self._service._shutdown.assert_awaited_once()

    async def test_stop_returns_if_already_stopping(self):
        self._service._is_stopping = True

        self._service._shutdown = AsyncMock()

        await self._service.stop()

        self._service._shutdown.assert_not_awaited()

    async def test_stop_cancels_tasks(self):

        async def blocking_task():
            await asyncio.sleep(10)

        task = asyncio.create_task(blocking_task())

        self._service._tasks = [task]

        self._service._shutdown = AsyncMock()

        await self._service.stop()

        self.assertTrue(task.cancelled())

    async def test_default_initialise_returns_true(self):
        result = await self._service._initialise()

        self.assertTrue(result)

    @patch.dict(os.environ, {}, clear=True)
    def test_check_for_configuration_defaults(self):
        result = BaseMicroservice._check_for_configuration(
            "CONFIG_FILE",
            "CONFIG_REQUIRED"
        )

        self.assertEqual(
            (None, False, None),
            result
        )

    @patch.dict(
        os.environ,
        {
            "CONFIG_REQUIRED": "true",
            "CONFIG_FILE": "/tmp/config.json"
        },
        clear=True
    )
    def test_check_for_configuration_required_and_present(self):
        result = BaseMicroservice._check_for_configuration(
            "CONFIG_FILE",
            "CONFIG_REQUIRED"
        )

        self.assertEqual(
            (None, True, "/tmp/config.json"),
            result
        )

    @patch.dict(
        os.environ,
        {
            "CONFIG_REQUIRED": "true"
        },
        clear=True
    )
    def test_check_for_configuration_missing_required_file(self):
        error, required, config = (
            BaseMicroservice._check_for_configuration(
                "CONFIG_FILE",
                "CONFIG_REQUIRED"
            )
        )

        self.assertEqual(
            "Configuration file is not defined",
            error
        )

        self.assertTrue(required)

        self.assertIsNone(config)

    @patch.dict(
        os.environ,
        {
            "CONFIG_REQUIRED": "invalid"
        },
        clear=True
    )
    def test_check_for_configuration_invalid_boolean(self):
        error, required, config = (
            BaseMicroservice._check_for_configuration(
                "CONFIG_FILE",
                "CONFIG_REQUIRED"
            )
        )

        self.assertIn(
            "Invalid value",
            error
        )

        self.assertFalse(required)

        self.assertIsNone(config)

    async def test_run_handles_keyboard_interrupt(self):
        self._service._is_initialised = True

        async def raise_keyboard_interrupt():
            raise KeyboardInterrupt

        self._service._create_tasks = raise_keyboard_interrupt

        self._service.stop = AsyncMock()

        with self.assertLogs(
                self._service.logger,
                level="DEBUG") as logs:
            await self._service.run()

        self.assertTrue(
            self._service.shutdown_event.is_set()
        )

        self.assertTrue(
            any(
                "Keyboard interrupt received" in log
                for log in logs.output
            )
        )

        self._service.stop.assert_awaited_once()
