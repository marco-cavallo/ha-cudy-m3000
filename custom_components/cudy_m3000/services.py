# Copyright 2026 Marco Cavallo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Servizi Home Assistant per amministrare il mesh Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .admin import DIAGNOSTIC_TOOLS
from .api import CudyError
from .const import DOMAIN
from .coordinator import CudyM3000Coordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_REBOOT_NODE = "reboot_node"
SERVICE_SET_LED = "set_led"
SERVICE_RUN_DIAGNOSTIC = "run_diagnostic"
SERVICE_REFRESH = "refresh"

ATTR_DEVICE_ID = "device_id"
ATTR_LED = "led"
ATTR_TOOL = "tool"
ATTR_TARGET = "target"

_NODE_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})

_LED_SCHEMA = _NODE_SCHEMA.extend({vol.Required(ATTR_LED): cv.boolean})

_DIAG_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TOOL): vol.In(list(DIAGNOSTIC_TOOLS)),
        vol.Required(ATTR_TARGET): cv.string,
    }
)


def _loaded_coordinators(hass: HomeAssistant) -> list[CudyM3000Coordinator]:
    """Coordinator di tutte le istanze caricate."""
    return [
        entry.runtime_data
        for entry in hass.config_entries.async_loaded_entries(DOMAIN)
        if getattr(entry, "runtime_data", None) is not None
    ]


def _first(hass: HomeAssistant) -> CudyM3000Coordinator:
    """Il coordinator della prima istanza, o un errore parlante."""
    found = _loaded_coordinators(hass)
    if not found:
        raise HomeAssistantError("Integrazione Cudy M3000 non caricata")
    return found[0]


def _resolve_node(hass: HomeAssistant, device_id: str) -> tuple[CudyM3000Coordinator, str]:
    """Risale dal device di Home Assistant al nodo mesh corrispondente."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise HomeAssistantError(f"Dispositivo sconosciuto: {device_id}")

    keys = {
        identifier[1]
        for identifier in device.identifiers
        if identifier[0] == DOMAIN
    }
    for coordinator in _loaded_coordinators(hass):
        for node_id, node in coordinator.data.nodes.items():
            if node.unique_key in keys:
                return coordinator, node_id

    raise HomeAssistantError(
        f"Il dispositivo {device.name} non è un nodo mesh Cudy"
    )


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Registra i servizi dell'integrazione, una volta sola."""
    if hass.services.has_service(DOMAIN, SERVICE_REBOOT_NODE):
        return

    async def _reboot(call: ServiceCall) -> None:
        """Riavvia un nodo mesh."""
        coordinator, node_id = _resolve_node(hass, call.data[ATTR_DEVICE_ID])
        node = coordinator.data.nodes[node_id]
        try:
            if node.is_root:
                await coordinator.admin.async_reboot_router()
            else:
                await coordinator.admin.async_node_action(node_id, "reboot")
        except CudyError as err:
            raise HomeAssistantError(f"Riavvio non riuscito: {err}") from err

    async def _set_led(call: ServiceCall) -> None:
        """Accende o spegne il LED di un nodo."""
        coordinator, node_id = _resolve_node(hass, call.data[ATTR_DEVICE_ID])
        try:
            await coordinator.admin.async_set_led(node_id, call.data[ATTR_LED])
        except CudyError as err:
            raise HomeAssistantError(f"LED non commutabile: {err}") from err
        await coordinator.async_refresh()

    async def _diagnostic(call: ServiceCall) -> ServiceResponse:
        """Esegue uno strumento diagnostico e ne restituisce l'output."""
        coordinator = _first(hass)
        try:
            output = await coordinator.admin.async_run_diagnostic(
                call.data[ATTR_TOOL], call.data[ATTR_TARGET]
            )
        except CudyError as err:
            raise HomeAssistantError(f"Diagnostica non riuscita: {err}") from err
        return {"output": output}

    async def _refresh(call: ServiceCall) -> None:
        """Forza una lettura immediata del router."""
        for coordinator in _loaded_coordinators(hass):
            await coordinator.async_refresh()

    hass.services.async_register(DOMAIN, SERVICE_REBOOT_NODE, _reboot, _NODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_LED, _set_led, _LED_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_RUN_DIAGNOSTIC,
        _diagnostic,
        _DIAG_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(DOMAIN, SERVICE_REFRESH, _refresh)


@callback
def async_unregister_services(hass: HomeAssistant) -> None:
    """Rimuove i servizi quando sparisce l'ultima istanza."""
    for service in (
        SERVICE_REBOOT_NODE,
        SERVICE_SET_LED,
        SERVICE_RUN_DIAGNOSTIC,
        SERVICE_REFRESH,
    ):
        hass.services.async_remove(DOMAIN, service)
