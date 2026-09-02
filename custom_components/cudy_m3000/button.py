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
"""Pulsanti di amministrazione per i nodi mesh Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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
    """Crea un pulsante di riavvio per ogni nodo."""
    coordinator = entry.runtime_data
    async_add_entities(
        CudyRebootButton(coordinator, node_id) for node_id in coordinator.data.nodes
    )


class CudyRebootButton(CudyNodeEntity, ButtonEntity):
    """Riavvia un nodo mesh."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_translation_key = "reboot"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: CudyM3000Coordinator, node_id: str) -> None:
        super().__init__(coordinator, node_id)
        self._attr_unique_id = f"{coordinator.data.nodes[node_id].unique_key}_reboot"

    async def async_press(self) -> None:
        """Invia il comando di riavvio."""
        node = self.node
        try:
            if node is not None and node.is_root:
                await self.coordinator.admin.async_reboot_router()
            else:
                await self.coordinator.admin.async_node_action(self._node_id, "reboot")
        except CudyError as err:
            raise HomeAssistantError(f"Riavvio non riuscito: {err}") from err
