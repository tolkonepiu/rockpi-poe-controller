"""Main fan controller for ROCK Pi PoE HAT."""

import logging
import signal
import time

from .config import Config
from .exceptions import FanControllerError, SensorError, GPIOError
from .gpio import GPIOController
from .metrics import MetricsCollector
from .sensors import create_default_sensor_suite

logger = logging.getLogger(__name__)


class FanController:
    """Main fan controller for ROCK Pi PoE HAT."""

    def __init__(self, config: Config):
        self.config = config
        self.metrics = MetricsCollector(
            host=config.metrics_host,
            port=config.metrics_port
        )
        self.gpio = GPIOController(
            enable_pin=config.fan_enable_pin,
            pwm_pin=config.fan_pwm_pin
        )
        self.sensors = create_default_sensor_suite(
            metrics_collector=self.metrics)

        self._running = False
        self._start_time = None
        self._current_speed = 0.0
        self._current_enabled = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Fan controller initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal: %s", signum)
        self.stop()

    def start(self) -> None:
        """Start the fan controller."""
        if self._running:
            logger.warning("Controller already running")
            return

        try:
            # Initialize components
            if not self.gpio.is_available():
                raise FanControllerError("GPIO controller not available")

            # Start metrics server
            self.metrics.start_server()

            # Start fan control loop
            self._running = True
            self._start_time = time.time()

            logger.info("Fan controller started")
            self._control_loop()

        except Exception as e:
            logger.error("Failed to start controller: %s", str(e))
            self.stop()
            raise

    def stop(self) -> None:
        """Stop the fan controller."""
        if not self._running:
            return

        logger.info("Stopping fan controller")
        self._running = False

        try:
            # Turn off fan
            self.gpio.turn_off()
            self._current_enabled = False
            self._current_speed = 0.0

            # Update metrics
            self.metrics.update_fan_enabled(False)
            self.metrics.update_fan_speed(0.0)

            # Cleanup GPIO
            self.gpio.cleanup()

            # Stop metrics server
            self.metrics.stop_server()

            logger.info("Fan controller stopped")

        except Exception as e:
            logger.error("Error during shutdown: %s", str(e))

    def _control_loop(self) -> None:
        """Main control loop for fan management."""
        logger.info("Starting fan control loop")

        while self._running:
            try:
                # Read temperature
                temperature = self.sensors.read_temperature()
                if self._start_time:
                    uptime = time.time() - self._start_time
                    self.metrics.update_uptime(uptime)

                # Determine fan speed based on temperature
                speed_percent, duty_cycle = self._calculate_fan_speed(
                    temperature)

                # Apply fan control
                self._apply_fan_control(speed_percent, duty_cycle)

                # Log status
                logger.info(
                    "Fan control status - temp: %.1f°C, speed: %.1f%%, duty: %.2f, enabled: %s",
                    temperature, speed_percent, duty_cycle, self._current_enabled
                )

            except SensorError as e:
                logger.error("Sensor error in control loop: %s", str(e))
                self.metrics.record_temperature_error()

            except GPIOError as e:
                logger.error("GPIO error in control loop: %s", str(e))
                self.metrics.record_gpio_error("control_loop")

            except Exception as e:
                logger.error("Unexpected error in control loop: %s", str(e))
            finally:
                time.sleep(self.config.update_interval)

    def _calculate_fan_speed(self, temperature: float) -> tuple[float, float]:
        if temperature >= self.config.lv3:
            speed_percent = 100.0
            duty_cycle = 0.0  # Full speed
        elif temperature >= self.config.lv2:
            speed_percent = 75.0
            duty_cycle = 0.25
        elif temperature >= self.config.lv1:
            speed_percent = 50.0
            duty_cycle = 0.5
        elif temperature >= self.config.lv0:
            speed_percent = 25.0
            duty_cycle = 0.75
        else:
            speed_percent = 0.0
            duty_cycle = 1.0  # Fan off

        return speed_percent, duty_cycle

    def _apply_fan_control(self, speed_percent: float, duty_cycle: float) -> None:
        # Determine if fan should be enabled
        enabled = speed_percent > 0.0

        # Update fan enable state if needed
        if enabled != self._current_enabled:
            if enabled:
                self.gpio.turn_on()
            else:
                self.gpio.turn_off()
            self._current_enabled = enabled

        self.metrics.update_fan_enabled(self._current_enabled)

        # Update fan speed if changed
        if abs(duty_cycle - self._current_speed) > 0.01:  # Small threshold to avoid noise
            self.gpio.set_fan_speed(duty_cycle)
            self._current_speed = duty_cycle
            self.metrics.update_fan_speed(speed_percent)
