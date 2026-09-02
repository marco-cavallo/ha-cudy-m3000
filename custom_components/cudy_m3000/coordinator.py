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
"""Coordinator di polling per il sistema mesh Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .admin import CudyAdmin
from .api import CudyAuthError, CudyClient, CudyError
from .const import DOMAIN, ROOT_NODE_ID
from .status import find_row, system_uptime

_LOGGER = logging.getLogger(__name__)


def _to_int(value: Any) -> int | None:
    """Converte in int i numeri che il firmware serve come stringa."""
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class MeshNode:
    """Un nodo del sistema mesh, normalizzato dal JSON del firmware."""

    node_id: str
    name: str
    is_root: bool
    mac: str | None = None
    ip: str | None = None
    serial: str | None = None
    model: str | None = None
    hardware: str | None = None
    firmware: str | None = None
    state: str | None = None
    backhaul: str | None = None
    led_on: bool | None = None
    clients: int | None = None
    cpu_load: int | None = None
    memory_load: int | None = None
    parent_mac: str | None = None
    hop: int | None = None
    uplink_iface: str | None = None
    radios: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def unique_key(self) -> str:
        """Chiave stabile per unique_id ed identificatori di device."""
        return (self.mac or self.node_id).replace(":", "").upper()


def _parse_node(raw: dict[str, Any]) -> MeshNode:
    """Normalizza un elemento di /admin/network/mesh/clients."""
    sysreport: dict[str, Any] = raw.get("sysreport") or {}
    sysstat: dict[str, Any] = raw.get("sysstatinfo") or {}
    parent: dict[str, Any] = sysreport.get("parent") or {}

    node_id = str(raw.get("id") or "")
    is_root = node_id == ROOT_NODE_ID

    radios = {
        key: value
        for key, value in sysstat.items()
        if key.startswith("radio") and isinstance(value, dict)
    }

    return MeshNode(
        node_id=node_id,
        name=str(raw.get("name") or node_id),
        is_root=is_root,
        mac=sysreport.get("macaddr"),
        ip=sysreport.get("ipaddr"),
        serial=sysreport.get("sn"),
        model=sysreport.get("board"),
        hardware=sysreport.get("hardware"),
        firmware=sysreport.get("firmware"),
        # Il nodo principale non riporta uno stato: se risponde, è connesso.
        state="connected" if is_root else raw.get("state"),
        backhaul=sysreport.get("meshtype"),
        led_on=None if sysreport.get("ledstatus") is None
        else sysreport.get("ledstatus") == "on",
        clients=_to_int(raw.get("devcnt")),
        cpu_load=_to_int(sysstat.get("cpuload")),
        memory_load=_to_int(sysstat.get("memload")),
        parent_mac=None if is_root else parent.get("macaddr"),
        hop=_to_int(parent.get("hop")),
        uplink_iface=parent.get("iface"),
        radios=radios,
    )


@dataclass(slots=True)
class MeshData:
    """Fotografia dell'intero sistema mesh a un dato istante."""

    nodes: dict[str, MeshNode]
    clients: list[dict[str, Any]] = field(default_factory=list)
    led: dict[str, dict[str, Any]] = field(default_factory=dict)
    status: dict[str, dict[str, Any]] = field(default_factory=dict)

    def clients_of(self, node_id: str) -> list[dict[str, Any]]:
        """Client agganciati a un nodo specifico."""
        return [c for c in self.clients if c.get("node_id") == node_id]

    def client_by_mac(self, mac: str) -> dict[str, Any] | None:
        """Cerca un client per indirizzo MAC."""
        target = mac.upper()
        return next((c for c in self.clients if c.get("mac") == target), None)

    @property
    def root(self) -> MeshNode | None:
        """Nodo principale (controller)."""
        return next((n for n in self.nodes.values() if n.is_root), None)

    @property
    def total_clients(self) -> int:
        """Somma dei client connessi su tutti i nodi."""
        return sum(n.clients or 0 for n in self.nodes.values())

    @property
    def uptime(self) -> int | None:
        """Uptime del nodo principale, in secondi."""
        return system_uptime(self.status.get("system", {}))

    def clients_on_band(self, band: str) -> int | None:
        """Numero di client su una banda, letto dal riquadro dispositivi."""
        value = find_row(self.status.get("devices", {}), band)
        try:
            return int(value) if value is not None else None
        except ValueError:
            return None

    @property
    def wireless_clients(self) -> int:
        """Client connessi via Wi-Fi."""
        return sum(1 for c in self.clients if not c.get("wired"))

    @property
    def online_nodes(self) -> int:
        """Numero di nodi in stato `connected`."""
        return sum(1 for n in self.nodes.values() if n.state == "connected")


class CudyM3000Coordinator(DataUpdateCoordinator[MeshData]):
    """Interroga il nodo principale e distribuisce i dati alle entità."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: CudyClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({client.host})",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.client = client
        self.admin = CudyAdmin(client)
        # L'elenco pagine dipende dalla modalità operativa e non cambia a
        # runtime: si sonda una volta sola, alla prima richiesta del pannello.
        self._pages_cache: list[dict[str, Any]] | None = None

    async def async_admin_pages(self) -> list[dict[str, Any]]:
        """Pagine di configurazione disponibili, sondate una volta sola."""
        if self._pages_cache is None:
            self._pages_cache = await self.admin.async_available_pages()
        return self._pages_cache

    async def _async_update_data(self) -> MeshData:
        """Scarica e normalizza lo stato del mesh."""
        try:
            raw_nodes = await self.client.async_get_mesh_nodes()
        except CudyAuthError as err:
            # Fa partire il flusso di riautenticazione nella UI.
            raise ConfigEntryAuthFailed(str(err)) from err
        except CudyError as err:
            raise UpdateFailed(str(err)) from err

        nodes: dict[str, MeshNode] = {}
        for raw in raw_nodes:
            if not isinstance(raw, dict):
                continue
            node = _parse_node(raw)
            if node.node_id:
                nodes[node.node_id] = node

        if not nodes:
            raise UpdateFailed("Il router non ha restituito alcun nodo mesh")

        clients: list[dict[str, Any]] = []
        for node_id, node in nodes.items():
            if not node.clients:
                continue
            try:
                clients.extend(await self.admin.async_get_clients(node_id))
            except CudyError as err:
                # Un nodo che non risponde non deve far fallire l'intero ciclo.
                _LOGGER.debug("Client non leggibili per %s: %s", node.name, err)

        try:
            led = await self.admin.async_led_map()
        except CudyError as err:
            _LOGGER.debug("Stato LED non leggibile: %s", err)
            led = {}

        try:
            status = await self.admin.async_get_status()
        except CudyError as err:
            _LOGGER.debug("Riquadri di stato non leggibili: %s", err)
            status = {}

        _LOGGER.debug(
            "Aggiornati %d nodi, %d client", len(nodes), len(clients)
        )
        return MeshData(nodes=nodes, clients=clients, led=led, status=status)
