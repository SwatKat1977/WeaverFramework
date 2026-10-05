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
from .base_microservice import BaseMicroservice

EXIT_SUCCESS: int = 0
EXIT_FAILURE: int = 1
EXIT_INTERRUPTED: int = 130


def run_microservice(service: BaseMicroservice) -> int:
    """Run a microservice until it stops, and return a process exit code.

    Installs SIGINT/SIGTERM handlers, initialises the service and runs it.

    Example::

        if __name__ == "__main__":
            sys.exit(run_microservice(MyService()))

    Args:
        service: The microservice to run.

    Returns:
        0 on a clean stop, 1 if initialisation or a task failed, and 130 if
        interrupted before the service could handle it.
    """

    async def main() -> int:
        service.install_signal_handlers()

        if not await service.initialise():
            service.logger.error("Microservice failed to initialise.")
            return EXIT_FAILURE

        await service.run()
        return EXIT_FAILURE if service.failed else EXIT_SUCCESS

    try:
        return asyncio.run(main())

    except KeyboardInterrupt:
        return EXIT_INTERRUPTED
