"""Prometheus metrics for ROCK Pi PoE HAT controller."""

import logging
import threading
from typing import Optional

from prometheus_client import Gauge, start_http_server

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collector for Prometheus metrics."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """Initialize metrics collector"""
        self.host = host
        self.port = port
        self._server_thread: Optional[threading.Thread] = None
        self._running = False

        # Temperature metrics
        self.temperature_gauge = Gauge(
            "rockpi_poe_temperature_celsius",
            "Current temperature in Celsius",
            ["sensor_type"]
        )

        # Fan metrics
        self.fan_speed_gauge = Gauge(
            "rockpi_poe_fan_speed_percent",
            "Current fan speed as percentage"
        )

        self.fan_enabled_gauge = Gauge(
            "rockpi_poe_fan_enabled",
            "Fan enabled status (1=enabled, 0=disabled)"
        )

        # Control metrics
        self.fan_speed_changes_total = Gauge(
            "rockpi_poe_fan_speed_changes_total",
            "Total number of fan speed changes"
        )

        # System metrics
        self.controller_uptime_seconds = Gauge(
            "rockpi_poe_controller_uptime_seconds",
            "Controller uptime in seconds"
        )

        self.temperature_read_errors_total = Gauge(
            "rockpi_poe_temperature_read_errors_total",
            "Total number of temperature read errors",
            ["sensor_type"]
        )

        self.gpio_errors_total = Gauge(
            "rockpi_poe_gpio_errors_total",
            "Total number of GPIO errors",
            ["operation"]
        )

        logger.info(
            "Metrics collector initialized - host: %s, port: %d", host, port)

    def start_server(self) -> None:
        """Start Prometheus metrics server."""
        if self._running:
            logger.warning("Metrics server already running")
            return

        try:
            start_http_server(self.port, addr=self.host)
            self._running = True
            logger.info("Prometheus metrics server started - host: %s, port: %d",
                        self.host, self.port)
        except Exception as e:
            logger.error("Failed to start metrics server: %s", str(e))
            raise

    def stop_server(self) -> None:
        """Stop Prometheus metrics server."""
        self._running = False
        logger.info("Metrics server stopped")

    def update_temperature(self, temperature: float, sensor_type: str) -> None:
        self.temperature_gauge.labels(sensor_type=sensor_type).set(temperature)

        logger.debug("Temperature metrics updated - temp: %.1f°C, sensor: %s",
                     temperature, sensor_type)

    def update_fan_speed(self, speed_percent: float) -> None:
        self.fan_speed_gauge.set(speed_percent)
        self.fan_speed_changes_total.inc()

        logger.debug("Fan speed metrics updated: %.1f%%", speed_percent)

    def update_fan_enabled(self, enabled: bool) -> None:
        value = 1 if enabled else 0
        self.fan_enabled_gauge.set(value)

        logger.debug("Fan enabled metrics updated: %s", enabled)

    def update_uptime(self, uptime_seconds: float) -> None:
        self.controller_uptime_seconds.set(uptime_seconds)

    def record_temperature_error(self, sensor_type: str = "unknown") -> None:
        self.temperature_read_errors_total.labels(
            sensor_type=sensor_type).inc()
        logger.warning(
            "Temperature read error recorded - sensor: %s", sensor_type)

    def record_gpio_error(self, operation: str) -> None:
        self.gpio_errors_total.labels(operation=operation).inc()
        logger.warning("GPIO error recorded - operation: %s", operation)
