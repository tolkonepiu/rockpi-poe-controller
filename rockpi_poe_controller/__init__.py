"""ROCK Pi 23W PoE HAT Controller.

A Python implementation for managing fans on ROCK Pi 23W PoE HAT
with temperature monitoring and Prometheus metrics.
"""

__version__ = "0.2.0"

from .config import Config
from .controller import FanController
from .exceptions import (
    FanControllerError,
    GPIOError,
    SensorError,
    ConfigurationError,
)
from .gpio import GPIOController
from .metrics import MetricsCollector
from .sensors import TemperatureSensor

__all__ = [
    "Config",
    "FanController",
    "FanControllerError",
    "GPIOError",
    "SensorError",
    "ConfigurationError",
    "GPIOController",
    "MetricsCollector",
    "TemperatureSensor",
]
