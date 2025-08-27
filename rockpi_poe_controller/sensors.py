"""Temperature sensor management for ROCK Pi PoE HAT."""

import os
from abc import ABC, abstractmethod
from typing import List

import structlog

from .exceptions import SensorError
from .metrics import MetricsCollector

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

    @abstractmethod
    def sensor_type(self) -> str:
        """Get the type identifier of the sensor."""
        pass


class ThermalZoneSensor(TemperatureSensor):
    """Thermal zone temperature sensor."""

    def __init__(self, zone_id: int, name: str):
        self.zone_id = zone_id
        self.name = name
        self.device_path = f"/sys/class/thermal/thermal_zone{zone_id}/temp"
        self._available = None

    def is_available(self) -> bool:
        if self._available is None:
            self._available = os.path.exists(self.device_path)
        return self._available

    def sensor_type(self) -> str:
        return f"thermal_zone_{self.name}"

    def read_temperature(self) -> float:
        if not self.is_available():
            raise SensorError(f"Thermal zone {self.name} not available")

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
            raise SensorError(
                f"Failed to read thermal zone {self.name}: {e}") from e


class CompositeTemperatureSensor(TemperatureSensor):
    """Composite temperature sensor that reads from multiple sources."""

    def __init__(self, sensors: List[TemperatureSensor],
                 metrics_collector: MetricsCollector):
        self.sensors = sensors
        self.metrics_collector = metrics_collector
        logger.info("Composite temperature sensor initialized",
                    sensor_count=len(sensors))

    def is_available(self) -> bool:
        """Check if any sensor in the composite is available."""
        return any(sensor.is_available() for sensor in self.sensors)

    def sensor_type(self) -> str:
        return "composite"

    def read_temperature(self) -> float:
        temperatures = []
        available_sensors = []

        for sensor in self.sensors:
            if sensor.is_available():
                try:
                    temp = sensor.read_temperature()
                    temperatures.append(temp)
                    available_sensors.append(sensor.sensor_type())
                    self.metrics_collector.update_temperature(
                        temp, sensor.sensor_type()
                    )
                except SensorError as e:
                    logger.warning("Sensor read failed",
                                   sensor=sensor.sensor_type(), error=str(e))
                    self.metrics_collector.record_temperature_error(
                        sensor.sensor_type()
                    )

        if not temperatures:
            self.metrics_collector.record_temperature_error(self.sensor_type())
            raise SensorError("No temperature sensors are available")

        max_temp = max(temperatures)
        self.metrics_collector.update_temperature(max_temp, self.sensor_type())

        logger.debug(
            "Composite temperature read",
            temperatures=temperatures,
            available_sensors=available_sensors,
            max_temperature=max_temp
        )

        return max_temp


def create_default_sensor_suite(metrics_collector: MetricsCollector) -> CompositeTemperatureSensor:
    sensors = [
        ThermalZoneSensor(0, "cpu"),
        ThermalZoneSensor(1, "gpu"),
    ]
    return CompositeTemperatureSensor(sensors, metrics_collector)
