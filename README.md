# SF Street Cleaning Home Assistant Integration

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

This component fires an event `sf_street_cleaning_alert` when a high-priority warning is detected. Use this to send notifications.

### Example Automation (`automations.yaml`)

```yaml
alias: "SF Street Cleaning Alert"
description: "Notify when parked in a street cleaning zone."
trigger:
  - platform: event
    event_type: sf_street_cleaning_alert
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🧹 Street Cleaning Warning!"
      message: >
        Your car is parked on {{ trigger.event.data.street }} ({{ trigger.event.data.side }}).
        Cleaning starts at {{ trigger.event.data.next_cleaning }}.
        Please move it within {{ trigger.event.data.hours_until }} hours!
      data:
        push:
            sound: "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"
            importance: high
```
