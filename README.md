# Thermobrain

Thermobrain is a Home Assistant custom integration for experimenting with a
software-only thermostat supervisor.

The first milestone is intentionally advisory-only. It observes an existing
`climate` entity, an optional indoor temperature sensor, and an optional
`weather` entity, then publishes recommendation sensors. It does not control
HVAC equipment yet.

## Current Features

- One Home Assistant config entry per zone.
- Multiple zones by adding the integration more than once.
- Recommendation sensors attach to the configured thermostat device when it has
  a Home Assistant device registry entry.
- Advisory sensors for recommended action, heat setpoint, cool setpoint,
  perceived temperature, confidence, and reason.
- Simple day/night schedule with sleep and wake temperatures.
- Cost strategy selector: comfort, balanced, or savings.
- Outdoor-temperature comfort adjustment.
- Hourly weather forecast lookup via Home Assistant's `weather.get_forecasts`
  action when a weather entity is configured.

## Installation

### HACS

Add this repository to HACS as a custom repository of type **Integration**:

```text
https://github.com/bakerlee/ha-better-thermostat
```

Install **Thermobrain** from HACS, then restart Home Assistant.

### Manual

Copy `custom_components/thermobrain` into your Home Assistant
`custom_components` directory and restart Home Assistant.

Then add the integration from the UI:

1. Go to **Settings** > **Devices & services**.
2. Select **Add integration**.
3. Search for **Thermobrain**.
4. Add one zone by choosing the thermostat, optional indoor temperature sensor,
   optional weather entity, sleep/wake temperatures, sleep/wake hours, and cost
   strategy.

## Entities

Each zone exposes these sensors:

- Recommended action
- Recommended heat setpoint
- Recommended cool setpoint
- Perceived temperature
- Target temperature
- Indoor temperature
- Outdoor temperature
- Forecast high temperature
- Confidence
- Reason

## Current Limitations

- Advisory-only. It does not call `climate.set_temperature` or change HVAC mode.
- The schedule is only a simple sleep window and wake target.
- The forecast model is deliberately simple and transparent.
- There is no learned thermal model yet.
- Full-control mode, anti-short-cycle enforcement, and multi-zone global
  optimization are future work.
