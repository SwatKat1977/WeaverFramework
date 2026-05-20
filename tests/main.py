import unittest
from tests.test_configuration_configuration_manager import TestConfigurationManager
from tests.test_configuration_setup import (TestConfigItemDataType,
                                            TestConfigurationSetupItem,
                                            TestConfigurationSetup)
from tests.test_microservice_api_response import TestMicroserviceApiResponse
from tests.test_microservice_base_api_route import TestMicroserviceBaseApiRoute
from tests.test_microservice_base_microservice import TestMicroserviceBaseMicroservice
from tests.test_microservice_http_content_type import TestMicroserviceHttpContentType
from tests.test_version import TestVersion
from tests.database.test_sqlite_interface import TestSqliteInterface
from tests.microservice.test_rest_client import TestRestClient
from tests.microservice.test_microservice_decorators import TestValidateJsonDecorator


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
