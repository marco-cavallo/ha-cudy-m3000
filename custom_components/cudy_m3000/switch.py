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
"""Interruttori dei LED dei nodi mesh Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CudyConfigEntry
from .api import CudyError
from .coordinator import CudyM3000Coordinator
from .entity import CudyNodeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CudyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea uno switch LED per ogni nodo che lo espone."""
    coordinator = entry.runtime_data
    async_add_entities(
        CudyLedSwitch(coordinator, node_id)
        for node_id in coordinator.data.nodes
        if node_id in coordinator.data.led
    )


class CudyLedSwitch(CudyNodeEntity, SwitchEntity):
    """Accende o spegne il LED di stato di un nodo."""

    _attr_translation_key = "led"
    _attr_icon = "mdi:led-on"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: CudyM3000Coordinator, node_id: str) -> None:
        super().__init__(coordinator, node_id)
        self._attr_unique_id = f"{coordinator.data.nodes[node_id].unique_key}_led"

    @property
    def is_on(self) -> bool | None:
        """Stato corrente del LED."""
        entry = self.coordinator.data.led.get(self._node_id)
        if entry is not None:
            return bool(entry.get("on"))
        node = self.node
        return None if node is None else node.led_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Accende il LED."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Spegne il LED."""
        await self._async_set(False)

    async def _async_set(self, on: bool) -> None:
        """Applica lo stato richiesto e riallinea i dati."""
        try:
            await self.coordinator.admin.async_set_led(self._node_id, on)
        except CudyError as err:
            raise HomeAssistantError(f"LED non commutabile: {err}") from err
        # Immediato, non debounced: altrimenti l'entità resta sullo stato vecchio.
        await self.coordinator.async_refresh()
