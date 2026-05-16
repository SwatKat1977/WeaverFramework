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
from dataclasses import dataclass
from typing import Final
import logging

DEFAULT_DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL: Final[int] = logging.INFO
DEFAULT_FORMAT_STRING: Final[str] = (
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@dataclass(slots=True, frozen=True)
class LoggingConfiguration:
    """Immutable logging configuration settings.

    Attributes:
        level: Logging severity level used by the logger.
        format_string: Format string applied to log messages.
        datetime_format: Datetime format string used for timestamps.
    """
    level: int | str = DEFAULT_LOG_LEVEL
    format_string: str = DEFAULT_FORMAT_STRING
    datetime_format: str = DEFAULT_DATETIME_FORMAT
