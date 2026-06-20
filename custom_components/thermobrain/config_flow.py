"""Config flow for Thermobrain."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_COST_STRATEGY,
    CONF_SLEEP_START_HOUR,
    CONF_SLEEP_TEMPERATURE,
    CONF_WAKE_HOUR,
    CONF_WAKE_TEMPERATURE,
    CONF_WEATHER_ENTITY,
    COST_STRATEGY_BALANCED,
    COST_STRATEGY_COMFORT,
    COST_STRATEGY_SAVINGS,
    DEFAULT_SLEEP_START_HOUR,
    DEFAULT_WAKE_HOUR,
    DOMAIN,
)


class ThermobrainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Thermobrain config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_CLIMATE_ENTITY])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._climate_title(user_input[CONF_CLIMATE_ENTITY]),
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._data_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration of an existing entry."""
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_CLIMATE_ENTITY])
            self._abort_if_unique_id_mismatch()

            return self.async_update_reload_and_abort(
                entry,
                title=self._climate_title(user_input[CONF_CLIMATE_ENTITY]),
                data=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._data_schema(entry.data),
        )

    def _data_schema(self, defaults: dict[str, Any] | None = None) -> vol.Schema:
        """Return the config flow schema."""
        defaults = defaults or {}
        weather_entity_default = _default(
            defaults,
            CONF_WEATHER_ENTITY,
            self._single_weather_entity(),
        )
        temperature_unit = self.hass.config.units.temperature_unit
        if temperature_unit == UnitOfTemperature.CELSIUS:
            default_sleep_temperature = 19.5
            default_wake_temperature = 22.0
            temperature_min = 7
            temperature_max = 32
            temperature_step = 0.5
        else:
            default_sleep_temperature = 67.0
            default_wake_temperature = 72.0
            temperature_min = 45
            temperature_max = 90
            temperature_step = 0.5

        temperature_selector = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=temperature_min,
                max=temperature_max,
                step=temperature_step,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement=temperature_unit,
            )
        )

        return vol.Schema(
            {
                vol.Required(
                    CONF_CLIMATE_ENTITY,
                    default=_default(defaults, CONF_CLIMATE_ENTITY),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate")
                ),
                vol.Optional(
                    CONF_WEATHER_ENTITY,
                    default=weather_entity_default,
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="weather")
                ),
                vol.Required(
                    CONF_SLEEP_TEMPERATURE,
                    default=_default(
                        defaults,
                        CONF_SLEEP_TEMPERATURE,
                        default_sleep_temperature,
                    ),
                ): temperature_selector,
                vol.Required(
                    CONF_WAKE_TEMPERATURE,
                    default=_default(
                        defaults, CONF_WAKE_TEMPERATURE, default_wake_temperature
                    ),
                ): temperature_selector,
                vol.Required(
                    CONF_SLEEP_START_HOUR,
                    default=_default(
                        defaults,
                        CONF_SLEEP_START_HOUR,
                        DEFAULT_SLEEP_START_HOUR,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=23,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_WAKE_HOUR,
                    default=_default(defaults, CONF_WAKE_HOUR, DEFAULT_WAKE_HOUR),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=23,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_COST_STRATEGY,
                    default=_default(
                        defaults, CONF_COST_STRATEGY, COST_STRATEGY_BALANCED
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=COST_STRATEGY_COMFORT,
                                label="Comfort",
                            ),
                            selector.SelectOptionDict(
                                value=COST_STRATEGY_BALANCED,
                                label="Balanced",
                            ),
                            selector.SelectOptionDict(
                                value=COST_STRATEGY_SAVINGS,
                                label="Savings",
                            ),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

    def _climate_title(self, entity_id: str) -> str:
        """Return a human-friendly title for the selected thermostat."""
        state = self.hass.states.get(entity_id)
        if state is not None:
            return state.name

        entity_registry = er.async_get(self.hass)
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry is not None:
            return entity_entry.name or entity_entry.original_name or entity_id

        return entity_id

    def _single_weather_entity(self) -> Any:
        """Return the only available weather entity when there is exactly one."""
        weather_entity_ids = [
            state.entity_id for state in self.hass.states.async_all("weather")
        ]
        if len(weather_entity_ids) == 1:
            return weather_entity_ids[0]

        entity_registry = er.async_get(self.hass)
        weather_entity_ids = [
            entity_entry.entity_id
            for entity_entry in entity_registry.entities.values()
            if entity_entry.entity_id.startswith("weather.")
            and entity_entry.disabled_by is None
        ]
        if len(weather_entity_ids) == 1:
            return weather_entity_ids[0]

        return vol.UNDEFINED


def _default(
    defaults: dict[str, Any],
    key: str,
    fallback: Any = vol.UNDEFINED,
) -> Any:
    """Return a schema default only when one is available."""
    return defaults[key] if key in defaults else fallback
