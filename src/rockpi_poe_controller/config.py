"""Configuration management for ROCK Pi PoE HAT controller."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    class Config:
        env_prefix = "POE_"
        env_nested_delimiter = "__"
        case_sensitive = False

    # Temperature thresholds
    lv0: int = Field(default=40, ge=0, le=100,
                     description="Temperature for 25% fan speed")
    lv1: int = Field(default=45, ge=0, le=100,
                     description="Temperature for 50% fan speed")
    lv2: int = Field(default=50, ge=0, le=100,
                     description="Temperature for 75% fan speed")
    lv3: int = Field(default=55, ge=0, le=100,
                     description="Temperature for 100% fan speed")

    # GPIO pins configuration
    fan_enable_pin: int = Field(
        default=16, description="GPIO pin for fan enable/disable")
    fan_pwm_pin: int = Field(
        default=13, description="GPIO pin for fan PWM control")

    # Control parameters
    update_interval: float = Field(
        default=10.0, ge=1.0, le=300.0, description="Temperature check interval in seconds")
    # Metrics configuration
    metrics_host: str = Field(
        default="0.0.0.0", description="Host for Prometheus metrics")
    metrics_port: int = Field(
        default=8000, ge=1024, le=65535, description="Port for Prometheus metrics")

    # Node identification
    node_name: str = Field(
        default="localhost", description="Node name for metrics labels")
    node_ip: str = Field(
        default="127.0.0.1", description="Node IP for metrics labels")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
