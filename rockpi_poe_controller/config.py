"""Configuration management for ROCK Pi PoE HAT controller."""

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class TemperatureLevels(BaseModel):
    """Temperature thresholds for fan speed levels."""

    level_0: int = Field(default=40, ge=0, le=100,
                         description="Temperature for 25% fan speed", alias="lv0")
    level_1: int = Field(default=45, ge=0, le=100,
                         description="Temperature for 50% fan speed", alias="lv1")
    level_2: int = Field(default=50, ge=0, le=100,
                         description="Temperature for 75% fan speed", alias="lv2")
    level_3: int = Field(default=55, ge=0, le=100,
                         description="Temperature for 100% fan speed", alias="lv3")

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
    class Config:
        env_prefix = "POE_"
        env_nested_delimiter = "__"
        case_sensitive = False

    # Temperature thresholds
    temperature_levels: TemperatureLevels = Field(
        default_factory=TemperatureLevels)

    # GPIO pins configuration
    fan_enable_pin: int = Field(
        default=16, description="GPIO pin for fan enable/disable")
    fan_pwm_pin: int = Field(
        default=13, description="GPIO pin for fan PWM control")

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
