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
import typing
from .logging_configuration import LoggingConfiguration
from weaver_framework.constants import BOOL_TRUE_VALUES, BOOL_FALSE_VALUES


class BaseMicroservice(abc.ABC):
    """Base microservice class."""
    __slots__ = ["_is_initialised",
                 "_is_stopping",
                 "_logger",
                 "_logger_config",
                 "_shutdown_complete",
                 "_shutdown_event",
                 "_tasks"]

    SERVICE_NAME: str = "Microservice"

    def __init__(self, logger_config: LoggingConfiguration | None = None) -> None:
        self._is_initialised: bool = False
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

            results = await asyncio.gather(*self._tasks,
                                           return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    self._logger.error(
                        "Task terminated with exception",
                        exc_info=result
                    )

        except KeyboardInterrupt:
            self._logger.debug("Service: Keyboard interrupt received.")
            self._shutdown_event.set()

        except asyncio.CancelledError:
            self._logger.debug("Service: Cancellation received.")
            raise

        finally:
            self._logger.info("Exiting microservice...")
            await self.stop()
            self._logger.info("Shutdown complete.")

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
