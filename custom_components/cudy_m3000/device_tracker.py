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
"""Tracciamento dei dispositivi connessi al mesh Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CudyConfigEntry
from .coordinator import CudyM3000Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CudyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea un tracker per client, aggiungendo i nuovi man mano che compaiono."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _sync() -> None:
        """Aggiunge i client non ancora tracciati."""
        new = [
            CudyClientTracker(coordinator, client["mac"])
            for client in coordinator.data.clients
            if client.get("mac") and client["mac"] not in known
        ]
        known.update(tracker.mac_address for tracker in new)
        if new:
            async_add_entities(new)

    _sync()
    entry.async_on_unload(coordinator.async_add_listener(_sync))


class CudyClientTracker(CoordinatorEntity[CudyM3000Coordinator], ScannerEntity):
    """Un dispositivo connesso a uno dei nodi mesh."""

    _attr_has_entity_name = False
    _attr_source_type = SourceType.ROUTER

    def __init__(self, coordinator: CudyM3000Coordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac.upper()
        self._attr_unique_id = f"client_{self._mac.replace(':', '')}"

    @property
    def _client(self) -> dict[str, Any] | None:
        """Dati correnti del client, se ancora connesso."""
        return self.coordinator.data.client_by_mac(self._mac)

    @property
    def source_type(self) -> SourceType:
        """I client sono rilevati interrogando il router."""
        return SourceType.ROUTER

    @property
    def mac_address(self) -> str:
        """Indirizzo MAC del dispositivo."""
        return self._mac

    @property
    def name(self) -> str:
        """Nome visualizzato: hostname se noto, altrimenti il MAC.

        Il router traduce l'hostname ignoto nella lingua richiesta, quindi il
        riconoscimento avviene nel parser e arriva qui come flag `named`.
        """
        client = self._client
        if client and client.get("named"):
            return client["hostname"]
        return self._mac

    @property
    def is_connected(self) -> bool:
        """True finché il client compare nell'elenco di un nodo."""
        return self._client is not None

    @property
    def ip_address(self) -> str | None:
        """Indirizzo IP corrente."""
        return (self._client or {}).get("ip")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Dettagli utili: nodo di aggancio, banda, throughput, durata."""
        client = self._client
        if client is None:
            return {}

        node = self.coordinator.data.nodes.get(client.get("node_id", ""))
        return {
            "node": node.name if node else client.get("node_id"),
            "node_id": client.get("node_id"),
            "connection": client.get("connection"),
            "band": client.get("band"),
            "wired": client.get("wired"),
            "tx_kbps": client.get("tx_kbps"),
            "rx_kbps": client.get("rx_kbps"),
            "duration": client.get("duration"),
        }
