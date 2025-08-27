"""Temperature sensor management for ROCK Pi PoE HAT."""

import os
from abc import ABC, abstractmethod
from typing import List, Optional

import structlog

from .exceptions import SensorError
from .metrics import MetricsCollector

logger = structlog.get_logger(__name__)


class TemperatureSensor(ABC):
    """Abstract base class for temperature sensors."""

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics_collector = metrics_collector

    @abstractmethod
    def read_temperature(self) -> float:
        """Read temperature from sensor."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if sensor is available."""
        pass

    def _record_temperature(self, temperature: float, sensor_type: str) -> None:
        if self.metrics_collector:
            self.metrics_collector.update_temperature(temperature, sensor_type)

    def _record_error(self, sensor_type: str) -> None:
        if self.metrics_collector:
            self.metrics_collector.record_temperature_error(sensor_type)


class ADCTemperatureSensor(TemperatureSensor):
    """ADC-based temperature sensor using voltage conversion."""

    def __init__(self, device_path: str = "/sys/bus/iio/devices/iio:device0/in_voltage0_raw",
                 metrics_collector: Optional[MetricsCollector] = None):
        super().__init__(metrics_collector)
        self.device_path = device_path
        self._available = None

    def is_available(self) -> bool:
        """Check if ADC sensor is available."""
        if self._available is None:
            self._available = os.path.exists(self.device_path)
        return self._available

    def read_temperature(self) -> float:
        if not self.is_available():
            self._record_error("adc")
            raise SensorError(
                f"ADC sensor not available at {self.device_path}")

        try:
            with open(self.device_path, "r") as f:
                raw_value = int(f.read().strip())

            # 42, the answer to life, the universe, and everything
            temperature = 42 + (960 - raw_value) * 0.05
            self._record_temperature(temperature, "adc")

            logger.debug("ADC temperature read",
                         raw_value=raw_value, temperature=temperature)
            return temperature

        except (OSError, ValueError) as e:
            self._record_error("adc")
            raise SensorError(f"Failed to read ADC temperature: {e}") from e


class ThermalZoneSensor(TemperatureSensor):
    """Thermal zone temperature sensor."""

    def __init__(self, zone_id: int, name: str, metrics_collector: Optional[MetricsCollector] = None):
        super().__init__(metrics_collector)
        self.zone_id = zone_id
        self.name = name
        self.device_path = f"/sys/class/thermal/thermal_zone{zone_id}/temp"
        self._available = None

    def is_available(self) -> bool:
        if self._available is None:
            self._available = os.path.exists(self.device_path)
        return self._available

    def read_temperature(self) -> float:
        if not self.is_available():
            self._record_error(f"thermal_zone_{self.name}")
            raise SensorError(f"Thermal zone {self.name} not available")

        try:
            with open(self.device_path, "r") as f:
                raw_temp = int(f.read().strip())

            temperature = raw_temp / 1000.0
            self._record_temperature(temperature, f"thermal_zone_{self.name}")

            logger.debug(
                "Thermal zone temperature read",
                zone_id=self.zone_id,
                name=self.name,
                raw_temp=raw_temp,
                temperature=temperature
            )
            return temperature

        except (OSError, ValueError) as e:
            self._record_error(f"thermal_zone_{self.name}")
            raise SensorError(
                f"Failed to read thermal zone {self.name}: {e}") from e


class CompositeTemperatureSensor(TemperatureSensor):
    """Composite temperature sensor that reads from multiple sources."""

    def __init__(self, sensors: List[TemperatureSensor],
                 metrics_collector: Optional[MetricsCollector] = None):
        super().__init__(metrics_collector)
        self.sensors = sensors
        logger.info("Composite temperature sensor initialized",
                    sensor_count=len(sensors))

    def is_available(self) -> bool:
        """Check if any sensor in the composite is available."""
        return any(sensor.is_available() for sensor in self.sensors)

    def read_temperature(self) -> float:
        temperatures = []
        available_sensors = []

        for sensor in self.sensors:
            if sensor.is_available():
                try:
                    temp = sensor.read_temperature()
                    temperatures.append(temp)
                    available_sensors.append(sensor.__class__.__name__)
                except SensorError as e:
                    logger.warning("Sensor read failed", sensor=type(
                        sensor).__name__, error=str(e))

        if not temperatures:
            self._record_error("composite")
            raise SensorError("No temperature sensors are available")

        max_temp = max(temperatures)
        self._record_temperature(max_temp, "composite")

        logger.debug(
            "Composite temperature read",
            temperatures=temperatures,
            available_sensors=available_sensors,
            max_temperature=max_temp
        )

        return max_temp


def create_default_sensor_suite(metrics_collector: Optional[MetricsCollector] = None) -> CompositeTemperatureSensor:
    sensors = [
        ADCTemperatureSensor(metrics_collector=metrics_collector),
        ThermalZoneSensor(0, "cpu", metrics_collector=metrics_collector),
        ThermalZoneSensor(1, "gpu", metrics_collector=metrics_collector),
    ]
    return CompositeTemperatureSensor(sensors, metrics_collector=metrics_collector)
