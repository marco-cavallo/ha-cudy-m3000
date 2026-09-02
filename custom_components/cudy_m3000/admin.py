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
"""Superficie di amministrazione del router, esposta al pannello.

Cudy M3000 - By Marco Cavallo.

Raccoglie in un unico posto: il registro delle pagine di configurazione, il
parser dell'elenco client per nodo e le azioni per nodo (LED, riavvio, reset,
rinomina). Le pagine sono descritte in modo dichiarativo perché tutte passano
dallo stesso motore CBI: aggiungerne una è una riga, non codice nuovo.
"""

from __future__ import annotations

import html as html_mod
import logging
import re
from dataclasses import dataclass
from typing import Any

from .api import CudyClient, CudyError
from .cbi import parse_form
from .status import STATUS_PANELS, parse_status_panel

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AdminPage:
    """Una pagina di configurazione raggiungibile dal pannello."""

    key: str
    path: str
    section: str
    icon: str
    # Alcune pagine esistono solo in certe modalità operative del router.
    optional: bool = False


# Sezioni usate per raggruppare le pagine nella UI del pannello.
SECTION_NETWORK = "network"
SECTION_WIRELESS = "wireless"
SECTION_SYSTEM = "system"
SECTION_SECURITY = "security"

ADMIN_PAGES: tuple[AdminPage, ...] = (
    # Rete
    AdminPage("lan", "/admin/network/lan/config", SECTION_NETWORK, "mdi:lan"),
    AdminPage("wan", "/admin/network/wan/config/detail", SECTION_NETWORK, "mdi:wan", True),
    AdminPage("igmp", "/admin/network/igmp", SECTION_NETWORK, "mdi:multicast", True),
    AdminPage("iptv", "/admin/network/iptv", SECTION_NETWORK, "mdi:television", True),
    AdminPage("wol", "/admin/network/wol", SECTION_NETWORK, "mdi:power-plug", True),
    AdminPage("captive_portal", "/admin/services/coovachilli", SECTION_NETWORK, "mdi:wifi-lock", True),
    # Wireless
    AdminPage("wifi", "/admin/network/wireless/config/uncombine", SECTION_WIRELESS, "mdi:wifi"),
    AdminPage("wifi_schedule", "/admin/network/wifi_schedule", SECTION_WIRELESS, "mdi:calendar-clock", True),
    AdminPage("wps", "/admin/network/wireless/wsc", SECTION_WIRELESS, "mdi:wifi-plus", True),
    # Sicurezza / accesso
    AdminPage("administration", "/admin/system/administration", SECTION_SECURITY, "mdi:shield-account", True),
    AdminPage("password", "/admin/system/password", SECTION_SECURITY, "mdi:key-variant"),
    # Sistema
    AdminPage("systime", "/admin/system/systime", SECTION_SYSTEM, "mdi:clock-outline"),
    AdminPage("timezone", "/admin/system/timezone", SECTION_SYSTEM, "mdi:earth", True),
    AdminPage("language", "/admin/system/language", SECTION_SYSTEM, "mdi:translate"),
    AdminPage("leds", "/admin/system/leds", SECTION_SYSTEM, "mdi:led-on"),
    AdminPage("autoreboot", "/admin/system/autoreboot", SECTION_SYSTEM, "mdi:restart-alert", True),
    AdminPage("autoupgrade", "/admin/system/autoupgrade", SECTION_SYSTEM, "mdi:update", True),
    AdminPage("workmode", "/admin/system/workmode", SECTION_SYSTEM, "mdi:swap-horizontal", True),
)

PAGES_BY_KEY: dict[str, AdminPage] = {page.key: page for page in ADMIN_PAGES}

# Endpoint delle azioni per nodo mesh: tutte vogliono ?client=<id>.
NODE_PAGE_MANAGEMENT = "/admin/network/mesh/management"
NODE_PAGE_RENAME = "/admin/network/mesh/devinfo"
NODE_PAGE_UPGRADE = "/admin/network/mesh/upgrade"
NODE_PAGE_REBOOT = "/admin/network/mesh/reboot"
NODE_PAGE_RESET = "/admin/network/mesh/reset"
NODE_PAGE_LEDS = "/admin/network/mesh/leds"
NODE_LED_CTL = "/admin/network/mesh/ledctl"

PATH_LEDS = "/admin/system/leds"
PATH_CLIENT_DEVLIST = "/admin/network/mesh/client/devlist"
PATH_CLIENT_DEVSTATUS = "/admin/network/mesh/client/devstatus"
PATH_SYSTEM_REBOOT = "/admin/system/reboot/reboot"
PATH_SYSLOG = "/admin/system/status/syslog"

