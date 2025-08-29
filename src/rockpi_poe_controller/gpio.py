"""GPIO control for ROCK Pi PoE HAT fan management."""

import logging
from typing import Optional

import mraa

from .exceptions import GPIOError, HardwareNotAvailableError

logger = logging.getLogger(__name__)


class GPIOController:
    """GPIO controller for fan management."""

    def __init__(self, enable_pin: int = 16, pwm_pin: int = 13):
        """Initialize GPIO controller.

        Args:
            enable_pin: GPIO pin for fan enable/disable
            pwm_pin: GPIO pin for PWM control
        """
        self.enable_pin = enable_pin
        self.pwm_pin = pwm_pin
        self._enable_gpio: Optional[mraa.Gpio] = None
        self._pwm_gpio: Optional[mraa.Pwm] = None
        self._is_initialized = False

    def initialize(self) -> None:
        """Initialize GPIO pins.

        Raises:
            HardwareNotAvailableError: If GPIO pins are not available
        """
        try:
            # Initialize enable pin
            self._enable_gpio = mraa.Gpio(self.enable_pin)
            self._enable_gpio.dir(mraa.DIR_OUT)
            logger.info("Enable GPIO pin initialized: %d", self.enable_pin)

            # Initialize PWM pin
            self._pwm_gpio = mraa.Pwm(self.pwm_pin)
            self._pwm_gpio.period_ms(13)  # Set PWM period to 13ms
            self._pwm_gpio.enable(True)
            logger.info("PWM GPIO pin initialized: %d", self.pwm_pin)

            self._is_initialized = True

        except Exception as e:
            logger.error("Failed to initialize GPIO: %s", str(e))
            raise HardwareNotAvailableError(
                f"GPIO initialization failed: {e}") from e

    def is_available(self) -> bool:
        """Check if GPIO controller is available."""
        if not self._is_initialized:
            try:
                self.initialize()
            except HardwareNotAvailableError:
                return False
        return True

    def set_fan_enable(self, enabled: bool) -> None:
        if not self.is_available():
            raise GPIOError("GPIO controller not available")

        try:
            value = 1 if enabled else 0
            self._enable_gpio.write(value)
            logger.info("Fan enable state changed: %s, pin: %d",
                        enabled, self.enable_pin)
        except Exception as e:
            raise GPIOError(f"Failed to set fan enable: {e}") from e

    def set_fan_speed(self, duty_cycle: float) -> None:
        if not self.is_available():
            raise GPIOError("GPIO controller not available")

        if not 0.0 <= duty_cycle <= 1.0:
            raise ValueError("Duty cycle must be between 0.0 and 1.0")

        try:
            # Convert duty cycle to PWM value (1.0 = full speed, 0.0 = off)
            pwm_value = 1.0 - duty_cycle
            self._pwm_gpio.write(pwm_value)

            logger.debug(
                "Fan speed changed: duty_cycle=%f, pwm_value=%f, pin: %d",
                duty_cycle, pwm_value, self.pwm_pin
            )
        except Exception as e:
            raise GPIOError(f"Failed to set fan speed: {e}") from e

    def turn_off(self) -> None:
        """Turn off fan completely."""
        try:
            self.set_fan_enable(False)
            self.set_fan_speed(1.0)  # Set PWM to off position
            logger.info("Fan turned off")
        except GPIOError as e:
            logger.error("Failed to turn off fan: %s", str(e))
            raise

    def turn_on(self) -> None:
        """Turn on fan."""
        try:
            self.set_fan_enable(True)
            logger.info("Fan turned on")
        except GPIOError as e:
            logger.error("Failed to turn on fan: %s", str(e))
            raise

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            if self._enable_gpio:
                self.set_fan_enable(False)
            if self._pwm_gpio:
                self.set_fan_speed(1.0)  # Turn off PWM
            logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.warning("Error during GPIO cleanup: %s", str(e))
        finally:
            self._is_initialized = False
