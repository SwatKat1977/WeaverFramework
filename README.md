# WeaverFramework
Python framework Quart wrapper for microservices

## Building WeaveFrame Wheel

* pip install build
* python -m build

## Quick start: a web microservice

```python
import sys
import quart
from weaver_framework.microservice import (QuartMicroservice,
                                           ServerConfiguration,
                                           run_microservice)

api = quart.Blueprint("api", __name__)


@api.get("/hello")
async def hello():
    return {"message": "hello"}


class HelloService(QuartMicroservice):
    SERVICE_NAME = "hello"

    async def _initialise(self) -> bool:
        # Connect to databases etc. here - runs before any request is served.
        self.app.register_blueprint(api)
        return True

    async def _shutdown(self) -> None:
        # Clean up here - runs after the server has stopped.
        pass


if __name__ == "__main__":
    sys.exit(run_microservice(HelloService(ServerConfiguration(port=8000))))
```

- `GET /health` returns 503 until `_initialise()` succeeds, 200 while running,
  and 503 again once shutdown starts.
- Ctrl+C or SIGTERM (e.g. `docker stop`) shuts down gracefully, letting
  in-flight requests finish.
- If the server or any background task fails, the service exits with code 1
  so it can be restarted.
- In tests, use `service.app.test_client()`; no server is started.
