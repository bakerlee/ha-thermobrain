"""Config flow for Adaptive Comfort."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, UnitOfTemperature
from homeassistant.helpers import selector

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_COST_STRATEGY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
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


class AdaptiveComfortConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Adaptive Comfort config flow."""

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
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._data_schema(),
            errors=errors,
        )

    def _data_schema(self) -> vol.Schema:
        """Return the user step schema."""
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
                vol.Required(CONF_NAME, default="Primary bedroom"): str,
                vol.Required(CONF_CLIMATE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate")
                ),
                vol.Optional(CONF_INDOOR_TEMPERATURE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_WEATHER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="weather")
                ),
                vol.Required(
                    CONF_SLEEP_TEMPERATURE, default=default_sleep_temperature
                ): temperature_selector,
                vol.Required(
                    CONF_WAKE_TEMPERATURE, default=default_wake_temperature
                ): temperature_selector,
                vol.Required(
                    CONF_SLEEP_START_HOUR, default=DEFAULT_SLEEP_START_HOUR
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=23,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_WAKE_HOUR, default=DEFAULT_WAKE_HOUR
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=23,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_COST_STRATEGY, default=COST_STRATEGY_BALANCED
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
