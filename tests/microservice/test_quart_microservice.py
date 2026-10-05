import asyncio
import http
import socket
import unittest
import aiohttp
import quart
from weaver_framework.microservice.quart_microservice import QuartMicroservice
from weaver_framework.microservice.server_configuration import \
    ServerConfiguration


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ExampleService(QuartMicroservice):

    SERVICE_NAME = "example-service"

    async def _initialise(self) -> bool:
        blueprint = quart.Blueprint("example", __name__)

        @blueprint.get("/hello")
        async def hello():
            return {"message": "hello"}

        @blueprint.get("/slow")
        async def slow():
            await asyncio.sleep(0.3)
            return {"message": "finished"}

        self.app.register_blueprint(blueprint)
        return True


class TestQuartMicroservice(unittest.IsolatedAsyncioTestCase):

    def test_app_is_a_quart_app(self):
        self.assertIsInstance(ExampleService().app, quart.Quart)

    def test_default_server_config(self):
        self.assertEqual(ServerConfiguration(), ExampleService().server_config)

    def test_grace_period_exceeds_server_timeout(self):
        service = ExampleService(ServerConfiguration(shutdown_timeout=4))

        self.assertGreater(service._shutdown_grace_period(), 4)

    async def test_health_follows_lifecycle_without_a_server(self):
        service = ExampleService()
        client = service.app.test_client()

        self.assertEqual(http.HTTPStatus.SERVICE_UNAVAILABLE,
                         (await client.get("/health")).status_code)

        await service.initialise()
        self.assertEqual(http.HTTPStatus.OK,
                         (await client.get("/health")).status_code)
        self.assertEqual({"message": "hello"},
                         await (await client.get("/hello")).get_json())

        service._is_stopping = True
        self.assertEqual(http.HTTPStatus.SERVICE_UNAVAILABLE,
                         (await client.get("/health")).status_code)

    async def test_default_background_tasks_and_shutdown(self):
        service = ExampleService()

        self.assertEqual([], await service._create_background_tasks())
        self.assertIsNone(await service._shutdown())

    async def test_create_tasks_includes_server_and_background(self):
        async def background():
            await asyncio.sleep(60)

        class WithBackground(ExampleService):
            async def _create_background_tasks(self):
                return [asyncio.create_task(background())]

        service = WithBackground()
        service._serve = lambda: asyncio.sleep(60)
        tasks = await service._create_tasks()

        self.assertEqual(2, len(tasks))
        self.assertEqual("example-service-http", tasks[0].get_name())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def test_hypercorn_config(self):
        quiet = ExampleService(ServerConfiguration(
            host="0.0.0.0", port=9000, shutdown_timeout=5))
        config = quiet._hypercorn_config()

        self.assertEqual(["0.0.0.0:9000"], config.bind)
        self.assertEqual(5.0, config.graceful_timeout)
        self.assertIsNone(config.accesslog)

        noisy = ExampleService(ServerConfiguration(access_log=True))
        self.assertIsNotNone(noisy._hypercorn_config().accesslog)

    async def test_serves_http_and_shuts_down_gracefully(self):
        port = free_port()
        service = ExampleService(ServerConfiguration(port=port,
                                                     shutdown_timeout=2))
        await service.initialise()
        runner = asyncio.create_task(service.run())
        base = f"http://127.0.0.1:{port}"

        async with aiohttp.ClientSession() as session:
            for _ in range(100):  # wait for the server to start
                try:
                    async with session.get(f"{base}/health") as response:
                        if response.status == http.HTTPStatus.OK:
                            break
                except aiohttp.ClientConnectionError:
                    await asyncio.sleep(0.05)
            else:
                self.fail("server did not start")

            async with session.get(f"{base}/hello") as response:
                self.assertEqual({"message": "hello"}, await response.json())

            # A request in flight when shutdown starts still completes.
            slow_request = asyncio.create_task(session.get(f"{base}/slow"))
            await asyncio.sleep(0.1)
            await service.stop()
            response = await slow_request
            self.assertEqual(http.HTTPStatus.OK, response.status)
            self.assertEqual({"message": "finished"}, await response.json())
            response.release()

        await asyncio.wait_for(runner, timeout=5)
        self.assertFalse(service.failed)
        self.assertTrue(service.shutdown_complete.is_set())

    async def test_port_in_use_fails_fast(self):
        with socket.socket() as blocker:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # Windows
                blocker.setsockopt(socket.SOL_SOCKET,
                                   socket.SO_EXCLUSIVEADDRUSE, 1)
            blocker.bind(("127.0.0.1", 0))
            blocker.listen()
            port = blocker.getsockname()[1]

            service = ExampleService(ServerConfiguration(port=port))
            await service.initialise()

            with self.assertLogs(service.logger, level="ERROR"):
                await asyncio.wait_for(service.run(), timeout=10)

        self.assertTrue(service.failed)
