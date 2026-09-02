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
"""Client asincrono per il firmware LuCI dei Cudy M3000.

Cudy M3000 - By Marco Cavallo.

Il firmware Cudy (derivato OpenWrt/LuCI) non ha API documentate, ma la pagina
della topologia mesh si alimenta da un endpoint JSON interno che espone tutto
quello che serve: inventario nodi, carico CPU/RAM, radio e client per nodo.

Autenticazione (ricavata da /luci-static/light/js/sysauth.js):
    1. GET  /cgi-bin/luci/                -> campi nascosti `_csrf` e `salt`
    2. POST /cgi-bin/luci/admin/get_token -> token di sessione monouso
    3. luci_password = sha256(sha256(password + salt) + token)
    4. POST /cgi-bin/luci/               -> cookie di sessione `sysauth`
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from typing import Any

import aiohttp

from .cbi import CbiForm, build_payload, parse_form, unknown_field_names

_LOGGER = logging.getLogger(__name__)


def _looks_like_login(text: str) -> bool:
    """True se il router ha risposto con la pagina di login invece del contenuto."""
    return 'name="luci_password"' in text and 'name="salt"' in text


def _submit_succeeded(text: str) -> bool:
    """Interpreta la risposta a un submit CBI."""
    lowered = text.lower()
    if "cbi-input-invalid" in lowered or "has-error" in lowered:
        return False
    return not _looks_like_login(text)

# Endpoint JSON usato dalla pagina "Mesh Topology" del firmware.
PATH_MESH_CLIENTS = "/admin/network/mesh/clients"
PATH_GET_TOKEN = "/admin/get_token"

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=25)

_RE_HIDDEN = r'name="{name}"[^>]*value="([^"]*)"'
_RE_HIDDEN_ALT = r'value="([^"]*)"[^>]*name="{name}"'


class CudyError(Exception):
    """Errore generico di comunicazione con il router."""


class CudyConnectionError(CudyError):
    """Il router non è raggiungibile."""


class CudyAuthError(CudyError):
    """Credenziali rifiutate dal router."""


def _hidden_field(html: str, name: str) -> str | None:
    """Estrae il valore di un input nascosto dal form di login."""
    for pattern in (_RE_HIDDEN, _RE_HIDDEN_ALT):
        match = re.search(pattern.format(name=re.escape(name)), html)
        if match:
            return match.group(1)
    return None


class CudyClient:
    """Gestisce sessione, login e letture verso un Cudy M3000."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        password: str,
        username: str = "admin",
        timezone: str = "UTC",
        language: str = "en",
    ) -> None:
        self._session = session
        self._host = host
        self._base = f"http://{host}/cgi-bin/luci"
        self._username = username
        self._password = password
        self._timezone = timezone
        self._language = language
        self._lock = asyncio.Lock()
        self._logged_in = False

    @property
    def host(self) -> str:
        """Indirizzo del nodo interrogato."""
        return self._host

    async def async_login(self) -> None:
        """Esegue il login e memorizza il cookie `sysauth` nella sessione."""
        try:
            # La pagina di login risponde 403 pur contenendo il form: è normale.
            async with self._session.get(
                f"{self._base}/", timeout=DEFAULT_TIMEOUT
            ) as resp:
                html = await resp.text()

            csrf = _hidden_field(html, "_csrf")
            salt = _hidden_field(html, "salt")
            if salt is None:
                raise CudyError(
                    "Form di login non riconosciuto: firmware non supportato?"
                )

            token = await self._async_fetch_token()

            digest = hashlib.sha256(f"{self._password}{salt}".encode()).hexdigest()
            if token:
                digest = hashlib.sha256(f"{digest}{token}".encode()).hexdigest()

            payload = {
                "_csrf": csrf or "",
                "token": token,
                "salt": salt,
                "zonename": self._timezone,
                "timeclock": str(int(time.time())),
                "luci_language": self._language,
                "luci_username": self._username,
                "luci_password": digest,
            }
            async with self._session.post(
                f"{self._base}/",
                data=payload,
                allow_redirects=False,
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                await resp.read()

        except aiohttp.ClientError as err:
            raise CudyConnectionError(f"Router non raggiungibile: {err}") from err
        except asyncio.TimeoutError as err:
            raise CudyConnectionError("Timeout nella connessione al router") from err

        if not self._has_auth_cookie():
            self._logged_in = False
            raise CudyAuthError("Login rifiutato: password errata?")

        self._logged_in = True
        _LOGGER.debug("Login riuscito su %s", self._host)

    async def _async_fetch_token(self) -> str:
        """Chiede un token monouso all'endpoint dedicato del router.

        È lo stesso endpoint che usa la UI del router prima di ogni login;
        farlo passare dall'integrazione evita di dipendere dal token che si
        trova incorporato nelle pagine, che può essere già stato consumato.
        """
        async with self._session.post(
            f"{self._base}{PATH_GET_TOKEN}", timeout=DEFAULT_TIMEOUT
        ) as resp:
            return (await resp.text()).strip()

    async def async_get_token(self) -> str:
        """Token monouso, rinnovando la sessione se necessario."""
        async with self._lock:
            if not self._logged_in:
                await self.async_login()
            return await self._async_fetch_token()

    @property
    def language(self) -> str:
        """Lingua con cui il router serve le pagine di configurazione."""
        return self._language

    async def async_set_language(self, language: str) -> None:
        """Cambia la lingua della sessione, rifacendo il login."""
        if language == self._language:
            return
        async with self._lock:
            self._language = language
            self._logged_in = False
            await self.async_login()

    def _has_auth_cookie(self) -> bool:
        """Verifica che la sessione abbia un cookie di autenticazione valido."""
        return any(
            cookie.key.startswith("sysauth")
            for cookie in self._session.cookie_jar
        )

    async def _async_get_json(self, path: str) -> Any:
        """GET autenticata che si aspetta JSON, con re-login trasparente."""
        async with self._lock:
            if not self._logged_in:
                await self.async_login()

            data = await self._async_try_json(path)
            if data is not None:
                return data

            # Sessione scaduta o invalidata da un altro client: un solo retry.
            _LOGGER.debug("Sessione scaduta su %s, rieseguo il login", self._host)
            self._logged_in = False
            await self.async_login()

            data = await self._async_try_json(path)
            if data is None:
                raise CudyAuthError(
                    f"Impossibile leggere {path}: la sessione non regge"
                )
            return data

    async def _async_try_json(self, path: str) -> Any | None:
        """Ritorna il JSON di `path`, o None se il router ha risposto altro.

        Quando la sessione non è valida il firmware serve la pagina di login
        (HTML) con status 200, quindi l'unico modo affidabile di accorgersene
        è tentare il parsing.
        """
        try:
            async with self._session.get(
                f"{self._base}{path}", timeout=DEFAULT_TIMEOUT
            ) as resp:
                if resp.status in (401, 403):
                    return None
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise CudyConnectionError(f"Errore leggendo {path}: {err}") from err
        except asyncio.TimeoutError as err:
            raise CudyConnectionError(f"Timeout leggendo {path}") from err

        stripped = text.lstrip()
        if not stripped.startswith(("[", "{")):
            return None

        try:
            import json

            return json.loads(text)
        except ValueError:
            return None

    async def async_get_mesh_nodes(self) -> list[dict[str, Any]]:
        """Ritorna l'elenco dei nodi mesh con stato, radio e carico."""
        data = await self._async_get_json(PATH_MESH_CLIENTS)
        if not isinstance(data, list):
            raise CudyError(
                f"Risposta inattesa da {PATH_MESH_CLIENTS}: {type(data).__name__}"
            )
        return data

    async def _async_authed_request(
        self,
        method: str,
        path: str,
        *,
        data: Any = None,
        retry: bool = True,
    ) -> str:
        """Richiesta autenticata che ritorna testo, con re-login trasparente."""
        async with self._lock:
            if not self._logged_in:
                await self.async_login()
            text = await self._async_raw_request(method, path, data)
            if _looks_like_login(text) and retry:
                _LOGGER.debug("Sessione invalidata su %s, rieseguo il login", self._host)
                self._logged_in = False
                await self.async_login()
                text = await self._async_raw_request(method, path, data)
            return text

    async def _async_raw_request(self, method: str, path: str, data: Any) -> str:
        """Esegue una singola richiesta HTTP e ne ritorna il corpo."""
        url = f"{self._base}{path}"
        try:
            async with self._session.request(
                method, url, data=data, timeout=DEFAULT_TIMEOUT
            ) as resp:
                return await resp.text()
        except aiohttp.ClientError as err:
            raise CudyConnectionError(f"Errore su {path}: {err}") from err
        except asyncio.TimeoutError as err:
            raise CudyConnectionError(f"Timeout su {path}") from err

    async def async_get_html(self, path: str) -> str:
        """Scarica una pagina della UI del router."""
        return await self._async_authed_request("GET", path)

    async def async_get_form(self, path: str) -> CbiForm:
        """Scarica una pagina di configurazione e la normalizza."""
        return parse_form(await self.async_get_html(path), path)

    async def async_submit_form(
        self, path: str, changes: dict[str, Any]
    ) -> tuple[bool, str]:
        """Applica delle modifiche a una pagina di configurazione.

        Il form viene riletto subito prima dell'invio: serve un token fresco e
        serve ripartire dai valori correnti, così le opzioni non toccate
        restano quelle che sono.
        """
        form = await self.async_get_form(path)

        unknown = unknown_field_names(form, changes)
        if unknown:
            raise CudyError(f"Campi sconosciuti per {path}: {', '.join(unknown)}")

        payload = build_payload(form, changes, timeclock=str(int(time.time())))
        body = aiohttp.FormData()
        for name, value in payload:
            body.add_field(name, value)

        text = await self._async_authed_request("POST", path, data=body, retry=False)
        return _submit_succeeded(text), text

    async def async_post_action(
        self,
        path: str,
        fields: dict[str, str] | None = None,
        token: str | None = None,
    ) -> str:
        """Esegue un'azione POST (toggle LED, riavvio nodo, diagnostica).

        Replica il formato multipart che usa `cbi_switch_toggle` nella UI.

        Il token va preso dalla pagina che disegna il comando: il router
        rifiuta silenziosamente un token appena emesso da /admin/get_token,
        che resta valido solo per il login.
        """
        if token is None:
            token = await self.async_get_token()
        body = aiohttp.FormData()
        body.add_field("token", token)
        body.add_field("cbi.submit", "1")
        for name, value in (fields or {}).items():
            body.add_field(name, value)
        return await self._async_authed_request("POST", path, data=body, retry=False)
