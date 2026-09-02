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
"""Comandi WebSocket che alimentano il pannello Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .admin import DIAGNOSTIC_TOOLS
from .api import CudyAuthError, CudyError
from .const import AUTHOR, DOMAIN, INTEGRATION_NAME, VERSION
from .coordinator import CudyM3000Coordinator, MeshNode

_LOGGER = logging.getLogger(__name__)

WS_OVERVIEW = f"{DOMAIN}/overview"
WS_PAGES = f"{DOMAIN}/pages"
WS_PAGE = f"{DOMAIN}/page"
WS_SAVE = f"{DOMAIN}/save"
WS_CLIENTS = f"{DOMAIN}/clients"
WS_NODE_ACTION = f"{DOMAIN}/node_action"
WS_REFRESH = f"{DOMAIN}/refresh"
WS_DIAGNOSTIC = f"{DOMAIN}/diagnostic"
WS_SYSLOG = f"{DOMAIN}/syslog"


def _coordinator(hass: HomeAssistant) -> CudyM3000Coordinator | None:
    """Il coordinator della prima istanza caricata."""
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is not None:
            return coordinator
    return None


def _node_dict(node: MeshNode, coordinator: CudyM3000Coordinator) -> dict[str, Any]:
    """Rappresentazione di un nodo per il pannello."""
    led = coordinator.data.led.get(node.node_id, {})
    return {
        "id": node.node_id,
        "key": node.unique_key,
        "name": node.name,
        "is_root": node.is_root,
        "state": node.state,
        "online": node.state == "connected",
        "ip": node.ip,
        "mac": node.mac,
        "serial": node.serial,
        "model": node.model,
        "hardware": node.hardware,
        "firmware": node.firmware,
        "backhaul": node.backhaul,
        "parent_mac": node.parent_mac,
        "hop": node.hop,
        "uplink_iface": node.uplink_iface,
        "clients": node.clients,
        "cpu_load": node.cpu_load,
        "memory_load": node.memory_load,
        "led_on": led.get("on", node.led_on),
        "radios": {
            key: {
                "channel": value.get("channel"),
                "bandwidth": value.get("htbw"),
                "mode": value.get("mode"),
                "txpower": value.get("txpower"),
                "country": value.get("country"),
                "disabled": value.get("disabled") == "1",
                "statistics": value.get("statistics", {}),
            }
            for key, value in node.radios.items()
        },
    }


@callback
def async_register(hass: HomeAssistant) -> None:
    """Registra i comandi WebSocket del pannello."""
    for command in (
        ws_overview, ws_pages, ws_page, ws_save, ws_clients,
        ws_node_action, ws_refresh, ws_diagnostic, ws_syslog,
    ):
        websocket_api.async_register_command(hass, command)


def _require(hass: HomeAssistant, connection, msg) -> CudyM3000Coordinator | None:
    """Recupera il coordinator o segnala l'errore al chiamante."""
    coordinator = _coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_loaded", "Integrazione non caricata")
        return None
    return coordinator


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_OVERVIEW})
@callback
def ws_overview(hass, connection, msg) -> None:
    """Stato completo del mesh: nodi, client e totali."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return

    data = coordinator.data
    root = data.root
    connection.send_result(
        msg["id"],
        {
            "integration": {
                "name": INTEGRATION_NAME,
                "version": VERSION,
                "author": AUTHOR,
                "domain": DOMAIN,
                "host": coordinator.client.host,
                "language": coordinator.client.language,
            },
            "system": {
                "model": root.model if root else None,
                "hardware": root.hardware if root else None,
                "firmware": root.firmware if root else None,
                "serial": root.serial if root else None,
                "ip": root.ip if root else None,
            },
            "totals": {
                "nodes": len(data.nodes),
                "nodes_online": data.online_nodes,
                "clients": data.total_clients,
                "clients_wireless": data.wireless_clients,
            },
            "status": list(data.status.values()),
            "uptime": data.uptime,
            "nodes": [_node_dict(n, coordinator) for n in data.nodes.values()],
            "clients": data.clients,
            "last_update_success": coordinator.last_update_success,
        },
    )


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_PAGES})
@websocket_api.async_response
async def ws_pages(hass, connection, msg) -> None:
    """Elenco delle pagine di configurazione disponibili."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return
    try:
        pages = await coordinator.async_admin_pages()
    except CudyError as err:
        connection.send_error(msg["id"], "router_error", str(err))
        return
    connection.send_result(msg["id"], {"pages": pages})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): WS_PAGE, vol.Required("key"): str}
)
@websocket_api.async_response
async def ws_page(hass, connection, msg) -> None:
    """Schema di una pagina di configurazione."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return
    try:
        connection.send_result(
            msg["id"], await coordinator.admin.async_get_page(msg["key"])
        )
    except CudyAuthError as err:
        connection.send_error(msg["id"], "auth_error", str(err))
    except CudyError as err:
        connection.send_error(msg["id"], "router_error", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_SAVE,
        vol.Required("key"): str,
        vol.Required("changes"): dict,
    }
)
@websocket_api.async_response
async def ws_save(hass, connection, msg) -> None:
    """Salva le modifiche a una pagina di configurazione."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return
    try:
        ok, _body = await coordinator.admin.async_save_page(msg["key"], msg["changes"])
    except CudyError as err:
        connection.send_error(msg["id"], "router_error", str(err))
        return
    # Refresh immediato: async_request_refresh è debounced e restituirebbe
    # ancora lo stato precedente, facendo sembrare l'azione senza effetto.
    await coordinator.async_refresh()
    connection.send_result(msg["id"], {"ok": ok})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): WS_CLIENTS, vol.Optional("node_id"): str}
)
@callback
def ws_clients(hass, connection, msg) -> None:
    """Client connessi, opzionalmente filtrati per nodo."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return
    node_id = msg.get("node_id")
    clients = (
        coordinator.data.clients_of(node_id) if node_id else coordinator.data.clients
    )
    connection.send_result(msg["id"], {"clients": clients})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_NODE_ACTION,
        vol.Required("node_id"): str,
        vol.Required("action"): vol.In(
            ["led_on", "led_off", "reboot", "reset", "rename"]
        ),
        vol.Optional("name"): str,
    }
)
@websocket_api.async_response
async def ws_node_action(hass, connection, msg) -> None:
    """Esegue un'azione su un nodo mesh."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return

    node_id, action = msg["node_id"], msg["action"]
    try:
        if action in ("led_on", "led_off"):
            ok = await coordinator.admin.async_set_led(node_id, action == "led_on")
        elif action == "rename":
            name = msg.get("name", "").strip()
            if not name:
                connection.send_error(msg["id"], "bad_request", "Nome mancante")
                return
            await coordinator.admin.async_rename_node(node_id, name)
            ok = True
        else:
            await coordinator.admin.async_node_action(node_id, action)
            ok = True
    except CudyError as err:
        connection.send_error(msg["id"], "router_error", str(err))
        return

    # Refresh immediato: async_request_refresh è debounced e restituirebbe
    # ancora lo stato precedente, facendo sembrare l'azione senza effetto.
    await coordinator.async_refresh()
    connection.send_result(msg["id"], {"ok": ok})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_REFRESH})
