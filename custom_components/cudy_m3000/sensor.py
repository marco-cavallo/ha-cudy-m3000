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
"""Sensori per il sistema mesh Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CudyConfigEntry
from .coordinator import CudyM3000Coordinator, MeshNode
from .entity import CudyNodeEntity


def _radio_channel(node: MeshNode, radio: str) -> int | None:
    """Canale in uso su una delle due radio."""
    info = node.radios.get(radio) or {}
    channel = info.get("channel")
    return channel if isinstance(channel, int) else None


@dataclass(frozen=True, kw_only=True)
class CudyNodeSensorDescription(SensorEntityDescription):
    """Descrive un sensore ricavato da un nodo mesh."""

    value_fn: Callable[[MeshNode], Any]
    attrs_fn: Callable[[MeshNode], dict[str, Any]] | None = None


NODE_SENSORS: tuple[CudyNodeSensorDescription, ...] = (
    CudyNodeSensorDescription(
        key="clients",
        translation_key="clients",
        icon="mdi:devices",
        native_unit_of_measurement="client",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda node: node.clients,
    ),
    CudyNodeSensorDescription(
        key="cpu_load",
        translation_key="cpu_load",
        icon="mdi:cpu-64-bit",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda node: node.cpu_load,
    ),
    CudyNodeSensorDescription(
        key="memory_load",
        translation_key="memory_load",
        icon="mdi:memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda node: node.memory_load,
    ),
    CudyNodeSensorDescription(
        key="state",
        translation_key="node_state",
        icon="mdi:lan-connect",
        device_class=SensorDeviceClass.ENUM,
        options=["connected", "disconnected", "connecting", "unknown"],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda node: node.state or "unknown",
    ),
    CudyNodeSensorDescription(
        key="backhaul",
        translation_key="backhaul",
        icon="mdi:transit-connection-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda node: node.backhaul,
        attrs_fn=lambda node: {
            "parent_mac": node.parent_mac,
            "hop": node.hop,
            "uplink_interface": node.uplink_iface,
            "ip_address": node.ip,
            "led": None if node.led_on is None else ("on" if node.led_on else "off"),
        },
    ),
    CudyNodeSensorDescription(
        key="channel_24",
        translation_key="channel_24",
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda node: _radio_channel(node, "radio0"),
        attrs_fn=lambda node: {
            "bandwidth": (node.radios.get("radio0") or {}).get("htbw"),
            "mode": (node.radios.get("radio0") or {}).get("mode"),
        },
    ),
    CudyNodeSensorDescription(
        key="channel_5",
        translation_key="channel_5",
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda node: _radio_channel(node, "radio1"),
        attrs_fn=lambda node: {
            "bandwidth": (node.radios.get("radio1") or {}).get("htbw"),
            "mode": (node.radios.get("radio1") or {}).get("mode"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CudyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea i sensori per ogni nodo mesh rilevato."""
    coordinator = entry.runtime_data

    entities: list[SensorEntity] = []
    for node_id in coordinator.data.nodes:
        entities.extend(
            CudyNodeSensor(coordinator, node_id, description)
            for description in NODE_SENSORS
        )

    root = coordinator.data.root
    if root is not None:
        entities.append(CudyTotalClientsSensor(coordinator, root.node_id))
        entities.append(CudyOnlineNodesSensor(coordinator, root.node_id))
        entities.append(CudyUptimeSensor(coordinator, root.node_id))
        entities.append(CudyBandClientsSensor(coordinator, root.node_id, "2.4", "clients_24g"))
        entities.append(CudyBandClientsSensor(coordinator, root.node_id, "5G", "clients_5g"))

    async_add_entities(entities)


