"""ROCK Pi 23W PoE HAT Fan Controller.

A modern Python implementation for managing fans on ROCK Pi 23W PoE HAT
with temperature monitoring, Prometheus metrics, and comprehensive testing.
"""

__version__ = "1.0.0"
__author__ = "ROCK Pi Community"

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
