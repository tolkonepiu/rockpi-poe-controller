"""Main fan controller for ROCK Pi PoE HAT."""

import signal
import sys
import time
from typing import Optional

import structlog

from .config import Config
from .exceptions import FanControllerError, SensorError, GPIOError
from .gpio import GPIOController
from .metrics import MetricsCollector
from .sensors import create_default_sensor_suite

logger = structlog.get_logger(__name__)


class FanController:
    """Main fan controller for ROCK Pi PoE HAT."""

    def __init__(self, config: Config):
        """Initialize fan controller.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.metrics = MetricsCollector(
            host=config.metrics_host,
            port=config.metrics_port
        )
        self.gpio = GPIOController(
            enable_pin=config.fan_enable_pin,
            pwm_pin=config.fan_pwm_pin
        )
        self.sensors = create_default_sensor_suite(metrics_collector=self.metrics)
        
        self._running = False
        self._start_time = None
        self._current_speed = 0.0
        self._current_enabled = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Fan controller initialized", config=config.dict())

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal", signal=signum)
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
            logger.error("Failed to start controller", error=str(e))
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
            logger.error("Error during shutdown", error=str(e))

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
                speed_percent, duty_cycle = self._calculate_fan_speed(temperature)
                
                # Apply fan control
                self._apply_fan_control(speed_percent, duty_cycle)
                
                # Log status
                logger.info(
                    "Fan control status",
                    temperature=temperature,
                    speed_percent=speed_percent,
                    duty_cycle=duty_cycle,
                    enabled=self._current_enabled
                )
                
                # Wait for next cycle
                time.sleep(self.config.update_interval)
                
            except SensorError as e:
                logger.error("Sensor error in control loop", error=str(e))
                self.metrics.record_temperature_error()
                time.sleep(self.config.update_interval)
                
            except GPIOError as e:
                logger.error("GPIO error in control loop", error=str(e))
                self.metrics.record_gpio_error("control_loop")
                time.sleep(self.config.update_interval)
                
            except Exception as e:
                logger.error("Unexpected error in control loop", error=str(e))
                time.sleep(self.config.update_interval)

    def _calculate_fan_speed(self, temperature: float) -> tuple[float, float]:
        """Calculate fan speed based on temperature.
        
        Args:
            temperature: Current temperature in Celsius
            
        Returns:
            Tuple of (speed_percent, duty_cycle)
        """
        levels = self.config.temperature_levels
        
        if temperature >= levels.level_3:
            speed_percent = 100.0
            duty_cycle = 0.0  # Full speed
        elif temperature >= levels.level_2:
            speed_percent = 75.0
            duty_cycle = 0.25
        elif temperature >= levels.level_1:
            speed_percent = 50.0
            duty_cycle = 0.5
        elif temperature >= levels.level_0:
            speed_percent = 25.0
            duty_cycle = 0.75
        else:
            speed_percent = 0.0
            duty_cycle = 1.0  # Fan off
            
        return speed_percent, duty_cycle

    def _apply_fan_control(self, speed_percent: float, duty_cycle: float) -> None:
        """Apply fan control settings.
        
        Args:
            speed_percent: Fan speed as percentage
            duty_cycle: PWM duty cycle
        """
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