# Strumenti diagnostici: stesso schema, ma il campo di input cambia nome fra
# uno e l'altro (`addr` per ping, `hostname` per nslookup), quindi si ricava
# dalla pagina invece di essere codificato qui.
DIAGNOSTIC_TOOLS: tuple[str, ...] = ("ping", "traceroute", "nslookup")

# L'output finisce in una textarea che il firmware chiama `_custom` negli
# strumenti diagnostici e `_download` nel log di sistema.
_RE_CUSTOM = re.compile(
    r'name="(?P<name>cbid\.\w+\.\d+\._(?:custom|download))"[^>]*>(?P<body>.*?)</textarea>',
    re.S | re.I,
)
_RE_REFRESH = re.compile(
    r'name="(?P<name>cbid\.\w+\.\d+\.refresh)"[^>]*value="(?P<value>[^"]*)"', re.I
)
_RE_INPUT_FIELD = re.compile(
    r'<input[^>]*type="text"[^>]*name="(?P<name>cbid\.\w+\.\d+\.(?!_custom)\w+)"', re.I
)

# Il router traduce l'hostname ignoto nella lingua richiesta: serve
# riconoscerlo per non usarlo come nome di un'entità.
UNKNOWN_HOSTNAMES: frozenset[str] = frozenset({
    "unknown", "sconosciuto", "unbekannt", "inconnu", "desconocido",
    "desconhecido", "onbekend", "nieznany", "neznámý", "neznámy", "okänd",
    "ukjent", "ukendt", "ismeretlen", "bilinmeyen", "necunoscut",
    "άγνωστο", "неизвестно", "невідомо", "непознат", "不明", "未知",
    "알 수 없음", "ไม่ทราบ", "không xác định", "غير معروف", "לא ידוע",
    "nepoznato", "nieznane", "-", "",
})


_RE_ROW = re.compile(r'<tr\b[^>]*id="cbi-[^"]*"[^>]*>(?P<body>.*?)</tr>', re.S | re.I)
_RE_CELL = re.compile(
    r'<div id="cbi-[^"-]+-\d+-(?P<col>[a-z]+)"[^>]*>(?P<body>.*?)<div id="cbip-',
    re.S | re.I,
)
_RE_STATIC_P = re.compile(
    r'<p class="form-control-static[^"]*"[^>]*>(?P<body>.*?)</p>', re.S | re.I
)
_RE_RATE = re.compile(r"([\d.]+)\s*([KMG]?bps)", re.I)


def _lines(fragment: str) -> list[str]:
    """Righe di testo di una cella, separate dai <br>."""
    parts = re.split(r"<br\s*/?>", fragment, flags=re.I)
    out = []
    for part in parts:
        text = html_mod.unescape(re.sub(r"<[^>]+>", "", part))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            out.append(text)
    return out


def _to_kbps(text: str) -> float | None:
    """Converte '0.64 Kbps' in kbps numerici."""
    match = _RE_RATE.search(text)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit.startswith("m"):
        return value * 1000
    if unit.startswith("g"):
        return value * 1_000_000
    if unit == "bps":
        return value / 1000
    return value


def _cell_lines(cells: dict[str, str], column: str) -> list[str]:
    """Righe di testo della colonna richiesta, vuote se la colonna manca."""
    match = _RE_STATIC_P.search(cells.get(column, ""))
    return _lines(match.group("body")) if match else []


def _band(link: str) -> str | None:
    """Banda radio ricavata dalla descrizione della connessione."""
    upper = link.upper()
    if "2.4" in upper:
        return "2.4G"
    if "5G" in upper:
        return "5G"
    return None


def parse_clients(raw_html: str, node_id: str) -> list[dict[str, Any]]:
    """Estrae i client connessi a un nodo dalla sua pagina devlist."""
    clients: list[dict[str, Any]] = []

    for row in _RE_ROW.finditer(raw_html):
        cells: dict[str, str] = {
            cell.group("col"): cell.group("body")
            for cell in _RE_CELL.finditer(row.group("body"))
        }
        if "ipmac" not in cells:
            continue

        host_lines = _cell_lines(cells, "hostname")
        ipmac_lines = _cell_lines(cells, "ipmac")
        speed_lines = _cell_lines(cells, "speed")
        online_lines = _cell_lines(cells, "online")

        link = host_lines[1] if len(host_lines) > 1 else ""
        mac = ipmac_lines[1] if len(ipmac_lines) > 1 else ""
        hostname = host_lines[0] if host_lines else ""

        clients.append(
            {
                "node_id": node_id,
                "hostname": hostname or "?",
                "named": hostname.strip().lower() not in UNKNOWN_HOSTNAMES,
                "connection": link,
                "band": _band(link),
                "wired": "wired" in link.lower() or "lan" in link.lower(),
                "ip": ipmac_lines[0] if ipmac_lines else "",
                "mac": mac.upper(),
                "tx_kbps": _to_kbps(speed_lines[0]) if speed_lines else None,
                "rx_kbps": _to_kbps(speed_lines[1]) if len(speed_lines) > 1 else None,
                "duration": online_lines[0] if online_lines else "",
            }
        )

    return clients


