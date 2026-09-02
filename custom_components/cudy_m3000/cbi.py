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
"""Motore generico per i form CBI di LuCI.

Cudy M3000 - By Marco Cavallo.

Tutte le pagine di configurazione del firmware Cudy usano lo stesso schema CBI
di LuCI, quindi non serve un parser per pagina: questo modulo trasforma una
qualsiasi pagina in uno schema dichiarativo (campi, tipi, opzioni, valori,
dipendenze) e sa ricostruire il POST che il browser invierebbe.

Convenzioni CBI rilevanti:
    cbid.<config>.<sezione>.<opzione>       valore del campo
    cbi.cbe.<config>.<sezione>.<opzione>    marcatore di presenza dei flag
    token + cbi.submit=1                    campi obbligatori di submit
    cbi_d_add("<id>", {"<dep>": "<val>"})   visibilità condizionale
"""

from __future__ import annotations

import html as html_mod
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Campi di servizio che gestiamo a mano e non vanno esposti nella UI.
CONTROL_FIELDS = frozenset({"token", "timeclock", "cbi.submit"})

_RE_SCRIPT = re.compile(r"<script.*?</script>", re.S | re.I)
_RE_FORM_ACTION = re.compile(r'<form[^>]*action="([^"]*)"', re.I)
_RE_TITLE = re.compile(r'<h4[^>]*class="modal-title"[^>]*>(.*?)</h4>', re.S | re.I)
_RE_GROUP = re.compile(
    r'<div class="form-group"(?P<attrs>[^>]*)>(?P<body>.*?)'
    r'(?=<div class="form-group"|<div class="cbi-page-actions"|</form>|$)',
    re.S | re.I,
)
_RE_TABLE = re.compile(r"<table\b(?P<attrs>[^>]*)>(?P<body>.*?)</table>", re.S | re.I)
_RE_ROW = re.compile(r'<tr\b(?P<attrs>[^>]*)>(?P<body>.*?)</tr>', re.S | re.I)
_RE_CELL = re.compile(r"<t[dh]\b[^>]*>(?P<body>.*?)</t[dh]>", re.S | re.I)
_RE_CELL_ID = re.compile(r'<div id="cbi-(?P<sid>[^"]+?)-(?P<col>[^"-]+)"', re.I)
_RE_STATIC = re.compile(
    r'<p class="form-control-static[^"]*"[^>]*>(?P<text>.*?)</p>', re.S | re.I
)
_RE_SWITCH_URL = re.compile(r"cbi_switch_toggle\(\s*this\s*,\s*\w+\s*,\s*'([^']+)'")
_RE_LABEL = re.compile(
    r'<label[^>]*class="[^"]*control-label[^"]*"[^>]*>(?P<inner>.*?)</label>', re.S | re.I
)
_RE_HELP = re.compile(r'data-content="([^"]*)"', re.I)
_RE_INPUT = re.compile(r"<input\b(?P<attrs>[^>]*)>", re.I)
_RE_SELECT = re.compile(
    r"<select\b(?P<attrs>[^>]*)>(?P<body>.*?)</select>", re.S | re.I
)
_RE_OPTION = re.compile(
    r"<option\b(?P<attrs>[^>]*)>(?P<text>.*?)</option>", re.S | re.I
)
_RE_TEXTAREA = re.compile(
    r"<textarea\b(?P<attrs>[^>]*)>(?P<body>.*?)</textarea>", re.S | re.I
)
_RE_TOGGLE = re.compile(r"fa-toggle-(on|off)", re.I)
_RE_DEP = re.compile(
    r'cbi_d_add\(\s*"(?P<id>[^"]+)"\s*,\s*(?P<deps>\{.*?\})', re.S
)


def _attr(attrs: str, name: str) -> str | None:
    """Valore di un attributo HTML, con entità già decodificate."""
    match = re.search(rf'{name}\s*=\s*"([^"]*)"', attrs, re.I)
    if match is None:
        match = re.search(rf"{name}\s*=\s*'([^']*)'", attrs, re.I)
    return html_mod.unescape(match.group(1)) if match else None


