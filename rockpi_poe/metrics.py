"""Prometheus metrics for ROCK Pi PoE HAT controller."""

import threading
import time
from typing import Optional

from prometheus_client import Gauge, Histogram, start_http_server
import structlog

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collector for Prometheus metrics."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """Initialize metrics collector.
        
        Args:
            host: Host to bind metrics server
            port: Port to bind metrics server
        """
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
        
        self.temperature_histogram = Histogram(
            "rockpi_poe_temperature_measurements",
            "Temperature measurements",
            ["sensor_type"],
            buckets=[20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
        )

        # Fan metrics
        self.fan_speed_gauge = Gauge(
            "rockpi_poe_fan_speed_percent",
            "Current fan speed as percentage",
            ["fan_id"]
        )
        
        self.fan_enabled_gauge = Gauge(
            "rockpi_poe_fan_enabled",
            "Fan enabled status (1=enabled, 0=disabled)",
            ["fan_id"]
        )

        # Control metrics
        self.fan_speed_changes_total = Gauge(
            "rockpi_poe_fan_speed_changes_total",
            "Total number of fan speed changes",
            ["fan_id"]
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

        logger.info("Metrics collector initialized", host=host, port=port)

    def start_server(self) -> None:
        """Start Prometheus metrics server."""
        if self._running:
            logger.warning("Metrics server already running")
            return

        try:
            start_http_server(self.port, addr=self.host)
            self._running = True
            logger.info("Prometheus metrics server started", host=self.host, port=self.port)
        except Exception as e:
            logger.error("Failed to start metrics server", error=str(e))
            raise

    def stop_server(self) -> None:
        """Stop Prometheus metrics server."""
        self._running = False
        logger.info("Metrics server stopped")

    def update_temperature(self, temperature: float, sensor_type: str = "composite") -> None:
        """Update temperature metrics.
        
        Args:
            temperature: Temperature in Celsius
            sensor_type: Type of sensor (e.g., 'adc', 'cpu', 'gpu', 'composite')
        """
        self.temperature_gauge.labels(sensor_type=sensor_type).set(temperature)
        self.temperature_histogram.labels(sensor_type=sensor_type).observe(temperature)
        
        logger.debug("Temperature metrics updated", temperature=temperature, sensor_type=sensor_type)

    def update_fan_speed(self, speed_percent: float, fan_id: str = "main") -> None:
        """Update fan speed metrics.
        
        Args:
            speed_percent: Fan speed as percentage (0-100)
            fan_id: Fan identifier
        """
        self.fan_speed_gauge.labels(fan_id=fan_id).set(speed_percent)
        self.fan_speed_changes_total.labels(fan_id=fan_id).inc()
        
        logger.debug("Fan speed metrics updated", speed_percent=speed_percent, fan_id=fan_id)

    def update_fan_enabled(self, enabled: bool, fan_id: str = "main") -> None:
        """Update fan enabled status metrics.
        
        Args:
            enabled: Whether fan is enabled
            fan_id: Fan identifier
        """
        value = 1 if enabled else 0
        self.fan_enabled_gauge.labels(fan_id=fan_id).set(value)
        
        logger.debug("Fan enabled metrics updated", enabled=enabled, fan_id=fan_id)

    def update_uptime(self, uptime_seconds: float) -> None:
        """Update controller uptime metric.
        
        Args:
            uptime_seconds: Uptime in seconds
        """
        self.controller_uptime_seconds.set(uptime_seconds)

    def record_temperature_error(self, sensor_type: str = "unknown") -> None:
        """Record temperature read error.
        
        Args:
            sensor_type: Type of sensor that failed
        """
        self.temperature_read_errors_total.labels(sensor_type=sensor_type).inc()
        logger.warning("Temperature read error recorded", sensor_type=sensor_type)

    def record_gpio_error(self, operation: str) -> None:
        """Record GPIO error.
        
        Args:
            operation: GPIO operation that failed
        """
        self.gpio_errors_total.labels(operation=operation).inc()
        logger.warning("GPIO error recorded", operation=operation)