class CudyAdmin:
    """Operazioni di amministrazione sopra il client HTTP."""

    def __init__(self, client: CudyClient) -> None:
        self._client = client

    async def async_available_pages(self) -> list[dict[str, Any]]:
        """Pagine effettivamente disponibili su questo router.

        Le pagine marcate opzionali dipendono dalla modalità operativa, quindi
        vanno sondate: in modalità access point, per esempio, la WAN non c'è.
        """
        available: list[dict[str, Any]] = []
        for page in ADMIN_PAGES:
            try:
                html = await self._client.async_get_html(page.path)
            except CudyError:
                if page.optional:
                    continue
                available.append(_page_dict(page, page.key, page.key))
                continue

            # Una pagina assente in questa modalità operativa non ha form.
            if page.optional and ("<form" not in html or len(html) < 400):
                continue

            form = parse_form(html, page.path)
            available.append(_page_dict(page, page.key, form.title or page.key))
        return available

    async def async_get_page(self, key: str) -> dict[str, Any]:
        """Schema di una pagina di configurazione."""
        page = PAGES_BY_KEY.get(key)
        if page is None:
            raise CudyError(f"Pagina sconosciuta: {key}")
        form = await self._client.async_get_form(page.path)
        payload = form.as_dict()
        payload["key"] = key
        payload["icon"] = page.icon
        payload["section"] = page.section
        return payload

    async def async_save_page(
        self, key: str, changes: dict[str, Any]
    ) -> tuple[bool, str]:
        """Salva le modifiche a una pagina di configurazione."""
        page = PAGES_BY_KEY.get(key)
        if page is None:
            raise CudyError(f"Pagina sconosciuta: {key}")
        return await self._client.async_submit_form(page.path, changes)

    async def async_run_diagnostic(self, tool: str, target: str) -> str:
        """Esegue ping, traceroute o nslookup sul router e ne ritorna l'output."""
        if tool not in DIAGNOSTIC_TOOLS:
            raise CudyError(f"Strumento diagnostico sconosciuto: {tool}")
        if not target.strip():
            raise CudyError("Destinazione mancante")

        path = f"/admin/network/{tool}"
        page = await self._client.async_get_html(path)

        field = _RE_INPUT_FIELD.search(page)
        button = _RE_REFRESH.search(page)
        token_match = re.search(r'name="token"[^>]*value="([^"]*)"', page)
        if field is None or button is None or token_match is None:
            raise CudyError(f"Pagina {tool} non riconosciuta")

        response = await self._client.async_post_action(
            path,
            {
                field.group("name"): target.strip(),
                button.group("name"): button.group("value"),
            },
            token=token_match.group(1),
        )
        output = _RE_CUSTOM.search(response)
        return html_mod.unescape(output.group("body")).strip() if output else ""

    async def async_get_syslog(self, lines: int = 300) -> str:
        """Ultime righe del log di sistema del router."""
        page = await self._client.async_get_html(PATH_SYSLOG)
        match = _RE_CUSTOM.search(page)
        if match is None:
            return ""
        text = html_mod.unescape(match.group("body")).strip()
        rows = text.splitlines()
        return "\n".join(rows[-lines:])

    async def async_get_status(self) -> dict[str, dict[str, Any]]:
        """Riquadri informativi della pagina di stato, per chiave."""
        panels: dict[str, dict[str, Any]] = {}
        for panel in STATUS_PANELS:
            try:
                html = await self._client.async_get_html(panel.path)
            except CudyError as err:
                _LOGGER.debug("Riquadro %s non leggibile: %s", panel.key, err)
                continue
            parsed = parse_status_panel(html, panel.key)
            parsed["icon"] = panel.icon
            panels[panel.key] = parsed
        return panels

    async def async_get_clients(self, node_id: str) -> list[dict[str, Any]]:
        """Client connessi a un singolo nodo mesh."""
        html = await self._client.async_get_html(
            f"{PATH_CLIENT_DEVLIST}?embedded=&client={node_id}"
        )
        return parse_clients(html, node_id)

    async def async_led_map(self) -> dict[str, dict[str, Any]]:
        """Mappa nodo -> stato LED e nome del campo che lo comanda."""
        mapping, _token = await self.async_led_state()
        return mapping

    async def async_led_state(self) -> tuple[dict[str, dict[str, Any]], str]:
        """Stato dei LED più il token della pagina, necessario per comandarli."""
        form = await self._client.async_get_form(PATH_LEDS)
        mapping: dict[str, dict[str, Any]] = {}
        for table in form.tables:
            for row in table.rows:
                cell = row["cells"].get("ledstatus")
                if not isinstance(cell, dict) or not cell.get("action_url"):
                    continue
                node_id = cell["action_url"].rsplit("/", 1)[-1]
                mapping[node_id] = {
                    "field": cell["name"],
                    "on": bool(cell["value"]),
                    "action_url": cell["action_url"],
                    "device": (row["cells"].get("device") or {}).get("value", ""),
                }
        return mapping, form.token

    async def async_set_led(self, node_id: str, on: bool) -> bool:
        """Accende o spegne il LED di un nodo."""
        mapping, token = await self.async_led_state()
        entry = mapping.get(node_id)
        if entry is None:
            raise CudyError(f"Nessun LED per il nodo {node_id}")
        if entry["on"] == on:
            return True

        field = entry["field"]
        response = await self._client.async_post_action(
            entry["action_url"],
            {
                "cbi.toggle": "1",
                f"cbi.cbe.{field.removeprefix('cbid.')}": "1",
                field: "1" if on else "0",
            },
            token=token,
        )
        return response.strip().upper().startswith("OK")

    async def async_toggle_field(self, key: str, field: str, on: bool) -> bool:
        """Commuta un interruttore che agisce con un POST immediato.

        Alcuni toggle delle pagine di configurazione non passano dal salvataggio
        del form: il firmware li invia subito al proprio endpoint, indicato
        nell'attributo action_url del campo. È il caso del controllo LED, dove
        ogni riga scrive sul nodo corrispondente.
        """
        page = PAGES_BY_KEY.get(key)
        if page is None:
            raise CudyError(f"Pagina sconosciuta: {key}")

        form = await self._client.async_get_form(page.path)
        target = None
        for table in form.tables:
            for row in table.rows:
                for cell in row["cells"].values():
                    if isinstance(cell, dict) and cell.get("name") == field:
                        target = cell
        if target is None:
            raise CudyError(f"Campo {field} non trovato in {key}")
        if not target.get("action_url"):
            raise CudyError(f"Il campo {field} non ha un'azione immediata")
        if bool(target.get("value")) == on:
            return True

        response = await self._client.async_post_action(
            target["action_url"],
            {
                "cbi.toggle": "1",
                f"cbi.cbe.{field.removeprefix('cbid.')}": "1",
                field: "1" if on else "0",
            },
            token=form.token,
        )
        return response.strip().upper().startswith("OK")

    async def async_node_action(self, node_id: str, action: str) -> str:
        """Esegue riavvio o reset su un nodo mesh."""
        paths = {"reboot": NODE_PAGE_REBOOT, "reset": NODE_PAGE_RESET}
        path = paths.get(action)
        if path is None:
            raise CudyError(f"Azione nodo sconosciuta: {action}")
        token = await self._page_token(f"{NODE_PAGE_MANAGEMENT}?client={node_id}")
        return await self._client.async_post_action(
            f"{path}?client={node_id}", {"client": node_id}, token=token
        )

    async def async_rename_node(self, node_id: str, name: str) -> str:
        """Rinomina un nodo mesh."""
        path = f"{NODE_PAGE_RENAME}?client={node_id}"
        return await self._client.async_post_action(
            path,
            {"client": node_id, "cbid.mesh.devinfo.name": name},
            token=await self._page_token(path),
        )

    async def async_reboot_router(self) -> str:
        """Riavvia il nodo principale."""
        return await self._client.async_post_action(
            PATH_SYSTEM_REBOOT, token=await self._page_token(PATH_SYSTEM_REBOOT)
        )

    async def _page_token(self, path: str) -> str:
        """Token incorporato in una pagina, l'unico che il router accetta."""
        form = await self._client.async_get_form(path)
        return form.token


def _page_dict(page: AdminPage, key: str, title: str) -> dict[str, Any]:
    """Descrittore leggero di una pagina, per l'indice del pannello.

    Il titolo arriva dal router, quindi è già nella lingua di Home Assistant.
    """
    return {
        "key": key,
        "title": title,
        "path": page.path,
        "section": page.section,
        "icon": page.icon,
    }
