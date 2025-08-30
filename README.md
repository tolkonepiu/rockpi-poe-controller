# ROCK Pi PoE HAT Controller

A Python-based fan controller for
[ROCK Pi PoE HAT](https://wiki.radxa.com/ROCKPI_23W_PoE_HAT) that automatically
adjusts fan speed based on temperature sensors and provides Prometheus metrics.

## Quick Start

### Using Docker (Recommended)

#### Basic Usage

```bash
docker run -d \
  --name rockpi-poe-controller \
  --privileged \
  --restart unless-stopped \
  -p 8000:8000 \
  ghcr.io/tolkonepiu/rockpi-poe-controller:latest
```

#### Custom Configuration

```bash
# Run with custom temperature thresholds and node identification
docker run -d \
  --name rockpi-poe-controller \
  --privileged \
  --restart unless-stopped \
  -p 8000:8000 \
  -e POE_LV0=35 \
  -e POE_LV1=40 \
  -e POE_LV2=45 \
  -e POE_LV3=50 \
  -e POE_UPDATE_INTERVAL=5.0 \
  -e POE_NODE_NAME="rockpi-01" \
  -e POE_NODE_IP="192.168.1.100" \
  ghcr.io/tolkonepiu/rockpi-poe-controller:latest
```

### Local Installation

First, install the [MRAA library](https://github.com/eclipse/mraa) for GPIO
communication, then run the following commands:

```bash
# Clone the repository
git clone https://github.com/tolkonepiu/rockpi-poe-controller.git
cd rockpi-poe-controller

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run the controller
python src/main.py start
```

### Kubernetes

For Kubernetes deployment examples, see the
[HelmRelease configuration](https://github.com/tolkonepiu/hl-cluster/blob/main/kubernetes/apps/hardware/rockpi-poe-controller/app/helmrelease.yaml).

## Configuration

The controller can be configured using environment variables.

### Environment Variables

| Variable              | Default     | Description                          |
| --------------------- | ----------- | ------------------------------------ |
| `POE_LV0`             | `40`        | Temperature (°C) for 25% fan speed   |
| `POE_LV1`             | `45`        | Temperature (°C) for 50% fan speed   |
| `POE_LV2`             | `50`        | Temperature (°C) for 75% fan speed   |
| `POE_LV3`             | `55`        | Temperature (°C) for 100% fan speed  |
| `POE_FAN_ENABLE_PIN`  | `16`        | GPIO pin for fan enable/disable      |
| `POE_FAN_PWM_PIN`     | `13`        | GPIO pin for fan PWM control         |
| `POE_UPDATE_INTERVAL` | `10.0`      | Temperature check interval (seconds) |
| `POE_METRICS_HOST`    | `0.0.0.0`   | Host for Prometheus metrics          |
| `POE_METRICS_PORT`    | `8000`      | Port for Prometheus metrics          |
| `POE_NODE_NAME`       | `localhost` | Node name for metrics labels         |
| `POE_NODE_IP`         | `127.0.0.1` | Node IP for metrics labels           |
| `POE_LOG_LEVEL`       | `INFO`      | Logging level                        |

### Temperature Thresholds

The fan speed is automatically adjusted based on temperature:

- **25% speed**: When temperature ≥ `POE_LV0`
- **50% speed**: When temperature ≥ `POE_LV1`
- **75% speed**: When temperature ≥ `POE_LV2`
- **100% speed**: When temperature ≥ `POE_LV3`

## Monitoring

### Prometheus Metrics

The controller exposes Prometheus metrics on port 8000 (configurable). The
`POE_NODE_NAME` and `POE_NODE_IP` environment variables are required and will be
added as labels (`node_name` and `node_ip`) to all metrics for easier
identification in multi-node environments.

Available metrics:

```text
# HELP rockpi_poe_temperature_celsius Current temperature in Celsius
# TYPE rockpi_poe_temperature_celsius gauge
rockpi_poe_temperature_celsius{sensor_type="thermal_zone_cpu",node_name="rockpi-01",node_ip="192.168.1.100"} 40.05
rockpi_poe_temperature_celsius{sensor_type="thermal_zone_gpu",node_name="rockpi-01",node_ip="192.168.1.100"} 36.25
rockpi_poe_temperature_celsius{sensor_type="composite_max",node_name="rockpi-01",node_ip="192.168.1.100"} 40.05
# HELP rockpi_poe_fan_speed_percent Current fan speed as percentage
# TYPE rockpi_poe_fan_speed_percent gauge
rockpi_poe_fan_speed_percent{node_name="rockpi-01",node_ip="192.168.1.100"} 25.0
# HELP rockpi_poe_fan_enabled Fan enabled status (1=enabled, 0=disabled)
# TYPE rockpi_poe_fan_enabled gauge
rockpi_poe_fan_enabled{node_name="rockpi-01",node_ip="192.168.1.100"} 1.0
# HELP rockpi_poe_fan_speed_changes_total Total number of fan speed changes
# TYPE rockpi_poe_fan_speed_changes_total gauge
rockpi_poe_fan_speed_changes_total{node_name="rockpi-01",node_ip="192.168.1.100"} 46.0
# HELP rockpi_poe_controller_uptime_seconds Controller uptime in seconds
# TYPE rockpi_poe_controller_uptime_seconds gauge
rockpi_poe_controller_uptime_seconds{node_name="rockpi-01",node_ip="192.168.1.100"} 830.2532060146332
# HELP rockpi_poe_temperature_read_errors_total Total number of temperature read errors
# TYPE rockpi_poe_temperature_read_errors_total gauge
# HELP rockpi_poe_gpio_errors_total Total number of GPIO errors
# TYPE rockpi_poe_gpio_errors_total gauge
```

## License

See [LICENSE](./LICENSE)
