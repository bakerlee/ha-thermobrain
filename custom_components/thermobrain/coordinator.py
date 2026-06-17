"""Recommendation coordinator for Thermobrain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_ENTITY_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    ACTION_COOL,
    ACTION_HEAT,
    ACTION_IDLE,
    ACTION_UNKNOWN,
    CONF_CLIMATE_ENTITY,
    CONF_COST_STRATEGY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_SLEEP_START_HOUR,
    CONF_SLEEP_TEMPERATURE,
    CONF_WAKE_HOUR,
    CONF_WAKE_TEMPERATURE,
    CONF_WEATHER_ENTITY,
    COST_STRATEGY_COMFORT,
    COST_STRATEGY_SAVINGS,
    DOMAIN,
    SERVICE_GET_FORECASTS,
    WEATHER_DOMAIN,
)

UPDATE_INTERVAL = timedelta(minutes=5)
FORECAST_LOOKAHEAD_HOURS = 4
WAKE_RECOVERY_WINDOW_HOURS = 2

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Recommendation:
    """Represent the latest advisory recommendation."""

    action: str
    perceived_temperature: float | None
    recommended_heat_setpoint: float | None
    recommended_cool_setpoint: float | None
    confidence: int
    reason: str
    target_temperature: float | None
    indoor_temperature: float | None
    outdoor_temperature: float | None
    forecast_high_temperature: float | None
    temperature_unit: str


class ThermobrainCoordinator(DataUpdateCoordinator[Recommendation]):
    """Calculate advisory thermostat recommendations for one zone."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.config_entry = config_entry

    async def _async_update_data(self) -> Recommendation:
        """Fetch inputs and calculate the latest recommendation."""
        data = self.config_entry.data
        temperature_unit = self.hass.config.units.temperature_unit

        climate_state = self.hass.states.get(data[CONF_CLIMATE_ENTITY])
        weather_entity_id = data.get(CONF_WEATHER_ENTITY)
        weather_state = (
            self.hass.states.get(weather_entity_id) if weather_entity_id else None
        )

        indoor_temperature = _float_or_none(
            self._read_indoor_temperature(climate_state, data)
        )
        outdoor_temperature = _float_or_none(
            weather_state.attributes.get(ATTR_TEMPERATURE) if weather_state else None
        )
        forecast_high_temperature = await self._forecast_high_temperature()

        if indoor_temperature is None:
            return Recommendation(
                action=ACTION_UNKNOWN,
                perceived_temperature=None,
                recommended_heat_setpoint=None,
                recommended_cool_setpoint=None,
                confidence=0,
                reason="No indoor temperature is available from the configured sensor or climate entity.",
                target_temperature=None,
                indoor_temperature=None,
                outdoor_temperature=outdoor_temperature,
                forecast_high_temperature=forecast_high_temperature,
                temperature_unit=temperature_unit,
            )

        target_temperature = self._current_target_temperature()
        perceived_temperature = self._perceived_temperature(
            indoor_temperature, outdoor_temperature, target_temperature
        )
        allowed_drift = self._allowed_drift()

        action = ACTION_IDLE
        heat_setpoint: float | None = None
        cool_setpoint: float | None = None
        reason = "Comfort is within the current allowed drift."

        if perceived_temperature < target_temperature - allowed_drift:
            if self._can_skip_wake_heating(indoor_temperature, forecast_high_temperature):
                reason = (
                    "Advising idle because the near-term outdoor forecast is warm "
                    "enough to let the zone recover without heat."
                )
            else:
                action = ACTION_HEAT
                heat_setpoint = target_temperature
                reason = (
                    "Perceived comfort is below target after "
                    "outdoor-temperature adjustment."
                )
        elif perceived_temperature > target_temperature + allowed_drift:
            action = ACTION_COOL
            cool_setpoint = target_temperature
            reason = (
                "Perceived comfort is above target after "
                "outdoor-temperature adjustment."
            )

        return Recommendation(
            action=action,
            perceived_temperature=round(perceived_temperature, 1),
            recommended_heat_setpoint=heat_setpoint,
            recommended_cool_setpoint=cool_setpoint,
            confidence=self._confidence(indoor_temperature, outdoor_temperature),
            reason=reason,
            target_temperature=target_temperature,
            indoor_temperature=indoor_temperature,
            outdoor_temperature=outdoor_temperature,
            forecast_high_temperature=forecast_high_temperature,
            temperature_unit=temperature_unit,
        )

    def _read_indoor_temperature(self, climate_state: Any, data: dict[str, Any]) -> Any:
        """Read the configured indoor temperature source."""
        indoor_entity_id = data.get(CONF_INDOOR_TEMPERATURE_ENTITY)
        if indoor_entity_id:
            indoor_state = self.hass.states.get(indoor_entity_id)
            if indoor_state is not None:
                return indoor_state.state

        if climate_state is None:
            return None

        return climate_state.attributes.get("current_temperature")

    async def _forecast_high_temperature(self) -> float | None:
        """Read the highest near-term weather forecast temperature when available."""
        weather_entity_id = self.config_entry.data.get(CONF_WEATHER_ENTITY)
        if not weather_entity_id:
            return None

        try:
            response = await self.hass.services.async_call(
                WEATHER_DOMAIN,
                SERVICE_GET_FORECASTS,
                {CONF_ENTITY_ID: weather_entity_id, "type": "hourly"},
                blocking=True,
                return_response=True,
            )
        except HomeAssistantError as err:
            LOGGER.debug(
                "Could not fetch hourly forecast for %s: %s", weather_entity_id, err
            )
            return None

        forecast = (response or {}).get(weather_entity_id, {}).get("forecast", [])
        temperatures: list[float] = []
        now = dt_util.utcnow()
        horizon = now + timedelta(hours=FORECAST_LOOKAHEAD_HOURS)

        for item in forecast:
            forecast_time = dt_util.parse_datetime(item.get("datetime", ""))
            if forecast_time is not None and not (now <= forecast_time <= horizon):
                continue

            value = _float_or_none(
                item.get(ATTR_TEMPERATURE) or item.get("native_temperature")
            )
            if value is not None:
                temperatures.append(value)

        if temperatures:
            return round(max(temperatures), 1)

        return None

    def _current_target_temperature(self) -> float:
        """Return the current comfort target from the simple day/night schedule."""
        data = self.config_entry.data
        now_hour = dt_util.now().hour
        sleep_start = int(data[CONF_SLEEP_START_HOUR])
        wake_hour = int(data[CONF_WAKE_HOUR])

        if _hour_in_window(now_hour, sleep_start, wake_hour):
            return float(data[CONF_SLEEP_TEMPERATURE])

        return float(data[CONF_WAKE_TEMPERATURE])

    def _perceived_temperature(
        self,
        indoor_temperature: float,
        outdoor_temperature: float | None,
        target_temperature: float,
    ) -> float:
        """Apply a small outdoor-temperature comfort correction."""
        if outdoor_temperature is None:
            return indoor_temperature

        influence = self._outdoor_influence()
        delta = outdoor_temperature - target_temperature
        correction = max(-3.0, min(3.0, delta * influence))
        return indoor_temperature + correction

    def _allowed_drift(self) -> float:
        """Return allowed comfort drift for the configured cost strategy."""
        strategy = self.config_entry.data[CONF_COST_STRATEGY]
        if strategy == COST_STRATEGY_COMFORT:
            return 0.8
        if strategy == COST_STRATEGY_SAVINGS:
            return 2.0
        return 1.2

    def _outdoor_influence(self) -> float:
        """Return outdoor-temperature comfort influence for the cost strategy."""
        strategy = self.config_entry.data[CONF_COST_STRATEGY]
        if strategy == COST_STRATEGY_COMFORT:
            return 0.06
        if strategy == COST_STRATEGY_SAVINGS:
            return 0.03
        return 0.045

    def _can_skip_wake_heating(
        self,
        indoor_temperature: float,
        forecast_high_temperature: float | None,
    ) -> bool:
        """Return true when upcoming outdoor warmth should recover the zone."""
        if forecast_high_temperature is None:
            return False

        data = self.config_entry.data
        now_hour = dt_util.now().hour
        wake_hour = int(data[CONF_WAKE_HOUR])
        wake_target = float(data[CONF_WAKE_TEMPERATURE])

        hours_until_wake = (wake_hour - now_hour) % 24
        in_recovery_window = hours_until_wake <= WAKE_RECOVERY_WINDOW_HOURS

        return (
            in_recovery_window
            and indoor_temperature < wake_target
            and forecast_high_temperature >= wake_target
        )

    def _confidence(
        self,
        indoor_temperature: float | None,
        outdoor_temperature: float | None,
    ) -> int:
        """Return a simple confidence score for the advisory recommendation."""
        confidence = 40
        if indoor_temperature is not None:
            confidence += 30
        if outdoor_temperature is not None:
            confidence += 15
        if self.config_entry.data.get(CONF_WEATHER_ENTITY):
            confidence += 15
        return min(confidence, 100)


def _hour_in_window(hour: int, start: int, end: int) -> bool:
    """Return true when hour is inside a possibly overnight window."""
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


def _float_or_none(value: Any) -> float | None:
    """Convert a Home Assistant state value to float if possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
