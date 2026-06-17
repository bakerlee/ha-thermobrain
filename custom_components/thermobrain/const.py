"""Constants for Thermobrain."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "thermobrain"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_CLIMATE_ENTITY = "climate_entity"
CONF_INDOOR_TEMPERATURE_ENTITY = "indoor_temperature_entity"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_SLEEP_TEMPERATURE = "sleep_temperature"
CONF_WAKE_TEMPERATURE = "wake_temperature"
CONF_SLEEP_START_HOUR = "sleep_start_hour"
CONF_WAKE_HOUR = "wake_hour"
CONF_COST_STRATEGY = "cost_strategy"

DEFAULT_SLEEP_START_HOUR = 22
DEFAULT_WAKE_HOUR = 7

COST_STRATEGY_COMFORT = "comfort"
COST_STRATEGY_BALANCED = "balanced"
COST_STRATEGY_SAVINGS = "savings"

ACTION_HEAT = "heat"
ACTION_COOL = "cool"
ACTION_IDLE = "idle"
ACTION_UNKNOWN = "unknown"

SERVICE_GET_FORECASTS = "get_forecasts"
WEATHER_DOMAIN = "weather"
