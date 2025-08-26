"""Temperature sensor management for ROCK Pi PoE HAT."""

import os
from abc import ABC, abstractmethod
from typing import List, Optional

import structlog

from .exceptions import SensorError

logger = structlog.get_logger(__name__)


class TemperatureSensor(ABC):
    """Abstract base class for temperature sensors."""

    @abstractmethod
    def read_temperature(self) -> float:
        """Read temperature from sensor."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if sensor is available."""
        pass


class ADCTemperatureSensor(TemperatureSensor):
    """ADC-based temperature sensor using voltage conversion."""

    def __init__(self, device_path: str = "/sys/bus/iio/devices/iio:device0/in_voltage0_raw"):
        """Initialize ADC temperature sensor.
        
        Args:
            device_path: Path to ADC device file
        """
        self.device_path = device_path
        self._available = None

    def is_available(self) -> bool:
        """Check if ADC sensor is available."""
        if self._available is None:
            self._available = os.path.exists(self.device_path)
        return self._available

    def read_temperature(self) -> float:
        """Read temperature from ADC sensor.
        
        Returns:
            Temperature in Celsius
            
        Raises:
            SensorError: If sensor is not available or read fails
        """
        if not self.is_available():
            raise SensorError(f"ADC sensor not available at {self.device_path}")

        try:
            with open(self.device_path, "r") as f:
                raw_value = int(f.read().strip())
            
            # Convert ADC value to temperature using the original formula
            # v2t = lambda x: 42 + (960 - x) * 0.05
            temperature = 42 + (960 - raw_value) * 0.05
            
            logger.debug("ADC temperature read", raw_value=raw_value, temperature=temperature)
            return temperature
            
        except (OSError, ValueError) as e:
            raise SensorError(f"Failed to read ADC temperature: {e}") from e


class ThermalZoneSensor(TemperatureSensor):
    """Thermal zone temperature sensor."""

    def __init__(self, zone_id: int, name: str = "thermal"):
        """Initialize thermal zone sensor.
        
        Args:
            zone_id: Thermal zone ID
            name: Sensor name for logging
        """
        self.zone_id = zone_id
        self.name = name
        self.device_path = f"/sys/class/thermal/thermal_zone{zone_id}/temp"
        self._available = None

    def is_available(self) -> bool:
        """Check if thermal zone sensor is available."""
        if self._available is None:
            self._available = os.path.exists(self.device_path)
        return self._available

    def read_temperature(self) -> float:
        """Read temperature from thermal zone.
        
        Returns:
            Temperature in Celsius
            
        Raises:
            SensorError: If sensor is not available or read fails
        """
        if not self.is_available():
            raise SensorError(f"Thermal zone {self.zone_id} not available")

        try:
            with open(self.device_path, "r") as f:
                raw_temp = int(f.read().strip())
            
            temperature = raw_temp / 1000.0
            
            logger.debug(
                "Thermal zone temperature read",
                zone_id=self.zone_id,
                name=self.name,
                raw_temp=raw_temp,
                temperature=temperature
            )
            return temperature
            
        except (OSError, ValueError) as e:
            raise SensorError(f"Failed to read thermal zone {self.zone_id}: {e}") from e


class CompositeTemperatureSensor:
    """Composite temperature sensor that reads from multiple sources."""

    def __init__(self, sensors: List[TemperatureSensor]):
        """Initialize composite sensor.
        
        Args:
            sensors: List of temperature sensors to use
        """
        self.sensors = sensors
        logger.info("Composite temperature sensor initialized", sensor_count=len(sensors))

    def read_temperature(self) -> float:
        """Read temperature from all available sensors and return the maximum.
        
        Returns:
            Maximum temperature from all available sensors
            
        Raises:
            SensorError: If no sensors are available
        """
        temperatures = []
        available_sensors = []

        for sensor in self.sensors:
            if sensor.is_available():
                try:
                    temp = sensor.read_temperature()
                    temperatures.append(temp)
                    available_sensors.append(sensor.__class__.__name__)
                except SensorError as e:
                    logger.warning("Sensor read failed", sensor=type(sensor).__name__, error=str(e))

        if not temperatures:
            raise SensorError("No temperature sensors are available")

        max_temp = max(temperatures)
        logger.debug(
            "Composite temperature read",
            temperatures=temperatures,
            available_sensors=available_sensors,
            max_temperature=max_temp
        )
        
        return max_temp

    def get_available_sensors(self) -> List[str]:
        """Get list of available sensor names."""
        return [type(sensor).__name__ for sensor in self.sensors if sensor.is_available()]


def create_default_sensor_suite() -> CompositeTemperatureSensor:
    """Create default sensor suite with ADC and thermal zones.
    
    Returns:
        Composite sensor with ADC, CPU, and GPU thermal sensors
    """
    sensors = [
        ADCTemperatureSensor(),
        ThermalZoneSensor(0, "CPU"),
        ThermalZoneSensor(1, "GPU"),
    ]
    return CompositeTemperatureSensor(sensors)
