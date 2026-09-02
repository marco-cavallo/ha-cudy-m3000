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
"""Config flow per l'integrazione Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import create_client, resolve_language
from .api import CudyAuthError, CudyConnectionError, CudyError
from .const import (
    AUTHOR,
    CONF_DEVICE_TRACKERS,
    CONF_LANGUAGE,
    CONF_PANEL,
    DEFAULT_DEVICE_TRACKERS,
    DEFAULT_LANGUAGE,
    DEFAULT_PANEL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    INTEGRATION_NAME,
    LANGUAGE_AUTO,
    MIN_SCAN_INTERVAL,
    ROUTER_LANGUAGES,
    VERSION as INTEGRATION_VERSION,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
    }
)


class CudyM3000ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gestisce l'aggiunta di un sistema mesh Cudy M3000."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Chiede indirizzo e password del nodo principale."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            username = user_input.get(CONF_USERNAME, DEFAULT_USERNAME).strip()

            client = create_client(
                self.hass,
                host,
                username,
                user_input[CONF_PASSWORD],
                resolve_language(self.hass, LANGUAGE_AUTO),
            )
            try:
                await client.async_login()
                nodes = await client.async_get_mesh_nodes()
            except CudyAuthError:
                errors["base"] = "invalid_auth"
            except CudyConnectionError:
                errors["base"] = "cannot_connect"
            except CudyError:
                _LOGGER.exception("Errore inatteso interrogando %s", host)
                errors["base"] = "unknown"
            else:
                root = next(
                    (n for n in nodes if isinstance(n, dict) and (n.get("sysreport") or {}).get("sn")),
                    None,
                )
                serial = (root or {}).get("sysreport", {}).get("sn") or host
                await self.async_set_unique_id(str(serial))
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})

                return self.async_create_entry(
                    title=f"Cudy M3000 ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Avvia la riautenticazione quando il router rifiuta le credenziali."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Chiede una nuova password per la voce esistente."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            client = create_client(
                self.hass,
                entry.data[CONF_HOST],
                entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
                user_input[CONF_PASSWORD],
                resolve_language(self.hass, LANGUAGE_AUTO),
            )
            try:
                await client.async_login()
            except CudyAuthError:
                errors["base"] = "invalid_auth"
            except CudyConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> CudyM3000OptionsFlow:
        """Espone il flow delle opzioni."""
        return CudyM3000OptionsFlow()


class CudyM3000OptionsFlow(OptionsFlow):
    """Menu delle opzioni: impostazioni e informazioni."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Mostra il menu di primo livello."""
        return self.async_show_menu(step_id="init", menu_options=["settings", "about"])

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Mostra e salva le opzioni."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        language_choices = [
            selector.SelectOptionDict(value=LANGUAGE_AUTO, label="Auto (Home Assistant)")
        ] + [
            selector.SelectOptionDict(value=code, label=code)
            for code in sorted(set(ROUTER_LANGUAGES.values()))
        ]

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=3600)),
                vol.Optional(
                    CONF_LANGUAGE,
                    default=options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=language_choices,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_PANEL, default=options.get(CONF_PANEL, DEFAULT_PANEL)
                ): bool,
                vol.Optional(
                    CONF_DEVICE_TRACKERS,
                    default=options.get(
                        CONF_DEVICE_TRACKERS, DEFAULT_DEVICE_TRACKERS
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="settings", data_schema=schema)

    async def async_step_about(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Spiega cosa fa l'integrazione e come sta girando adesso."""
        if user_input is not None:
            return await self.async_step_init()

        return self.async_show_form(
            step_id="about",
            data_schema=vol.Schema({}),
            description_placeholders=self._about_placeholders(),
        )

    def _about_placeholders(self) -> dict[str, str]:
        """Valori vivi mostrati nella scheda informativa."""
        options = self.config_entry.options
        placeholders = {
            "name": INTEGRATION_NAME,
            "version": INTEGRATION_VERSION,
            "author": AUTHOR,
            "host": self.config_entry.data.get(CONF_HOST, "-"),
            "interval": str(
                options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
            "language": str(options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)),
            "panel": _onoff(options.get(CONF_PANEL, DEFAULT_PANEL)),
            "trackers": _onoff(
                options.get(CONF_DEVICE_TRACKERS, DEFAULT_DEVICE_TRACKERS)
            ),
        }

        coordinator = getattr(self.config_entry, "runtime_data", None)
        if coordinator is None or coordinator.data is None:
            placeholders.update(
                dict.fromkeys(
                    (
                        "model", "firmware", "serial", "uptime", "nodes",
                        "nodes_online", "clients", "clients_24", "clients_5",
                    ),
                    "-",
                )
            )
            return placeholders

        data = coordinator.data
        root = data.root
        placeholders.update(
            {
                "model": _join(
                    root.model if root else None, root.hardware if root else None
                ),
                "firmware": (root.firmware if root else None) or "-",
                "serial": (root.serial if root else None) or "-",
                "uptime": _uptime(data.uptime),
                "nodes": str(len(data.nodes)),
                "nodes_online": str(data.online_nodes),
                "clients": str(data.total_clients),
                "clients_24": str(data.clients_on_band("2.4") or "-"),
                "clients_5": str(data.clients_on_band("5G") or "-"),
            }
        )
        return placeholders


def _onoff(value: bool) -> str:
    """Rappresentazione compatta di un'opzione booleana."""
    return "on" if value else "off"


def _join(model: str | None, hardware: str | None) -> str:
    """Modello e revisione hardware senza ripetere il modello."""
    if not hardware:
        return model or "-"
    if not model:
        return hardware
    return hardware if hardware.startswith(model) else f"{model} {hardware}"


def _uptime(seconds: int | None) -> str:
    """Uptime leggibile, indipendente dalla lingua."""
    if not seconds:
        return "-"
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"