def _has_flag(attrs: str, name: str) -> bool:
    """True se un attributo booleano (checked, disabled, selected) è presente."""
    return re.search(rf"\b{name}\b", attrs, re.I) is not None


def _text(fragment: str) -> str:
    """Testo leggibile da un frammento HTML."""
    stripped = re.sub(r"<[^>]+>", "", fragment)
    return html_mod.unescape(re.sub(r"\s+", " ", stripped)).strip()


@dataclass(slots=True)
class CbiField:
    """Un campo di configurazione esposto dal router."""

    name: str
    kind: str  # text | password | select | flag | radio | textarea | static
    label: str = ""
    value: Any = ""
    options: list[dict[str, str]] = field(default_factory=list)
    help: str = ""
    group_id: str = ""
    # Alternative in OR: il campo è visibile se una qualsiasi è soddisfatta.
    depends: list[dict[str, str]] = field(default_factory=list)
    required: bool = False
    editable: bool = True
    # Sezione UCI (la parte centrale di cbid.<config>.<sezione>.<opzione>):
    # serve al pannello per separare visivamente, ad esempio, 2.4G da 5G.
    section: str = ""
    # Toggle che agiscono con un POST diretto invece che col submit del form
    # (è il caso dei LED per nodo mesh).
    action_url: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Rappresentazione serializzabile per il pannello."""
        return {
            "name": self.name,
            "kind": self.kind,
            "label": self.label,
            "value": self.value,
            "options": self.options,
            "help": self.help,
            "group_id": self.group_id,
            "depends": self.depends,
            "required": self.required,
            "editable": self.editable,
            "section": self.section,
            "action_url": self.action_url,
        }


@dataclass(slots=True)
class CbiTable:
    """Una sezione tabellare (una riga per elemento, es. i LED dei nodi)."""

    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Rappresentazione serializzabile per il pannello."""
        return {"columns": self.columns, "rows": self.rows}