@websocket_api.async_response
async def ws_refresh(hass, connection, msg) -> None:
    """Forza un aggiornamento immediato dei dati."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return
    await coordinator.async_refresh()
    connection.send_result(msg["id"], {"ok": coordinator.last_update_success})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_DIAGNOSTIC,
        vol.Required("tool"): vol.In(list(DIAGNOSTIC_TOOLS)),
        vol.Required("target"): str,
    }
)
@websocket_api.async_response
async def ws_diagnostic(hass, connection, msg) -> None:
    """Esegue uno strumento diagnostico sul router."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return
    try:
        output = await coordinator.admin.async_run_diagnostic(
            msg["tool"], msg["target"]
        )
    except CudyError as err:
        connection.send_error(msg["id"], "router_error", str(err))
        return
    connection.send_result(msg["id"], {"output": output})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_SYSLOG,
        vol.Optional("lines", default=300): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=2000)
        ),
    }
)
@websocket_api.async_response
async def ws_syslog(hass, connection, msg) -> None:
    """Ultime righe del log di sistema del router."""
    coordinator = _require(hass, connection, msg)
    if coordinator is None:
        return
    try:
        output = await coordinator.admin.async_get_syslog(msg["lines"])
    except CudyError as err:
        connection.send_error(msg["id"], "router_error", str(err))
        return
    connection.send_result(msg["id"], {"output": output})
