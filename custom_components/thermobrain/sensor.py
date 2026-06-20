"""Sensor platform for Thermobrain."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ACTION_COOL,
    ACTION_HEAT,
    ACTION_IDLE,
    ACTION_UNKNOWN,
    CONF_CLIMATE_ENTITY,
    DOMAIN,
)
from .coordinator import Recommendation, ThermobrainCoordinator


@dataclass(frozen=True, kw_only=True)
class ThermobrainSensorEntityDescription(SensorEntityDescription):
    """Describe a Thermobrain sensor."""

    value_fn: Callable[[Recommendation], str | int | float | None]
    unit_fn: Callable[[Recommendation], str | None] = lambda data: None


SENSOR_DESCRIPTIONS: tuple[ThermobrainSensorEntityDescription, ...] = (
    ThermobrainSensorEntityDescription(
        key="recommended_action",
        translation_key="recommended_action",
        device_class=SensorDeviceClass.ENUM,
        options=[ACTION_HEAT, ACTION_COOL, ACTION_IDLE, ACTION_UNKNOWN],
        value_fn=lambda data: data.action,
    ),
    ThermobrainSensorEntityDescription(
        key="recommended_heat_setpoint",
        translation_key="recommended_heat_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: data.recommended_heat_setpoint,
        unit_fn=lambda data: data.temperature_unit,
    ),
    ThermobrainSensorEntityDescription(
        key="recommended_cool_setpoint",
        translation_key="recommended_cool_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: data.recommended_cool_setpoint,
        unit_fn=lambda data: data.temperature_unit,
    ),
    ThermobrainSensorEntityDescription(
        key="perceived_temperature",
        translation_key="perceived_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: data.perceived_temperature,
        unit_fn=lambda data: data.temperature_unit,
    ),
    ThermobrainSensorEntityDescription(
        key="target_temperature",
        translation_key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda data: data.target_temperature,
        unit_fn=lambda data: data.temperature_unit,
    ),
    ThermobrainSensorEntityDescription(
        key="confidence",
        translation_key="confidence",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.confidence,
        unit_fn=lambda data: PERCENTAGE,
    ),
    ThermobrainSensorEntityDescription(
        key="reason",
        translation_key="reason",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.reason,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Thermobrain sensors from a config entry."""
    coordinator = ThermobrainCoordinator(hass, entry)
    entry.async_on_unload(coordinator.async_track_source_updates())
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    device_info = _thermobrain_device_info(hass, entry)
    async_add_entities(
        ThermobrainSensor(coordinator, entry, description, device_info)
        for description in SENSOR_DESCRIPTIONS
    )


def _thermobrain_device_info(hass: HomeAssistant, entry: ConfigEntry) -> DeviceInfo:
    """Return device info for the Thermobrain advisory zone."""
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Thermobrain",
        model="Advisory thermostat zone",
        name=entry.title,
    )
    if via_device := _source_via_device(hass, entry):
        device_info["via_device"] = via_device

    return device_info


def _source_via_device(
    hass: HomeAssistant, entry: ConfigEntry
) -> tuple[str, str] | None:
    """Return the configured climate device identifier for topology linking."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    source_entity = entity_registry.async_get(entry.data[CONF_CLIMATE_ENTITY])
    if source_entity is None or source_entity.device_id is None:
        return None

    source_device = device_registry.async_get(source_entity.device_id)
    if source_device is None:
        return None

    return next(iter(sorted(source_device.identifiers)), None)


class ThermobrainSensor(CoordinatorEntity[ThermobrainCoordinator], SensorEntity):
    """Represent a Thermobrain advisory sensor."""

    entity_description: ThermobrainSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ThermobrainCoordinator,
        entry: ConfigEntry,
        description: ThermobrainSensorEntityDescription,
        device_info: DeviceInfo | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> str | int | float | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the native unit of measurement."""
        return self.entity_description.unit_fn(self.coordinator.data)
