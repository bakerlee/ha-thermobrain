# Existing Home Assistant Thermostat Research for Thermobrain

Date: 2026-06-17

## Question

Does an existing Home Assistant integration already provide the desired Thermobrain behavior?

Desired shape:

- Software-only controller that ultimately interfaces with existing Home Assistant climate entities.
- Multiple zones.
- Advisory-only and full-control execution modes.
- Uses Home Assistant weather integrations and forecasts.
- Optimizes a tradeoff between comfort deviation and operating cost.
- Handles outdoor-temperature-influenced comfort, forecast-aware morning recovery, and tighter heat/cool behavior than a fixed heat/cool deadband.
- Leaves room for post-MVP learning of house response and user preferences.

## Search Method

I searched the Home Assistant official documentation, HACS-adjacent GitHub projects, GitHub repository search, and known community thermostat projects. Search themes included:

- Home Assistant smart thermostat
- Home Assistant thermostat weather forecast
- Home Assistant thermostat PID
- Home Assistant thermostat HACS
- predictive, AI, digital twin, outdoor temperature, auto heat/cool, weather compensation

## Short Answer

I did not find an existing integration that should be adopted as-is for Thermobrain.

The closest existing project is Versatile Thermostat. It is mature and actively maintained, supports many underlying device types, can wrap existing climate entities, has centralized configuration, has self-regulation, and can account for outdoor temperature in some algorithms. But it does not appear to provide an advisory-only mode, forecast-aware planning over a future schedule, a cost-vs-comfort objective, or the specific "do not heat before wake if free outdoor recovery will happen" behavior.

OASIS Climate is conceptually closest to predictive/digital-twin optimization, but as of this research it is a very small, unreleased, closed-beta/coming-soon project rather than a usable replacement.

## Candidate Projects

### Home Assistant Generic Thermostat

Source: https://www.home-assistant.io/integrations/generic_thermostat/

Why it matters:

- Official Home Assistant helper.
- Converts a temperature sensor plus a switch into a climate entity.
- Supports heat or cool mode, tolerances, cycle limits, keepalive, and preset temperatures.

Gaps:

- One entity can only control one switch. The docs explicitly state that heat and AC require two Generic Thermostat entities.
- No multi-zone supervisory controller.
- No forecast use.
- No cost/comfort optimization.
- No advisory-only mode.
- No learning.

Verdict: Useful baseline behavior and a compatibility reference, but not a solution.

### Better Thermostat

Source: https://github.com/KartoffelToby/better_thermostat

Why it matters:

- Active and popular HACS integration.
- Wraps Home Assistant climate entities.
- Uses room sensors, window/door sensors, weather forecasts, or an outdoor sensor.
- Supports grouped TRVs, configurable presets, dynamic preset learning, and advanced algorithms including MPC, PID, TPI, and time-based control.
- Latest GitHub release observed during research: 1.8.2 on 2026-06-13.

Gaps:

- Framed primarily around TRVs/radiator thermostats.
- Existing weather use appears oriented around deciding whether to heat and improving TRV behavior, not optimizing over a future comfort schedule and energy cost objective.
- No documented advisory-only mode.
- No explicit multi-zone global optimizer across physical climate entities.
- No explicit comfort model where outdoor temperature adjusts perceived indoor comfort.

Verdict: Strong prior art and maybe worth studying carefully before implementation. Not a drop-in match.

### Versatile Thermostat

Sources:

- https://github.com/jmcollin78/versatile_thermostat
- https://www.versatile-thermostat.org/en/
- https://www.versatile-thermostat.org/en/docs/creation/
- https://www.versatile-thermostat.org/en/docs/self-regulation/
- https://www.versatile-thermostat.org/en/docs/algorithms/

Why it matters:

- Active, mature HACS integration.
- Works over switches, valves, or existing climate entities.
- Provides centralized configuration and a central mode for many VTherms.
- Supports presets, windows, presence, motion, power shedding, central boiler control, safety, TPI, self-regulation, auto-start/stop, and direct valve control.
- The TPI algorithm includes outdoor temperature:

  `on_percent = coef_int * (target_temperature - current_temperature) + coef_ext * (target_temperature - outdoor_temperature)`

- Self-regulation can adjust the setpoint sent to an underlying climate entity based on room error, accumulated error, and outdoor-vs-target temperature.
- Auto-start/stop uses observed temperature slope to decide when to restart heating or cooling.

Gaps:

- The optimization appears local/regulatory, not a forecast-horizon scheduler.
- No documented advisory-only mode.
- No explicit user-facing cost-vs-comfort objective.
- No explicit support for using Home Assistant weather forecasts to choose not to heat/cool because upcoming weather will naturally recover the zone.
- Multi-zone support is present operationally via many VTherms and centralized control, but not obviously as a coupled global optimizer.
- Outdoor temperature is used for equipment regulation, not explicitly as a perceived-comfort correction.

Verdict: Closest mature existing integration. If the goal were "better Home Assistant thermostat today," this is the first thing to try. If the goal is the stated optimizer, it is prior art rather than a substitute.

### HASmartThermostat / Smart Thermostat PID

Source: https://github.com/ScratMan/HASmartThermostat

Why it matters:

- HACS-installable PID thermostat.
- Supports heater and cooler outputs.
- Supports multiple valves.
- Has outdoor temperature compensation:

  `E = Ke * (target_temp - outdoor_temp)`

Gaps:

- YAML-oriented PID controller rather than a user-trustable supervisory thermostat.
- Outdoor temperature compensation is current-condition feed-forward, not forecast planning.
- No advisory-only mode.
- No cost/comfort objective.
- No multi-zone optimizer beyond configuring multiple instances.

