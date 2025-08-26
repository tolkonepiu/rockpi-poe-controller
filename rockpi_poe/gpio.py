"""GPIO control for ROCK Pi PoE HAT fan management."""

from typing import Optional

import mraa
import structlog

from .exceptions import GPIOError, HardwareNotAvailableError

logger = structlog.get_logger(__name__)


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
        self._current_duty_cycle = 1.0
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
            logger.info("Enable GPIO pin initialized", pin=self.enable_pin)

            # Initialize PWM pin
            self._pwm_gpio = mraa.Pwm(self.pwm_pin)
            self._pwm_gpio.period_ms(13)  # Set PWM period to 13ms
            self._pwm_gpio.enable(True)
            logger.info("PWM GPIO pin initialized", pin=self.pwm_pin)

            self._is_initialized = True

        except Exception as e:
            logger.error("Failed to initialize GPIO", error=str(e))
            raise HardwareNotAvailableError(f"GPIO initialization failed: {e}") from e

    def is_available(self) -> bool:
        """Check if GPIO controller is available."""
        if not self._is_initialized:
            try:
                self.initialize()
            except HardwareNotAvailableError:
                return False
        return True

    def set_fan_enable(self, enabled: bool) -> None:
        """Enable or disable fan.
        
        Args:
            enabled: True to enable fan, False to disable
            
        Raises:
            GPIOError: If GPIO operation fails
        """
        if not self.is_available():
            raise GPIOError("GPIO controller not available")

        try:
            value = 1 if enabled else 0
            self._enable_gpio.write(value)
            logger.info("Fan enable state changed", enabled=enabled, pin=self.enable_pin)
        except Exception as e:
            raise GPIOError(f"Failed to set fan enable: {e}") from e

    def set_fan_speed(self, duty_cycle: float) -> None:
        """Set fan speed using PWM duty cycle.
        
        Args:
            duty_cycle: PWM duty cycle (0.0 to 1.0, where 1.0 is full speed)
            
        Raises:
            GPIOError: If GPIO operation fails
        """
        if not self.is_available():
            raise GPIOError("GPIO controller not available")

        if not 0.0 <= duty_cycle <= 1.0:
            raise ValueError("Duty cycle must be between 0.0 and 1.0")

        try:
            # Convert duty cycle to PWM value (1.0 = full speed, 0.0 = off)
            pwm_value = 1.0 - duty_cycle
            self._pwm_gpio.write(pwm_value)
            self._current_duty_cycle = duty_cycle
            
            logger.debug(
                "Fan speed changed",
                duty_cycle=duty_cycle,
                pwm_value=pwm_value,
                pin=self.pwm_pin
            )
        except Exception as e:
            raise GPIOError(f"Failed to set fan speed: {e}") from e

    def get_current_duty_cycle(self) -> float:
        """Get current fan duty cycle.
        
        Returns:
            Current duty cycle (0.0 to 1.0)
        """
        return self._current_duty_cycle

    def turn_off(self) -> None:
        """Turn off fan completely."""
        try:
            self.set_fan_enable(False)
            self.set_fan_speed(1.0)  # Set PWM to off position
            logger.info("Fan turned off")
        except GPIOError as e:
            logger.error("Failed to turn off fan", error=str(e))
            raise

    def turn_on(self) -> None:
        """Turn on fan."""
        try:
            self.set_fan_enable(True)
            logger.info("Fan turned on")
        except GPIOError as e:
            logger.error("Failed to turn on fan", error=str(e))
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
            logger.warning("Error during GPIO cleanup", error=str(e))
        finally:
            self._is_initialized = False
