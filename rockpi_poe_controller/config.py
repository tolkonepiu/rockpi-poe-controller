"""Configuration management for ROCK Pi PoE HAT controller."""

import os

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class TemperatureLevels(BaseModel):
    """Temperature thresholds for fan speed levels."""

    level_0: int = Field(default=40, ge=0, le=100,
                         description="Temperature for 25% fan speed")
    level_1: int = Field(default=45, ge=0, le=100,
                         description="Temperature for 50% fan speed")
    level_2: int = Field(default=50, ge=0, le=100,
                         description="Temperature for 75% fan speed")
    level_3: int = Field(default=55, ge=0, le=100,
                         description="Temperature for 100% fan speed")

    @validator("level_1")
    def validate_level_1(cls, v, values):
        """Ensure level_1 is greater than level_0."""
        if "level_0" in values and v <= values["level_0"]:
            raise ValueError("level_1 must be greater than level_0")
        return v

    @validator("level_2")
    def validate_level_2(cls, v, values):
        """Ensure level_2 is greater than level_1."""
        if "level_1" in values and v <= values["level_1"]:
            raise ValueError("level_2 must be greater than level_1")
        return v

    @validator("level_3")
    def validate_level_3(cls, v, values):
        """Ensure level_3 is greater than level_2."""
        if "level_2" in values and v <= values["level_2"]:
            raise ValueError("level_3 must be greater than level_2")
        return v


class Config(BaseSettings):
    """Main configuration class for the fan controller."""

    # Temperature thresholds
    temperature_levels: TemperatureLevels = Field(
        default_factory=TemperatureLevels)

    # GPIO pins configuration
    fan_enable_pin: int = Field(
        default=16, description="GPIO pin for fan enable/disable")
    fan_pwm_pin: int = Field(
        default=13, description="GPIO pin for fan PWM control")

    # Sensor configuration
    adc_device_path: str = Field(
        default="/sys/bus/iio/devices/iio:device0/in_voltage0_raw",
        description="Path to ADC device for temperature sensor"
    )
    thermal_zone_cpu: int = Field(
        default=0, description="Thermal zone for CPU temperature")
    thermal_zone_gpu: int = Field(
        default=1, description="Thermal zone for GPU temperature")

    # Control parameters
    update_interval: float = Field(
        default=10.0, ge=1.0, le=300.0, description="Temperature check interval in seconds")
    fan_startup_delay: float = Field(
        default=2.0, ge=0.0, le=10.0, description="Delay before starting fan in seconds")

    # Metrics configuration
    metrics_port: int = Field(
        default=8000, ge=1024, le=65535, description="Port for Prometheus metrics")
    metrics_host: str = Field(
        default="0.0.0.0", description="Host for Prometheus metrics")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )

    class Config:
        """Pydantic configuration."""
        env_prefix = "POE_"
        env_nested_delimiter = "__"
        case_sensitive = False

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            temperature_levels=TemperatureLevels(
                level_0=int(os.getenv("POE_LV0", "40")),
                level_1=int(os.getenv("POE_LV1", "45")),
                level_2=int(os.getenv("POE_LV2", "50")),
                level_3=int(os.getenv("POE_LV3", "55")),
            )
        )