@dataclass(slots=True)
class CbiForm:
    """Una pagina di configurazione, normalizzata."""

    path: str
    title: str
    token: str
    action: str
    fields: list[CbiField]
    tables: list[CbiTable] = field(default_factory=list)
    # Coppie (nome, valore) da rispedire invariate: marcatori cbi.cbe e simili.
    passthrough: list[tuple[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def field_by_name(self, name: str) -> CbiField | None:
        """Cerca un campo per nome, tra quelli semplici e quelli in tabella."""
        for item in self.fields:
            if item.name == name:
                return item
        for table in self.tables:
            for row in table.rows:
                for cell in row["cells"].values():
                    if isinstance(cell, dict) and cell.get("name") == name:
                        return CbiField(**{
                            k: v for k, v in cell.items()
                            if k in CbiField.__slots__
                        })
        return None

    def as_dict(self) -> dict[str, Any]:
        """Schema serializzabile per il pannello."""
        return {
            "path": self.path,
            "title": self.title,
            "fields": [f.as_dict() for f in self.fields],
            "tables": [t.as_dict() for t in self.tables],
            "notes": self.notes,
        }


def _parse_dependencies(raw_html: str) -> dict[str, list[dict[str, str]]]:
    """Estrae le dipendenze di visibilità dichiarate via cbi_d_add().

    Lo stesso campo può comparire più volte: sono alternative in OR, quindi
    vanno raccolte in lista e non sovrascritte.
    """
    deps: dict[str, list[dict[str, str]]] = {}
    for match in _RE_DEP.finditer(raw_html):
        try:
            parsed = json.loads(match.group("deps"))
        except ValueError:
            continue
        if isinstance(parsed, dict):
            deps.setdefault(match.group("id"), []).append(
                {str(k): str(v) for k, v in parsed.items()}
            )
    return deps


def _parse_widgets(body: str) -> list[tuple[str, str, dict[str, Any]]]:
    """Estrae i widget di un blocco, come (nome, tipo, dati)."""
    widgets: list[tuple[str, str, dict[str, Any]]] = []

    for match in _RE_SELECT.finditer(body):
        attrs = match.group("attrs")
        name = _attr(attrs, "name")
        if not name:
            continue
        options: list[dict[str, str]] = []
        selected = ""
        for opt in _RE_OPTION.finditer(match.group("body")):
            value = _attr(opt.group("attrs"), "value") or ""
            options.append({"value": value, "label": _text(opt.group("text"))})
            if _has_flag(opt.group("attrs"), "selected"):
                selected = value
        if not selected and options:
            selected = options[0]["value"]
        widgets.append((name, "select", {"value": selected, "options": options}))

    for match in _RE_TEXTAREA.finditer(body):
        name = _attr(match.group("attrs"), "name")
        if name:
            widgets.append(
                (name, "textarea", {"value": html_mod.unescape(match.group("body"))})
            )

    for match in _RE_INPUT.finditer(body):
        attrs = match.group("attrs")
        name = _attr(attrs, "name")
        if not name:
            continue
        input_type = (_attr(attrs, "type") or "text").lower()
        if input_type == "submit":
            continue
        widgets.append(
            (
                name,
                input_type,
                {
                    "value": _attr(attrs, "value") or "",
                    "checked": _has_flag(attrs, "checked"),
                    "required": "required" in (_attr(attrs, "class") or ""),
                    "readonly": _has_flag(attrs, "readonly")
                    or _has_flag(attrs, "disabled"),
                },
            )
        )

    return widgets


def _build_field(
    name: str,
    kind: str,
    data: dict[str, Any],
    *,
    label: str,
    help_text: str,
    gid: str,
    deps: dict[str, list[dict[str, str]]],
    block: str,
) -> CbiField | None:
    """Costruisce un CbiField da un widget grezzo, o None se va ignorato."""
    is_toggle = bool(_RE_TOGGLE.search(block))
    switch = _RE_SWITCH_URL.search(block)

    if kind == "hidden" and is_toggle:
        resolved, value = "flag", str(data.get("value", "0")) == "1"
    elif kind == "checkbox":
        resolved, value = "flag", bool(data.get("checked"))
    elif kind in ("select", "textarea"):
        resolved, value = kind, data.get("value", "")
    elif kind == "hidden":
        return None
    else:
        resolved = "password" if kind == "password" else "text"
        value = data.get("value", "")

    parts = name.split(".")
    return CbiField(
        name=name,
        kind=resolved,
        section=parts[2] if len(parts) > 2 else "",
        label=label or name,
        value=value,
        options=data.get("options", []),
        help=help_text,
        group_id=gid,
        depends=deps.get(gid, []),
        required=bool(data.get("required")),
        editable=not data.get("readonly"),
        action_url=switch.group(1).replace("/cgi-bin/luci", "") if switch else None,
    )


def _parse_tables(
    body_html: str, deps: dict[str, list[dict[str, str]]], claimed: set[str]
) -> list[CbiTable]:
    """Estrae le sezioni tabellari (una riga per elemento)."""
    tables: list[CbiTable] = []

    for tmatch in _RE_TABLE.finditer(body_html):
        raw_rows = list(_RE_ROW.finditer(tmatch.group("body")))
        if not raw_rows:
            continue

        columns: list[str] = []
        rows: list[dict[str, Any]] = []

        for rmatch in raw_rows:
            row_body = rmatch.group("body")
            row_id = _attr(rmatch.group("attrs"), "id") or ""
            cells = list(_RE_CELL.finditer(row_body))

            # Riga di intestazione: nessun id cbi-* e nessun widget.
            if not row_id.startswith("cbi-") and "<th" in row_body.lower():
                columns = [_text(c.group("body")) for c in cells]
                continue
            if not row_id.startswith("cbi-"):
                continue

            parsed_cells: dict[str, Any] = {}
            order: list[str] = []
            for cell in cells:
                cell_body = cell.group("body")
                id_match = _RE_CELL_ID.search(cell_body)
                col = id_match.group("col") if id_match else f"col{len(order)}"
                order.append(col)

                widgets = [
                    w for w in _parse_widgets(cell_body)
                    if not w[0].startswith("cbi.cbe.")
                ]
                if widgets:
                    name, kind, data = widgets[0]
                    built = _build_field(
                        name, kind, data, label=col, help_text="",
                        gid=id_match.group(0) if id_match else "",
                        deps=deps, block=cell_body,
                    )
                    if built is not None:
                        parsed_cells[col] = built.as_dict()
                        claimed.add(name)
                        continue

                static = _RE_STATIC.search(cell_body)
                parsed_cells[col] = {
                    "kind": "static",
                    "value": _text(static.group("text")) if static else _text(cell_body),
                }

            if parsed_cells:
                rows.append({"id": row_id, "cells": parsed_cells})
                if not columns or len(columns) != len(order):
                    columns = order

        if rows:
            tables.append(CbiTable(columns=columns, rows=rows))

    return tables


def parse_form(raw_html: str, path: str) -> CbiForm:
    """Trasforma una pagina di configurazione in uno schema CbiForm."""
    body_html = _RE_SCRIPT.sub("", raw_html)
    deps = _parse_dependencies(raw_html)

    token_match = re.search(r'name="token"[^>]*value="([^"]*)"', raw_html)
    token = token_match.group(1) if token_match else ""

    action_match = _RE_FORM_ACTION.search(raw_html)
    action = html_mod.unescape(action_match.group(1)) if action_match else path

    title_match = _RE_TITLE.search(body_html)
    title = _text(title_match.group(1)) if title_match else path.rsplit("/", 1)[-1]

    notes = [
        _text(m) for m in re.findall(
            r'<div class="alert alert-info"[^>]*>(.*?)</div>', body_html, re.S
        )
    ]

    fields: list[CbiField] = []
    passthrough: list[tuple[str, str]] = []
    claimed: set[str] = set()

    tables = _parse_tables(body_html, deps, claimed)

    for group in _RE_GROUP.finditer(body_html):
        gid = _attr(group.group("attrs"), "id") or ""
        block = group.group("body")

        label_match = _RE_LABEL.search(block)
        label = _text(label_match.group("inner")) if label_match else ""
        help_match = _RE_HELP.search(block)
        help_text = html_mod.unescape(help_match.group(1)) if help_match else ""

        widgets = _parse_widgets(block)
        markers = [w for w in widgets if w[0].startswith("cbi.cbe.")]
        for name, _kind, data in markers:
            if name not in claimed:
                passthrough.append((name, str(data.get("value", "1"))))
                claimed.add(name)

        value_widgets = [
            w for w in widgets
            if not w[0].startswith("cbi.cbe.") and w[0] not in CONTROL_FIELDS
        ]

        radios = [w for w in value_widgets if w[1] == "radio"]
        if radios:
            name = radios[0][0]
            selected = next(
                (w[2]["value"] for w in radios if w[2].get("checked")),
                radios[0][2]["value"],
            )
            labels = re.findall(
                r'<input[^>]*type="radio"[^>]*>\s*(?:</label>)?\s*([^<]{1,40})', block
            )
            options = [
                {
                    "value": w[2]["value"],
                    "label": _text(labels[i]) if i < len(labels) else w[2]["value"],
                }
                for i, w in enumerate(radios)
            ]
            fields.append(
                CbiField(
                    name=name, kind="radio", label=label, value=selected,
                    options=options, help=help_text, group_id=gid,
                    depends=deps.get(gid, []),
                )
            )
            claimed.add(name)
            continue

        # LuCI rende alcune opzioni come combobox: una <select> e un <input>
        # con lo stesso name. Vanno rispediti entrambi (il valore cambiato vale
        # per tutti, avendo lo stesso nome) ma se ne mostra uno solo.
        seen_names: set[str] = set()
        for name, kind, data in value_widgets:
            if kind == "hidden" and not _RE_TOGGLE.search(block):
                if name not in claimed:
                    passthrough.append((name, str(data.get("value", ""))))
                    claimed.add(name)
                continue

            built = _build_field(
                name, kind, data,
                label=label or name,
                help_text=help_text, gid=gid, deps=deps, block=block,
            )
            if built is None:
                continue
            if name in seen_names:
                # Duplicato della combobox: entra nel payload, non nella UI.
                built.kind = "mirror"
            seen_names.add(name)
            fields.append(built)
            claimed.add(name)

    for match in _RE_INPUT.finditer(body_html):
        attrs = match.group("attrs")
        name = _attr(attrs, "name")
        if not name or name in claimed or name in CONTROL_FIELDS:
            continue
        if (_attr(attrs, "type") or "").lower() == "hidden":
            passthrough.append((name, _attr(attrs, "value") or ""))
            claimed.add(name)

    _number_repeated_labels(fields)

    return CbiForm(
        path=path, title=title, token=token, action=action, fields=fields,
        tables=tables, passthrough=passthrough, notes=[n for n in notes if n],
    )


def _number_repeated_labels(fields: list[CbiField]) -> None:
    """Numera le etichette ripetute solo quando i campi convivono a schermo.

    Il firmware chiama tutti e quattro i server NTP «Server NTP», e lì l'indice
    serve. Ma chiama «Canale» anche le quattro varianti alternative legate alla
    modalità radio: quelle non sono mai visibili insieme, e numerarle
    confonderebbe invece di chiarire. Il discriminante sono le dipendenze:
    stesse dipendenze significa visibili insieme.
    """

    def bucket(item: CbiField) -> tuple[str, str, str]:
        return (item.section, item.label, json.dumps(item.depends, sort_keys=True))

    counts: dict[tuple[str, str, str], int] = {}
    for item in fields:
        if item.kind != "mirror":
            counts[bucket(item)] = counts.get(bucket(item), 0) + 1

    seen: dict[tuple[str, str, str], int] = {}
    for item in fields:
        if item.kind == "mirror":
            continue
        key = bucket(item)
        if counts.get(key, 0) < 2:
            continue
        seen[key] = seen.get(key, 0) + 1
        item.label = f"{item.label} {seen[key]}"


def build_payload(
    form: CbiForm, changes: dict[str, Any] | None = None, timeclock: str = ""
) -> list[tuple[str, str]]:
    """Ricostruisce il POST del form applicando le modifiche richieste.

    Ritorna una lista di coppie (e non un dict) perché CBI usa lo stesso nome
    più volte per le liste dinamiche, ad esempio i server NTP.
    """
    changes = changes or {}
    payload: list[tuple[str, str]] = [
        ("token", form.token),
        ("timeclock", timeclock),
        ("cbi.submit", "1"),
    ]
    payload.extend(form.passthrough)

    def emit(name: str, kind: str, current: Any) -> None:
        raw = changes.get(name, current)
        if kind == "flag":
            payload.append((name, "1" if raw in (True, "1", 1, "true") else "0"))
        else:
            payload.append((name, "" if raw is None else str(raw)))

    for item in form.fields:
        emit(item.name, item.kind, item.value)

    for table in form.tables:
        for row in table.rows:
            for cell in row["cells"].values():
                if isinstance(cell, dict) and cell.get("kind") not in (None, "static"):
                    emit(cell["name"], cell["kind"], cell.get("value"))

    return payload


def unknown_field_names(form: CbiForm, changes: dict[str, Any]) -> list[str]:
    """Nomi presenti nelle modifiche ma non nel form: indicano un errore."""
    known = {f.name for f in form.fields}
    for table in form.tables:
        for row in table.rows:
            for cell in row["cells"].values():
                if isinstance(cell, dict) and cell.get("name"):
                    known.add(cell["name"])
    return sorted(name for name in changes if name not in known)
