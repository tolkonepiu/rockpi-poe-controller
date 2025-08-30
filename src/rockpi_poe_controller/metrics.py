"""Prometheus metrics for ROCK Pi PoE HAT controller."""

import logging

from prometheus_client import Gauge, start_http_server

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collector for Prometheus metrics."""

    def __init__(self, config):
        """Initialize metrics collector"""
        self.config = config
        self._server = None
        self._server_thread = None
        self._running = False
        self._common_labels = {
            "node_name": config.node_name,
            "node_ip": config.node_ip
        }

        # Temperature metrics
        self.temperature_gauge = Gauge(
            "rockpi_poe_temperature_celsius",
            "Current temperature in Celsius",
            ["sensor_type"] + list(self._common_labels.keys())
        )

        # Fan metrics
        self.fan_speed_gauge = Gauge(
            "rockpi_poe_fan_speed_percent",
            "Current fan speed as percentage",
            list(self._common_labels.keys())
        )

        self.fan_enabled_gauge = Gauge(
            "rockpi_poe_fan_enabled",
            "Fan enabled status (1=enabled, 0=disabled)",
            list(self._common_labels.keys())
        )

        # Control metrics
        self.fan_speed_changes_total = Gauge(
            "rockpi_poe_fan_speed_changes_total",
            "Total number of fan speed changes",
            list(self._common_labels.keys())
        )

        # System metrics
        self.controller_uptime_seconds = Gauge(
            "rockpi_poe_controller_uptime_seconds",
            "Controller uptime in seconds",
            list(self._common_labels.keys())
        )

        self.temperature_read_errors_total = Gauge(
            "rockpi_poe_temperature_read_errors_total",
            "Total number of temperature read errors",
            ["sensor_type"] + list(self._common_labels.keys())
        )

        self.gpio_errors_total = Gauge(
            "rockpi_poe_gpio_errors_total",
            "Total number of GPIO errors",
            ["operation"] + list(self._common_labels.keys())
        )

        logger.info(
            "Metrics collector initialized - host: %s, port: %d",
            self.config.metrics_host, self.config.metrics_port)

    def start_server(self) -> None:
        """Start Prometheus metrics server."""
        if self._running:
            logger.warning("Metrics server already running")
            return

        try:
            self._server, self._server_thread = start_http_server(
                self.config.metrics_port, addr=self.config.metrics_host)
            self._running = True
            logger.info("Prometheus metrics server started - host: %s, port: %d",
                        self.config.metrics_host, self.config.metrics_port)
        except Exception as e:
            logger.error("Failed to start metrics server: %s", str(e))
            raise

    def stop_server(self) -> None:
        """Stop Prometheus metrics server."""
        if not self._running:
            return

        try:
            self._server.shutdown()
            self._server_thread.join(timeout=5.0)
            self._running = False
            logger.info("Metrics server stopped")
        except Exception as e:
            logger.error("Error stopping metrics server: %s", str(e))
            self._running = False

    def update_temperature(self, temperature: float, sensor_type: str) -> None:
        labels = {"sensor_type": sensor_type, **self._common_labels}
        self.temperature_gauge.labels(**labels).set(temperature)

        logger.debug("Temperature metrics updated - temp: %.1f°C, sensor: %s",
                     temperature, sensor_type)

    def update_fan_speed(self, speed_percent: float) -> None:
        self.fan_speed_gauge.labels(**self._common_labels).set(speed_percent)
        self.fan_speed_changes_total.labels(**self._common_labels).inc()

        logger.debug("Fan speed metrics updated: %.1f%%", speed_percent)

    def update_fan_enabled(self, enabled: bool) -> None:
        value = 1 if enabled else 0
        self.fan_enabled_gauge.labels(**self._common_labels).set(value)

        logger.debug("Fan enabled metrics updated: %s", enabled)

    def update_uptime(self, uptime_seconds: float) -> None:
        self.controller_uptime_seconds.labels(
            **self._common_labels).set(uptime_seconds)

    def record_temperature_error(self, sensor_type: str) -> None:
        labels = {"sensor_type": sensor_type, **self._common_labels}
        self.temperature_read_errors_total.labels(**labels).inc()
        logger.warning(
            "Temperature read error recorded - sensor: %s", sensor_type)

    def record_gpio_error(self, operation: str) -> None:
        labels = {"operation": operation, **self._common_labels}
        self.gpio_errors_total.labels(**labels).inc()
        logger.warning("GPIO error recorded - operation: %s", operation)
