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
"""Sensori binari per i nodi mesh Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CudyConfigEntry
from .coordinator import CudyM3000Coordinator
from .entity import CudyNodeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CudyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea un sensore di connettività per ogni nodo."""
    coordinator = entry.runtime_data
    async_add_entities(
        CudyNodeOnline(coordinator, node_id) for node_id in coordinator.data.nodes
    )


class CudyNodeOnline(CudyNodeEntity, BinarySensorEntity):
    """Indica se un nodo mesh è raggiungibile."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "node_online"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CudyM3000Coordinator, node_id: str) -> None:
        super().__init__(coordinator, node_id)
        self._attr_unique_id = f"{coordinator.data.nodes[node_id].unique_key}_online"

    @property
    def is_on(self) -> bool:
        """True quando il nodo è connesso al mesh."""
        node = self.node
        return node is not None and node.state == "connected"

    @property
    def available(self) -> bool:
        """Resta disponibile anche se il nodo sparisce, per segnalare l'offline."""
        return self.coordinator.last_update_success
