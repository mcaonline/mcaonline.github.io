# Nanoleaf Essentials Integration

A custom Home Assistant integration specifically designed for Nanoleaf Essentials devices that solves known API communication issues.

## Features

- Complete control over Nanoleaf Essentials devices
- Robust API communication with error handling
- Brightness, color, and effect controls
- Automatic device discovery
- Solves POST/GET issues with standard integration

## Installation

1. Install via HACS
2. Restart Home Assistant
3. Add integration via Settings → Devices & Services
4. Follow the setup wizard to connect your Nanoleaf Essentials

## Configuration

The integration uses a configuration flow - no YAML configuration needed!

1. Enter your device IP address
2. Enable API access in the Nanoleaf mobile app
3. Complete setup within 30 seconds

## Supported Devices

- Nanoleaf Essentials A19 Bulb
- Nanoleaf Essentials Lightstrip
- Other Nanoleaf Essentials devices

## Troubleshooting

Enable debug logging by adding to configuration.yaml:

```yaml
logger:
  default: info
  logs:
    custom_components.nanoleaf_essentials: debug
```

## Support

Report issues on GitHub: [Repository Issues](https://github.com/yourusername/nanoleaf-essentials-hass/issues)