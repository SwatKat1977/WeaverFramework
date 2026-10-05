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
import asyncio
import typing
import hypercorn.asyncio
import hypercorn.config
import quart
from .base_microservice import BaseMicroservice
from .health_check_mixin import HealthCheckMixin
from .logging_configuration import LoggingConfiguration
from .server_configuration import ServerConfiguration


class QuartMicroservice(BaseMicroservice, HealthCheckMixin):
    """A microservice that serves a Quart app.

    The service owns its Quart app (``self.app``) and serves it with
    Hypercorn as one of its managed tasks, so the web server shares the
    service lifecycle:

    * ``_initialise()`` runs before the server accepts any requests.
    * ``/health`` returns 503 until initialised, 200 while running, and
      503 again once shutdown starts.
    * On stop, the server stops accepting connections and gives in-flight
      requests ``shutdown_timeout`` seconds to finish; then ``_shutdown()``
      runs.
    * If the server or any background task fails, the whole service stops.

    Use Weaver's ``_initialise()`` and ``_shutdown()`` for start-up and
    clean-up rather than Quart's ``before_serving``/``after_serving``.

    Example::

        class IdentityService(QuartMicroservice):
            SERVICE_NAME = "identity"

            async def _initialise(self) -> bool:
                self.app.register_blueprint(identity_api)
                return True

        if __name__ == "__main__":
            sys.exit(run_microservice(IdentityService()))

    In tests, use ``service.app.test_client()``; no server is started.
    """
    __slots__ = ["_app", "_server_config"]

    def __init__(self,
                 server_config: ServerConfiguration | None = None,
                 logger_config: LoggingConfiguration | None = None) -> None:
        super().__init__(logger_config)
        self._server_config: ServerConfiguration = (server_config or
                                                    ServerConfiguration())
        self._app: quart.Quart = quart.Quart(type(self).__module__)
        self.register_health_check(self._app)

    @property
    def app(self) -> quart.Quart:
        """The Quart application served by this microservice."""
        return self._app

    @property
    def server_config(self) -> ServerConfiguration:
        """The HTTP server settings."""
        return self._server_config

    def _shutdown_grace_period(self) -> float:
        """Time stop() allows for the server to drain before cancelling.

        Returns:
            Slightly longer than the server's own shutdown timeout.
        """
        return self._server_config.shutdown_timeout + 1.0

    async def _create_tasks(self) -> list[asyncio.Task[typing.Any]]:
        """Create the HTTP server task plus any background tasks."""
        server = asyncio.create_task(self._serve(),
                                     name=f"{self.SERVICE_NAME}-http")
        return [server, *await self._create_background_tasks()]

    async def _create_background_tasks(self) -> list[asyncio.Task[typing.Any]]:
        """Create tasks that run alongside the HTTP server.

        Override to add work such as an event consumer. Long-running tasks
        should stop when ``self.shutdown_event`` is set.

        Returns:
            The background tasks (none by default).
        """
        return []

    async def _shutdown(self) -> None:
        """Clean up after the server has stopped. Override if needed."""

    def _hypercorn_config(self) -> hypercorn.config.Config:
        """Build the Hypercorn configuration from the server settings."""
        config = hypercorn.config.Config()
        config.bind = [f"{self._server_config.host}:{self._server_config.port}"]
        config.graceful_timeout = float(self._server_config.shutdown_timeout)
        config.errorlog = self._logger
        config.accesslog = (self._logger if self._server_config.access_log
                            else None)
        return config

    async def _serve(self) -> None:
        """Serve the app until shutdown is requested."""
        self._logger.info("Serving HTTP on %s:%d",
                          self._server_config.host, self._server_config.port)
        await hypercorn.asyncio.serve(
            self._app,
            self._hypercorn_config(),
            shutdown_trigger=self._shutdown_event.wait)
