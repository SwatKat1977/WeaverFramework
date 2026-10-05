"""
Copyright 2026 Weaver Framework Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import abc
import asyncio
import logging
import os
import signal
import typing
from weaver_framework.constants import BOOL_TRUE_VALUES, BOOL_FALSE_VALUES
from .logging_configuration import LoggingConfiguration


class BaseMicroservice(abc.ABC):
    """Base microservice class."""
    # Lifecycle state is tracked in separate flags for clarity.
    # pylint: disable=too-many-instance-attributes
    __slots__ = ["_failed",
                 "_is_initialised",
                 "_is_stopping",
                 "_logger",
                 "_logger_config",
                 "_shutdown_complete",
                 "_shutdown_event",
                 "_tasks"]

    SERVICE_NAME: str = "Microservice"

    # Seconds that stop() waits for tasks to finish by themselves (after
    # shutdown_event is set) before cancelling them. 0 cancels immediately.
    SHUTDOWN_GRACE_PERIOD: float = 0.0

    def __init__(self, logger_config: LoggingConfiguration | None = None) -> None:
        self._is_initialised: bool = False
        self._failed: bool = False
        self._logger_config: LoggingConfiguration = (logger_config or
                                                     LoggingConfiguration())
        self._shutdown_event: asyncio.Event = asyncio.Event()
        self._shutdown_complete: asyncio.Event = asyncio.Event()
        self._tasks: list[asyncio.Task[typing.Any]] = []

        self._logger: logging.Logger = logging.getLogger(self.SERVICE_NAME)
        self._logger.propagate = False
        log_format = logging.Formatter(self._logger_config.format_string,
                                       self._logger_config.datetime_format)
        console_stream = logging.StreamHandler()
        console_stream.setFormatter(log_format)
        self._logger.setLevel(self._logger_config.level)

        if not self._logger.handlers:
            self._logger.addHandler(console_stream)

        self._is_stopping: bool = False

    @property
    def logger(self) -> logging.Logger:
        """
        Property getter for logger instance.

        Returns:
            Returns the logger instance.
        """
        return self._logger

    @property
    def shutdown_event(self) -> asyncio.Event:
        """
        Event used to signal the shutdown of the service.

        This event should be awaited or checked by background tasks to
        gracefully stop operations when the application is shutting down.
        """
        return self._shutdown_event

    @property
    def shutdown_complete(self) -> asyncio.Event:
        """
        Event that indicates the service has completed its shutdown process.

        This should be set when all shutdown tasks and cleanup procedures have
        finished, allowing other components (like the main app) to know when
        it's safe to exit.
        """
        return self._shutdown_complete

    @property
    def is_initialised(self) -> bool:
        """Whether the microservice has been initialised."""
        return self._is_initialised

    @property
    def is_stopping(self) -> bool:
        """Whether the microservice is currently stopping."""
        return self._is_stopping

    @property
    def failed(self) -> bool:
        """Whether the microservice stopped because of an error.

        True if initialisation failed or a task raised an exception.
        """
        return self._failed

    def install_signal_handlers(self) -> None:
        """Stop gracefully on SIGINT (Ctrl+C) and SIGTERM (e.g. docker stop).

        Must be called from inside the running event loop. Where the event
        loop does not support signal handlers (Windows), it falls back to
        :func:`signal.signal`.
        """
        loop = asyncio.get_running_loop()

        def fallback_handler(signum: int, _frame: typing.Any) -> None:
            loop.call_soon_threadsafe(self._handle_signal, signum)

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._handle_signal, sig)

            except NotImplementedError:
                signal.signal(sig, fallback_handler)

    def _handle_signal(self, signum: int) -> None:
        """Request a graceful shutdown in response to a signal."""
        self._logger.info("Received %s, shutting down.",
                          signal.Signals(signum).name)
        self._shutdown_event.set()

    async def initialise(self) -> bool:
        """
        Microservice initialisation.  It should return a boolean
        (True => Successful, False => Unsuccessful), upon success
        self._is_initialised is set to True.

        Returns:
            Boolean: True => Successful, False => Unsuccessful.
        """
        if await self._initialise():
            self._is_initialised = True
            return True

        self._failed = True
        await self.stop()

        return False

    async def run(self) -> None:
        """
        Start the microservice.
        """

        if not self._is_initialised:
            self._logger.warning(
                "Microservice is not initialised. Exiting run loop."
            )
            return

        self._logger.info("Microservice starting.")

        try:
            self._tasks = await self._create_tasks()
            await self._supervise_tasks()

        except KeyboardInterrupt:
            self._logger.debug("Service: Keyboard interrupt received.")
            self._shutdown_event.set()

        except asyncio.CancelledError:
            self._logger.debug("Service: Cancellation received.")
            raise

        finally:
            self._logger.info("Exiting microservice...")
            await self.stop()

            # If stop() was already running elsewhere, wait for it to finish.
            if self._is_stopping:
                await self._shutdown_complete.wait()

            self._logger.info("Shutdown complete.")

    def _shutdown_grace_period(self) -> float:
        """Seconds stop() lets tasks finish by themselves before cancelling.

        Returns:
            ``SHUTDOWN_GRACE_PERIOD`` by default; subclasses may override.
        """
        return self.SHUTDOWN_GRACE_PERIOD

    async def _supervise_tasks(self) -> None:
        """Wait on the service's tasks until it is time to stop.

        Returns when shutdown is requested (``shutdown_event`` is set, for
        example by a signal or :meth:`stop`), when every task has finished,
        or as soon as any task raises an exception. Failing fast means a
        broken service exits (and can be restarted) rather than carrying on
        half-working.
        """
        pending: set[asyncio.Task[typing.Any]] = set(self._tasks)
        shutdown_requested = asyncio.create_task(self._shutdown_event.wait())

        try:
            while pending and not self._shutdown_event.is_set():
                done, _ = await asyncio.wait(
                    pending | {shutdown_requested},
                    return_when=asyncio.FIRST_COMPLETED)

                for task in done - {shutdown_requested}:
                    pending.discard(task)
                    self._check_task_result(task)

        finally:
            shutdown_requested.cancel()

    def _check_task_result(self, task: asyncio.Task[typing.Any]) -> None:
        """Log a task's exception (if any) and trigger a fail-fast shutdown."""
        if task.cancelled():
            return

        exception = task.exception()

        if exception is not None:
            self._logger.error("Task terminated with exception",
                               exc_info=exception)
            self._failed = True
            self._shutdown_event.set()

    async def stop(self) -> None:
        """
        Stop the microservice, it will wait until shutdown has been marked as
        completed before calling the shutdown method.
        """

        if self._is_stopping or self._shutdown_complete.is_set():
            return

        self._is_stopping = True

        self._logger.info("Stopping microservice...")
        self._logger.info('Waiting for microservice shutdown to complete')

        self._shutdown_event.set()

        unfinished = [task for task in self._tasks if not task.done()]

        grace_period = self._shutdown_grace_period()

        if unfinished and grace_period > 0:
            await asyncio.wait(unfinished, timeout=grace_period)

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(
            *self._tasks,
            return_exceptions=True)

        await self._shutdown()

        self._shutdown_complete.set()

        self._logger.info('Microservice shutdown complete...')

    async def _initialise(self) -> bool:
        """
        Microservice initialisation.  It should return a boolean
        (True => Successful, False => Unsuccessful).

        Returns:
            Boolean: True => Successful, False => Unsuccessful.
        """
        return True

    @abc.abstractmethod
    async def _create_tasks(self) -> list[asyncio.Task[typing.Any]]:
        """Create and return the service's background tasks."""

    @abc.abstractmethod
    async def _shutdown(self) -> None:
        """Abstract method for microservice shutdown."""

    @classmethod
    def _check_for_configuration(cls,
                                 config_file_env: str,
                                 config_file_required_env: str) \
            -> tuple[str | None, bool, str | None]:
        """
        Check whether a configuration file is required and available based
        on environment variables.

        This function inspects two environment variables:
          - One specifying the path to a configuration file.
          - One specifying whether the configuration file is required.

        It validates the "required" flag against known boolean true/false
        values, determines whether the configuration file is missing when
        required, and returns the appropriate error status and state.

        Args:
            config_file_env (str):
                The name of the environment variable that holds the
                configuration file path.
            config_file_required_env (str):
                The name of the environment variable that indicates whether the
                configuration file is required.
                Expected values (case-insensitive):
                "true", "1", "yes", "on", "false", "0", "no", "off".

        Returns:
            tuple[str | None, bool, str | None]:
                A tuple containing:
                - `error_status` (str | None): An error message if a fatal
                  error occurred, otherwise None.
                - `config_file_required` (bool): Whether a configuration file
                  is required.
                - `config_file` (str | None): The configuration file path if
                  defined, otherwise None.

        Notes:
            - If `config_file_required_env` contains an invalid value, an error
              message is returned.
            - If a configuration file is required but not provided, an error
              message is returned.
            - If both checks pass, `error_status` will be None.

        Example:
            >>> os.environ["MY_CONFIG_FILE"] = "/etc/app.conf"
            >>> os.environ["MY_CONFIG_FILE_REQUIRED"] = "true"
            >>> cls._check_for_configuration("MY_CONFIG_FILE",
                                             "MY_CONFIG_FILE_REQUIRED")
            (None, True, "/etc/app.conf")
        """
        # Default return values
        config_file_required: bool = False
        error_status: typing.Optional[str] = None

        config_file = os.getenv(config_file_env)
        raw_required = os.getenv(config_file_required_env,
                                 "false").strip().lower()

        # Check if it's a true value.
        if raw_required in BOOL_TRUE_VALUES:
            config_file_required = True

        # Check if it's a false value.
        elif raw_required in BOOL_FALSE_VALUES:
            config_file_required = False

        # Unknown value - e.g. not true or false value.
        else:
            error_status = (f"Invalid value for {config_file_required_env}: "
                            f"'{raw_required}'")

        if not error_status and not config_file and config_file_required:
            error_status = "Configuration file is not defined"

        return error_status, config_file_required, config_file
