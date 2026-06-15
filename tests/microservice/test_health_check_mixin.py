import http
import json
import unittest

import quart

from weaver_framework.microservice.base_microservice import BaseMicroservice
from weaver_framework.microservice.health_check_mixin import HealthCheckMixin


class ConcreteService(BaseMicroservice, HealthCheckMixin):

    SERVICE_NAME = "test-service"

    async def _create_tasks(self):
        return []

    async def _shutdown(self):
        pass


class CustomHealthService(BaseMicroservice, HealthCheckMixin):

    SERVICE_NAME = "custom-service"

    async def _create_tasks(self):
        return []

    async def _shutdown(self):
        pass

    async def _get_health_data(self) -> dict:
        return {"database": "ok"}


class CustomPathService(BaseMicroservice, HealthCheckMixin):

    SERVICE_NAME = "custom-path-service"
    HEALTH_CHECK_PATH = "/healthz"

    async def _create_tasks(self):
        return []

    async def _shutdown(self):
        pass


class TestHealthCheckMixin(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self._app = quart.Quart(__name__)
        self._service = ConcreteService()
        self._service.register_health_check(self._app)

    async def test_returns_503_when_not_initialised(self):

        async with self._app.test_client() as client:
            response = await client.get("/health")

        self.assertEqual(
            http.HTTPStatus.SERVICE_UNAVAILABLE,
            response.status_code
        )

    async def test_returns_200_when_initialised(self):

        self._service._is_initialised = True

        async with self._app.test_client() as client:
            response = await client.get("/health")

        self.assertEqual(
            http.HTTPStatus.OK,
            response.status_code
        )

    async def test_response_contains_service_name(self):

        async with self._app.test_client() as client:
            response = await client.get("/health")

        body = json.loads(await response.get_data())

        self.assertEqual("test-service", body["service"])

    async def test_response_status_is_unavailable_when_not_initialised(self):

        async with self._app.test_client() as client:
            response = await client.get("/health")

        body = json.loads(await response.get_data())

        self.assertEqual("unavailable", body["status"])

    async def test_response_status_is_healthy_when_initialised(self):

        self._service._is_initialised = True

        async with self._app.test_client() as client:
            response = await client.get("/health")

        body = json.loads(await response.get_data())

        self.assertEqual("healthy", body["status"])

    async def test_response_initialised_is_false_when_not_initialised(self):

        async with self._app.test_client() as client:
            response = await client.get("/health")

        body = json.loads(await response.get_data())

        self.assertFalse(body["initialised"])

    async def test_response_initialised_is_true_when_initialised(self):

        self._service._is_initialised = True

        async with self._app.test_client() as client:
            response = await client.get("/health")

        body = json.loads(await response.get_data())

        self.assertTrue(body["initialised"])

    async def test_content_type_is_json(self):

        async with self._app.test_client() as client:
            response = await client.get("/health")

        self.assertIn("application/json", response.content_type)

    async def test_custom_health_data_is_included_in_response(self):

        app = quart.Quart(__name__)
        service = CustomHealthService()
        service._is_initialised = True
        service.register_health_check(app)

        async with app.test_client() as client:
            response = await client.get("/health")

        body = json.loads(await response.get_data())

        self.assertEqual("ok", body["database"])

    async def test_default_get_health_data_returns_empty_dict(self):

        result = await self._service._get_health_data()

        self.assertEqual({}, result)

    async def test_custom_health_check_path(self):

        app = quart.Quart(__name__)
        service = CustomPathService()
        service.register_health_check(app)

        async with app.test_client() as client:
            response = await client.get("/healthz")

        self.assertEqual(
            http.HTTPStatus.SERVICE_UNAVAILABLE,
            response.status_code
        )

    async def test_default_health_check_path(self):

        self.assertEqual("/health", self._service.HEALTH_CHECK_PATH)
