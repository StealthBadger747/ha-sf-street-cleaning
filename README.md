# SF Street Cleaning Home Assistant Integration

[![Open your Home Assistant instance and adding repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=StealthBadger747&repository=ha-sf-street-cleaning&category=integration) [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=sf_street_cleaning)

A native Home Assistant Custom Component that monitors your vehicle's location (via `ha-fordpass`) and warns you about upcoming San Francisco street cleaning.

## Installation

### HACS

1.  Add this repository to HACS as a **Custom Repository**.
2.  Search for "SF Street Cleaning" and install.
3.  Restart Home Assistant.

## Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **Add Integration**.
3.  Search for **SF Street Cleaning**.
4.  Select your vehicle's **Device Tracker** entity (e.g., `device_tracker.fordpass_vin123`).
5.  Click **Submit**.

A new sensor `sensor.sf_street_cleaning_status` will be created.

## Notifications (Automation)

This integration provides the data (sensor attributes). You can create Automations in Home Assistant to notify you.

### Example 1: Imminent Warning (2 Hours Before)

```yaml
alias: "Street Cleaning: 2 Hour Warning"
trigger:
  - platform: numeric_state
    entity_id: sensor.sf_street_cleaning_status
    attribute: cleaning_in_hours
    below: 2.1
    above: 0
action:
  - action: notify.mobile_app_your_phone
    data:
      title: "🧹 Move Car Now!"
      message: "Cleaning starts in {{ state_attr('sensor.sf_street_cleaning_status', 'cleaning_in_hours') }} hours on {{ state_attr('sensor.sf_street_cleaning_status', 'street') }}."
      data:
        push:
            sound: "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"
            importance: high
```

### Example 2: Night Before Warning (10 PM)

Checks at 10 PM if there is cleaning *tomorrow morning* (e.g. within 12 hours).

```yaml
alias: "Street Cleaning: Night Before"
trigger:
  - platform: time
    at: "22:00:00"
condition:
  - condition: numeric_state
    entity_id: sensor.sf_street_cleaning_status
    attribute: cleaning_in_hours
    below: 24 # 10 PM + 24h = covers all street cleaning for the next day.
    above: 0
action:
  - action: notify.mobile_app_your_phone
    data:
      title: "🧹 Cleaning Tomorrow Morning"
      message: "Don't forget! Cleaning on {{ state_attr('sensor.sf_street_cleaning_status', 'street') }} is tomorrow at {{ state_attr('sensor.sf_street_cleaning_status', 'next_cleaning') }}."
```

### Example 3: Parked Notification

Trigger when you park the car (Ignition Off). Wait 2 minutes for GPS to update, then notify if there is an upcoming cleaning.

```yaml
alias: "Street Cleaning: Parked Check"
trigger:
  - platform: state
    entity_id: sensor.fordpass_ignitionstatus
    from: "On"
    to: "Off"
    for: "00:01:00" # Wait 1 mins for GPS to settle
condition:
  - condition: numeric_state
    entity_id: sensor.sf_street_cleaning_status
    attribute: cleaning_in_hours
    above: 0
    below: 72 # Only notify if cleaning is within 3 days
action:
  - action: notify.mobile_app_your_phone
    data:
      title: "🚗 Parked in SF"
      message: "You are parked on {{ state_attr('sensor.sf_street_cleaning_status', 'street') }}. Next cleaning is {{ state_attr('sensor.sf_street_cleaning_status', 'next_cleaning') }}."
```

## Testing

To verify everything is working without waiting for street cleaning:

### 1. Test the Automations
Go to **Settings > Automations**.
1.  Find your create automation.
2.  Click the three dots -> **Run**.
3.  Verify you get the notification on your phone.

### 2. Test the Sensor Logic
Go to **Developer Tools > States**.
1.  Find your `device_tracker` entity (e.g. `device_tracker.fordpass_...`).
2.  Note its current state.
3.  **Set State** to a location in a cleaning zone:
    *   **State**: `not_home`
    *   **Attributes**: Paste the current attributes but change `latitude` and `longitude`.
    *   **Coordinates for Testing (Marina)**:
        *   Lat: `37.8000`
        *   Lon: `-122.4400`
        *   Heading: `0` (North)
4.  Click **Set State**.
5.  Check `sensor.sf_street_cleaning_status`. Any automation looking for `cleaning_in_hours` should trigger if the time aligns.

