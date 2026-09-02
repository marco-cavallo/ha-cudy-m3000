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
"""Diagnostica scaricabile per una istanza dell'integrazione.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import CudyConfigEntry

# Oltre alla password, i dati dei client identificano dispositivi di casa:
# vanno oscurati prima che il file finisca in un ticket.
TO_REDACT = {CONF_PASSWORD, "mac", "ip", "hostname", "serial", "sn"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CudyConfigEntry
) -> dict[str, Any]:
    """Raccoglie stato e configurazione per la segnalazione di problemi."""
    coordinator = entry.runtime_data
    data = coordinator.data

    return async_redact_data(
        {
            "entry": {
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            "router": {
                "host": coordinator.client.host,
                "language": coordinator.client.language,
                "last_update_success": coordinator.last_update_success,
                "uptime_seconds": data.uptime,
            },
            "totals": {
                "nodes": len(data.nodes),
                "nodes_online": data.online_nodes,
                "clients": data.total_clients,
            },
            "nodes": [
                {
                    "id": node.node_id,
                    "name": node.name,
                    "is_root": node.is_root,
                    "state": node.state,
                    "model": node.model,
                    "hardware": node.hardware,
                    "firmware": node.firmware,
                    "serial": node.serial,
                    "mac": node.mac,
                    "ip": node.ip,
                    "backhaul": node.backhaul,
                    "hop": node.hop,
                    "clients": node.clients,
                    "cpu_load": node.cpu_load,
                    "memory_load": node.memory_load,
                    "radios": node.radios,
                }
                for node in data.nodes.values()
            ],
            "clients": data.clients,
            "led": data.led,
            "status": data.status,
        },
        TO_REDACT,
    )
