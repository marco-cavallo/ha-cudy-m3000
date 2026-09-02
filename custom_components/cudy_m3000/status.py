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
"""Pannelli informativi della pagina di stato del router.

Cudy M3000 - By Marco Cavallo.

La home del firmware è composta da riquadri caricati singolarmente, ognuno con
la stessa struttura: un titolo, una riga di intestazione con il dato principale
e un elenco di coppie etichetta/valore. Un solo parser li copre tutti.
"""

from __future__ import annotations

import html as html_mod
import logging
import re
from dataclasses import dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StatusPanel:
    """Un riquadro informativo della pagina di stato."""

    key: str
    path: str
    icon: str


# `/admin/network/bandwidth` esiste ma il firmware 2.5.28 va in errore 500
# nel rendere il suo template, quindi non lo interroghiamo.
STATUS_PANELS: tuple[StatusPanel, ...] = (
    StatusPanel("system", "/admin/system/status", "mdi:chip"),
    StatusPanel("mesh", "/admin/network/mesh/status", "mdi:access-point-network"),
    StatusPanel("devices", "/admin/network/devices/status", "mdi:devices"),
    StatusPanel("wireless", "/admin/network/wireless/status", "mdi:wifi"),
    StatusPanel("lan", "/admin/network/lan/status", "mdi:lan"),
)

_RE_TITLE = re.compile(r'<h3 class="panel-title"[^>]*>(?P<t>.*?)</h3>', re.S | re.I)
_RE_HEAD = re.compile(r"<thead>(?P<b>.*?)</thead>", re.S | re.I)
_RE_TH = re.compile(r"<th[^>]*>(?P<t>.*?)</th>", re.S | re.I)
_RE_ROW = re.compile(r'<tr\b[^>]*id="cbi-table-\d+"[^>]*>(?P<b>.*?)</tr>', re.S | re.I)
_RE_PAIR = re.compile(
    r'<div id="cbi-table-\d+-(?P<col>content|data)"[^>]*>(?P<b>.*?)<div id="cbip-',
    re.S | re.I,
)
_RE_STATIC = re.compile(
    r'<p class="form-control-static[^"]*"[^>]*>(?P<t>.*?)</p>', re.S | re.I
)
_RE_DETAILS = re.compile(r'<a class="btn[^"]*"[^>]*href="([^"]+)"', re.I)
# Formati tipo "2 Day 15:26:38" oppure "15:26:38": la parola cambia con la
# lingua, i numeri no.
_RE_UPTIME = re.compile(r"(?:(\d+)\s*\D+?\s*)?(\d{1,3}):(\d{2}):(\d{2})")


def _text(fragment: str) -> str:
    """Testo leggibile da un frammento HTML."""
    stripped = re.sub(r"<[^>]+>", "", fragment)
    return html_mod.unescape(re.sub(r"\s+", " ", stripped)).strip()


def parse_status_panel(raw_html: str, key: str) -> dict[str, Any]:
    """Normalizza un riquadro di stato in titolo, intestazione e righe."""
    title_match = _RE_TITLE.search(raw_html)
    title = _text(title_match.group("t")) if title_match else key

    headline: dict[str, Any] = {}
    head_match = _RE_HEAD.search(raw_html)
    if head_match:
        cells = [_text(m.group("t")) for m in _RE_TH.finditer(head_match.group("b"))]
        if cells:
            headline = {
                "label": cells[0],
                "value": cells[1] if len(cells) > 1 else "",
                "ok": "text-success" in head_match.group("b"),
            }

    rows: list[dict[str, str]] = []
    for row in _RE_ROW.finditer(raw_html):
        cells: dict[str, str] = {}
        for pair in _RE_PAIR.finditer(row.group("b")):
            static = _RE_STATIC.search(pair.group("b"))
            cells[pair.group("col")] = _text(static.group("t")) if static else ""
        label, value = cells.get("content", ""), cells.get("data", "")
        if label:
            rows.append({"label": label, "value": value})

    details = _RE_DETAILS.search(raw_html)
    return {
        "key": key,
        "title": title,
        "headline": headline,
        "rows": rows,
        "details_path": details.group(1).replace("/cgi-bin/luci", "")
        if details
        else None,
    }


def uptime_seconds(text: str) -> int | None:
    """Converte l'uptime del router in secondi.

    Il firmware localizza la parola «giorni», quindi ci si appoggia solo ai
    numeri: `2 Day 15:26:38` e `2 Giorno 15:26:38` danno lo stesso risultato.
    """
    match = _RE_UPTIME.search(text or "")
    if not match:
        return None
    days = int(match.group(1) or 0)
    hours, minutes, seconds = (int(match.group(i)) for i in (2, 3, 4))
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


_RE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def system_uptime(panel: dict[str, Any]) -> int | None:
    """Uptime in secondi dal riquadro di sistema.

    L'etichetta è localizzata, quindi si riconosce la riga dalla forma del
    valore: durata `[N g] HH:MM:SS`, escludendo l'ora locale che contiene una
    data e altrimenti combacerebbe.
    """
    for row in panel.get("rows", []):
        value = row.get("value", "")
        if _RE_DATE.search(value):
            continue
        seconds = uptime_seconds(value)
        if seconds is not None:
            return seconds
    return None


def find_row(panel: dict[str, Any], *needles: str) -> str | None:
    """Valore della prima riga la cui etichetta contiene uno dei termini.

    Le etichette sono localizzate, quindi si accettano più varianti.
    """
    wanted = [n.lower() for n in needles]
    for row in panel.get("rows", []):
        label = row["label"].lower()
        if any(n in label for n in wanted):
            return row["value"]
    return None