Verdict: Useful algorithmic reference for PID and outdoor compensation. Not the product shape.

### Dual Smart Thermostat

Source: https://github.com/swingerman/ha-dual-smart-thermostat

Why it matters:

- Enhanced generic thermostat with heat/cool, heat pump, fan, dry/humidity, floor temperature, presets, openings, and action reason tracking.
- Handles "keep between" style heat/cool behavior over switches and sensors.
- Has some outside-temperature behavior for fan economizer decisions.
- Active as of this research, with a push observed on 2026-06-15.

Gaps:

- Primarily an improved thermostat entity, not a predictive optimizer.
- No documented use of weather forecasts.
- No advisory-only mode.
- No cost/comfort objective.
- No learned house thermal model.
- Does not solve the "wake at 72 without unnecessary heat if the day will warm the house" behavior.

Verdict: Good reference for heat/cool mechanics and safety. Not the intended integration.

### hacker-cb Smart Thermostat

Source: https://github.com/hacker-cb/hassio-component-smart-thermostat

Why it matters:

- Provides auto heat/cool modes and PID support.

Gaps:

- Smaller and less feature-complete than the top candidates.
- No evidence of forecast planning, advisory mode, cost optimization, or multi-zone optimization.

Verdict: Not a substitute.

### Schedy / Scheduler Component

Sources:

- https://hass-apps.readthedocs.io/en/stable/apps/schedy/
- https://github.com/nielsfaber/scheduler-component

Why they matter:

- Mature scheduling approaches for Home Assistant entities, including thermostats/climate entities.
- Good references for schedule UX and timeline concepts.

Gaps:

- These schedule setpoints or states. They do not optimize HVAC operation against weather forecasts, perceived comfort, thermal response, and cost.
- No advisory/full-control thermostat brain.

Verdict: Useful UX inspiration, not the thermostat intelligence.

### OASIS Climate

Source: https://github.com/mircotaddei/oasis-climate-ha-integration

Why it matters:

- Conceptually close: claims predictive modeling, digital twin control, weather anticipation, thermal inertia exploitation, and comfort/energy optimization.

Gaps:

- Repository describes itself as "Coming Soon" and closed beta.
- No releases observed during research.
- Only 1 GitHub star observed during research.
- No evidence yet of a stable, installable, auditable Home Assistant integration.
- Unknown advisory/full-control behavior, multi-zone support, and licensing/practical deployment story.

Verdict: Watch, but do not depend on it for this project.

### Other Search Results

Many other GitHub results were vendor bridges, Lovelace thermostat cards, ESP32/Pico thermostat firmware, local DIY hardware projects, or tiny/archived experiments. They do not address the stated software-only Home Assistant supervisory-control problem.

Examples of non-matches:

- Vendor-specific bridges for Mysa, Themo, Tesla T-Smart, COSA/Nuvia, BTicino, Devi, Moneta, etc.
- Lovelace thermostat dashboards and timeline cards.
- ESP32 or Raspberry Pi thermostat firmware.
- Small zero/one-star "AI" or "smart thermostat" experiments without usable evidence.

## Home Assistant Platform Notes

Official Home Assistant APIs support the integration shape we want:

- Climate entities expose `HVACMode.AUTO`, `HVACMode.HEAT_COOL`, target temperature ranges, presets, and standard HVAC actions.
- Weather entities expose current weather attributes such as temperature, humidity, apparent temperature, wind, UV, and cloud coverage.
- Weather forecasts are available through a separate API. Home Assistant supports daily, hourly, and twice-daily forecast features, and the user-facing `weather.get_forecasts` action can retrieve forecasts from one or more weather entities.

This suggests Thermobrain should consume existing climate and weather entities rather than owning weather-provider integrations or physical HVAC drivers.

## Conclusion

Build Thermobrain as a new integration, but steal the right ideas:

- Use Versatile Thermostat as the main design reference for wrapping underlying climate entities, centralized multi-zone configuration, presets, safe regulation, and outdoor-temperature feed-forward.
- Use Better Thermostat as a reference for weather-aware TRV behavior, grouped devices, advanced algorithms, and Home Assistant custom-integration maturity.
- Use Dual Smart Thermostat as a reference for heat/cool range behavior, HVAC action reasoning, heat pump/fan/dry edge cases, and safety constraints.
- Use Home Assistant's official weather forecast APIs for provider-independent forecast input.

Thermobrain's unique product idea should be:

1. A supervisory optimizer over existing climate entities.
2. A zone model with ideal comfort temperature, acceptable deviation, and optional perceived-comfort correction from outdoor conditions.
3. A schedule/forecast horizon, initially simple and deterministic.
4. An explicit comfort-vs-cost setting, probably qualitative for MVP: conservative, balanced, aggressive.
5. Advisory mode first: publish recommended setpoints/actions and explanations without controlling devices.
6. Full-control mode later: apply setpoints to underlying climate entities with safety limits, anti-short-cycle rules, and clear traceability.

## MVP Research Recommendation

Before writing code, install and try Versatile Thermostat in a test Home Assistant instance if feasible. It may be good enough for some zones immediately, and it will expose practical requirements we should either match or deliberately avoid.

If building this project, do not start with machine learning. Start with a transparent model:

- Forecast input: current weather plus hourly forecast where available.
- Zone input: current temperature, humidity if available, desired comfort schedule, occupied/asleep state, and underlying climate capabilities.
- Cost/comfort knob: qualitative mode mapping to allowed drift, recovery aggressiveness, and minimum benefit threshold before actuation.
- Output in advisory mode: "recommended HVAC mode", "recommended heat setpoint", "recommended cool setpoint", "reason", "expected comfort deviation", and "confidence".
