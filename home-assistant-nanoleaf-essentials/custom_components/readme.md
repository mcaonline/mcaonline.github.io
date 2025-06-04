# Nanoleaf Essentials Home Assistant Integration

A custom integration for Home Assistant specifically developed for Nanoleaf Essentials devices. This integration solves known issues with the standard Nanoleaf integration and provides a more stable connection to Essentials devices.

## 🌟 Features

- ✅ Turn Nanoleaf Essentials on/off
- ✅ Brightness control (0-100%)
- ✅ RGB color control
- ✅ Effects support
- ✅ Automatic device discovery
- ✅ German and English translations
- ✅ Robust API communication
- ✅ Simple setup process

## 📋 Requirements

- Home Assistant Core 2023.1 or newer
- Nanoleaf Essentials device on the same network
- Nanoleaf Mobile App on your smartphone

## 🚀 Installation

### Method 1: Manual Installation

#### 1. Create Directory Structure

Create the following folder structure in your Home Assistant `config` directory:

```
/config/custom_components/nanoleaf_essentials/
├── __init__.py
├── manifest.json
├── const.py
├── config_flow.py
├── coordinator.py
├── light.py
├── strings.json
└── translations/
    ├── en.json
    └── de.json
```

#### 2. Copy Files

**Option A: SSH/Terminal**
```bash
cd /config
mkdir -p custom_components/nanoleaf_essentials/translations
# Copy all files to the corresponding folders
```

**Option B: File Editor Add-on**
1. Install the "File Editor" add-on from the Add-on Store
2. Open File Editor
3. Create the folder structure
4. Copy the content of each file individually

**Option C: Samba/CIFS Share**
1. Connect via Samba to your Home Assistant
2. Navigate to the `config` folder
3. Create the folder structure and copy all files

#### 3. Restart Home Assistant

Restart Home Assistant:
- **UI**: `Settings` → `System` → `Restart`
- **CLI**: `ha core restart`

### Method 2: Git Installation

```bash
cd /config/custom_components
git clone https://github.com/yourusername/nanoleaf-essentials.git nanoleaf_essentials
```

## ⚙️ Configuration

### 1. Add Integration

1. Go to `Settings` → `Devices & Services`
2. Click `Add Integration`
3. Search for "Nanoleaf Essentials"
4. Select the integration

### 2. Device Setup

#### Step 1: Enter IP Address
- Enter the IP address of your Nanoleaf Essentials device
- Example: `192.168.0.80`
- The integration automatically tests the connection on port 16021

#### Step 2: Enable API Access
After entering the IP, instructions will appear:

**📱 In the Nanoleaf App:**
1. Open the Nanoleaf App
2. Go to `More` → `My Devices`
3. Select your Essentials Light
4. Make sure you are connected (e.g. APP via Bluetooth or IP)
5. Tap the **three dots** (⋮)
6. Select `Preferences`
7. Tap `Connect to the API`
8. **Important**: Press "OK" in Home Assistant **within 30 seconds**

#### Step 3: Completion
- The integration automatically retrieves the API key
- The device is added as a Light entity
- Setup is complete!

## 🎮 Usage

### Light Entity
After successful setup, a Light entity will be available:
- **Name**: `light.nanoleaf_essentials_[IP]`
- **Functions**: On/Off, Brightness, Color, Effects

### Example Automations

**Turn on at sunset:**
```yaml
automation:
  - alias: "Turn on Nanoleaf at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: light.turn_on
      target:
        entity_id: light.nanoleaf_essentials_10_80_23_56
      data:
        brightness: 180
        rgb_color: [255, 200, 100]
```

**Color based on time of day:**
```yaml
automation:
  - alias: "Nanoleaf color by time"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: light.turn_on
      target:
        entity_id: light.nanoleaf_essentials_10_80_23_56
      data:
        effect: "Energize"
```

## 🔧 Troubleshooting

### Common Issues

#### "Cannot connect" error
- ✅ Check the device's IP address
- ✅ Ensure port 16021 is reachable
- ✅ Verify the device is reachable via ip / network

#### "Timeout" during API setup
- ✅ API access enabled in the app within 30 seconds?
- ✅ Bluetooth connection to the app active?
- ✅ Device is online and reachable?

#### Entity doesn't appear
- ✅ Check Home Assistant logs
- ✅ Integration installed correctly?
- ✅ Home Assistant restarted?

### Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.nanoleaf_essentials: debug
```

Find logs under: `Settings` → `System` → `Logs`

### Manual API Testing

You can test the API manually:

```bash
# Get API key (device must be in pairing mode)
curl -X GET http://[IP]:16021/api/v1/new

# Query status
curl -X GET http://[IP]:16021/api/v1/[API_KEY]/state

# Turn on light
curl -X PUT http://[IP]:16021/api/v1/[API_KEY]/state \
  -H "Content-Type: application/json" \
  -d '{"on":{"value":true}}'
```

## 📊 Supported Devices

This integration has been tested with:
- ✅ Nanoleaf Essentials Lightstrip HD (NL72K1) via IP Connectivity (WLAN)


*Other Essentials devices should also work.*

## 🔄 Updates

### Manual Updates
1. Download the latest files
2. Replace files in the `custom_components/nanoleaf_essentials/` folder
3. Restart Home Assistant

### Git Updates
```bash
cd /config/custom_components/nanoleaf_essentials
git pull origin main
```

## 🐛 Report Issues

If you find problems:

1. **Check the logs** with debug logging enabled
2. **Create an issue** with the following information:
   - Home Assistant version
   - Nanoleaf device model
   - Error message/logs
   - Steps to reproduce

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Create a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the official Nanoleaf integration
- Inspired by community feedback on Essentials issues
- Thanks to all beta testers

## 📚 Additional Resources

- [Home Assistant Custom Integrations](https://developers.home-assistant.io/docs/creating_integration_file_structure)
- [Nanoleaf API Documentation](https://forum.nanoleaf.me/docs)
- [Home Assistant Community Forum](https://community.home-assistant.io/)

---

**Made with ❤️ for the Home Assistant Community**