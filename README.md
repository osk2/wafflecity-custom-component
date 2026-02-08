<img src="assets/icon.png" alt="Waffle City" width="128">

# Waffle City Custom Component for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
![GitHub release (latest version)](https://img.shields.io/github/v/release/osk2/wafflecity-custom-component?style=for-the-badge)
[![GitHub license](https://img.shields.io/github/license/osk2/wafflecity-custom-component?style=for-the-badge)](https://github.com/osk2/wafflecity-custom-component/blob/master/LICENSE)

**English** | [繁體中文](README.zh-Hant.md)

Home Assistant integration for Waffle City (窩福社區) package tracking.

## Features

- Track pending packages at your building
- Automatic polling every 15 minutes
- Package details available as sensor attributes

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add `https://github.com/osk2/wafflecity-custom-component` with category "Integration"
5. Search for "Waffle City" and install
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/wafflecity` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Waffle City"
4. Enter your credentials:
   - **Phone Number**: Your registered phone number
   - **Password**: Your account password
   - **Country Code**: Select your country (default: TW)

## Sensor

The integration creates a sensor `sensor.waffle_city_pending_packages` with:

- **State**: Number of pending packages
- **Attributes**:
  - `packages`: List of package details
  - `user_id`: Your Waffle City user ID

## Automation Example

```yaml
automation:
  - alias: "Notify New Package"
    trigger:
      - platform: state
        entity_id: sensor.waffle_city_pending_packages
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
    action:
      - service: notify.mobile_app
        data:
          title: "New Package Arrived"
          message: "You have {{ states('sensor.waffle_city_pending_packages') }} package(s) waiting."
```

## Supported Countries

TW, CN, HK, MO, JP, KR, TH, SG, MY, ID, VN, PH, AU, IN

## License

MIT
