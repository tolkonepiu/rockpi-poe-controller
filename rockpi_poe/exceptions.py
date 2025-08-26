"""Custom exceptions for ROCK Pi PoE HAT controller."""


class FanControllerError(Exception):
    """Base exception for fan controller errors."""

    pass


class GPIOError(FanControllerError):
    """Exception raised when GPIO operations fail."""

    pass


class SensorError(FanControllerError):
    """Exception raised when temperature sensor operations fail."""

    pass


class ConfigurationError(FanControllerError):
    """Exception raised when configuration is invalid."""

    pass


class HardwareNotAvailableError(FanControllerError):
    """Exception raised when required hardware is not available."""

    pass
