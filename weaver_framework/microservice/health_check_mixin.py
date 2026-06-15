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
import http
import json
import quart


class HealthCheckMixin:
    """Mixin that adds a health check endpoint to a BaseMicroservice subclass.

    Registers a GET route on the provided Quart app that returns service
    health status as JSON. The response includes the service name,
    initialisation state, and any custom fields provided by the subclass.

    The HTTP status code reflects readiness:
        - ``200 OK`` when the service is initialised and healthy.
        - ``503 Service Unavailable`` when the service is not yet initialised.

    Usage::

        class MyService(BaseMicroservice, HealthCheckMixin):

            async def _initialise(self) -> bool:
                self.register_health_check(self._app)
                return True

    To add custom health fields, override ``_get_health_data``::

        class MyService(BaseMicroservice, HealthCheckMixin):

            async def _get_health_data(self) -> dict:
                return {"database": await self._check_db()}

    Attributes:
        HEALTH_CHECK_PATH: URL path for the health check endpoint.
    """
    # pylint: disable=too-few-public-methods

    HEALTH_CHECK_PATH: str = "/health"

    def register_health_check(self, app: quart.Quart) -> None:
        """Register the health check route on the given Quart app.

        Args:
            app: The Quart application instance to register the route on.
        """
        app.add_url_rule(
            self.HEALTH_CHECK_PATH,
            "health_check",
            self._health_check_handler,
            methods=["GET"]
        )

    async def _get_health_data(self) -> dict:
        """Return custom fields to include in the health check response.

        Override this method to add service-specific health information
        such as database connectivity or downstream service status.

        Returns:
            A dictionary of additional fields to merge into the response.
        """
        return {}

    async def _health_check_handler(self) -> quart.Response:
        """Handle GET requests to the health check endpoint.

        Returns:
            A JSON response with service health status.
        """
        is_healthy: bool = self._is_initialised  # type: ignore[attr-defined]

        data = {
            "status": "healthy" if is_healthy else "unavailable",
            "service": self.SERVICE_NAME,  # type: ignore[attr-defined]
            "initialised": is_healthy,
        }

        custom_data = await self._get_health_data()
        data.update(custom_data)

        status_code = (http.HTTPStatus.OK
                       if is_healthy
                       else http.HTTPStatus.SERVICE_UNAVAILABLE)

        return quart.Response(
            json.dumps(data),
            status=status_code,
            content_type="application/json"
        )
