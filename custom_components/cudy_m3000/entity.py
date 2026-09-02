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
"""Classi base per le entità Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import CudyM3000Coordinator, MeshNode


class CudyNodeEntity(CoordinatorEntity[CudyM3000Coordinator]):
    """Entità agganciata a un singolo nodo mesh."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CudyM3000Coordinator, node_id: str) -> None:
        super().__init__(coordinator)
        self._node_id = node_id

    @property
    def node(self) -> MeshNode | None:
        """Il nodo di questa entità nell'ultimo aggiornamento."""
        return self.coordinator.data.nodes.get(self._node_id)

    @property
    def available(self) -> bool:
        """L'entità è disponibile finché il nodo compare nella topologia."""
        return super().available and self.node is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Descrive il nodo come device separato in Home Assistant."""
        node = self.node
        if node is None:
            return DeviceInfo(identifiers={(DOMAIN, self._node_id)})

        info = DeviceInfo(
            identifiers={(DOMAIN, node.unique_key)},
            manufacturer=MANUFACTURER,
            name=node.name,
            model=node.model,
            hw_version=node.hardware,
            sw_version=node.firmware,
            serial_number=node.serial,
        )
        if node.mac:
            info["connections"] = {(CONNECTION_NETWORK_MAC, node.mac)}
        if node.ip:
            info["configuration_url"] = f"http://{node.ip}/"

        # I satelliti vengono mostrati come figli del nodo principale.
        if not node.is_root and node.parent_mac:
            info["via_device"] = (DOMAIN, node.parent_mac.replace(":", "").upper())

        return info