class CudyNodeSensor(CudyNodeEntity, SensorEntity):
    """Sensore ricavato da un singolo nodo mesh."""

    entity_description: CudyNodeSensorDescription

    def __init__(
        self,
        coordinator: CudyM3000Coordinator,
        node_id: str,
        description: CudyNodeSensorDescription,
    ) -> None:
        super().__init__(coordinator, node_id)
        self.entity_description = description
        node = coordinator.data.nodes[node_id]
        self._attr_unique_id = f"{node.unique_key}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Valore corrente del sensore."""
        node = self.node
        return None if node is None else self.entity_description.value_fn(node)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Attributi aggiuntivi, se la descrizione ne prevede."""
        node = self.node
        if node is None or self.entity_description.attrs_fn is None:
            return None
        return {
            key: value
            for key, value in self.entity_description.attrs_fn(node).items()
            if value is not None
        }


class CudyTotalClientsSensor(CudyNodeEntity, SensorEntity):
    """Client totali connessi all'intero mesh."""

    _attr_translation_key = "total_clients"
    _attr_icon = "mdi:account-group"
    _attr_native_unit_of_measurement = "client"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: CudyM3000Coordinator, node_id: str) -> None:
        super().__init__(coordinator, node_id)
        self._attr_unique_id = f"{coordinator.data.nodes[node_id].unique_key}_total_clients"

    @property
    def native_value(self) -> int:
        """Somma dei client su tutti i nodi."""
        return self.coordinator.data.total_clients


class CudyOnlineNodesSensor(CudyNodeEntity, SensorEntity):
    """Numero di nodi mesh attualmente connessi."""

    _attr_translation_key = "online_nodes"
    _attr_icon = "mdi:access-point-network"
    _attr_native_unit_of_measurement = "nodi"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CudyM3000Coordinator, node_id: str) -> None:
        super().__init__(coordinator, node_id)
        self._attr_unique_id = f"{coordinator.data.nodes[node_id].unique_key}_online_nodes"

    @property
    def native_value(self) -> int:
        """Conteggio dei nodi in stato connected."""
        return self.coordinator.data.online_nodes

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Elenco dei nodi con il rispettivo stato."""
        return {
            "nodes": {
                node.name: node.state for node in self.coordinator.data.nodes.values()
            },
            "total_nodes": len(self.coordinator.data.nodes),
        }


class CudyUptimeSensor(CudyNodeEntity, SensorEntity):
    """Momento in cui il nodo principale è stato acceso."""

    _attr_translation_key = "uptime"
    _attr_icon = "mdi:clock-start"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CudyM3000Coordinator, node_id: str) -> None:
        super().__init__(coordinator, node_id)
        self._attr_unique_id = f"{coordinator.data.nodes[node_id].unique_key}_uptime"
        self._boot: datetime | None = None

    @property
    def native_value(self) -> datetime | None:
        """Istante di avvio, stabilizzato per non oscillare a ogni lettura.

        Il router riporta i secondi di attività: ricalcolare l'istante di boot
        a ogni polling lo farebbe ballare di un secondo, generando storico
        inutile. Si aggiorna solo se lo scarto supera il minuto, cioè quando il
        router è stato davvero riavviato.
        """
        seconds = self.coordinator.data.uptime
        if seconds is None:
            return self._boot

        computed = dt_util.utcnow() - timedelta(seconds=seconds)
        if self._boot is None or abs((computed - self._boot).total_seconds()) > 60:
            self._boot = computed
        return self._boot

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Uptime grezzo, comodo da mostrare così com'è."""
        seconds = self.coordinator.data.uptime
        return {} if seconds is None else {"uptime_seconds": seconds}


class CudyBandClientsSensor(CudyNodeEntity, SensorEntity):
    """Client connessi su una singola banda radio."""

    _attr_icon = "mdi:wifi"
    _attr_native_unit_of_measurement = "client"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: CudyM3000Coordinator,
        node_id: str,
        band: str,
        translation_key: str,
    ) -> None:
        super().__init__(coordinator, node_id)
        self._band = band
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"{coordinator.data.nodes[node_id].unique_key}_{translation_key}"
        )

    @property
    def native_value(self) -> int | None:
        """Conteggio riportato dal riquadro dispositivi del router."""
        return self.coordinator.data.clients_on_band(self._band)
