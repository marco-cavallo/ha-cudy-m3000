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
"""Integrazione Cudy M3000 (sistema mesh Wi-Fi 6 AX3000).

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

import logging

import aiohttp
from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from . import websocket_api as cudy_ws
from .api import CudyAuthError, CudyClient, CudyConnectionError
from .const import (
    CONF_DEVICE_TRACKERS,
    CONF_LANGUAGE,
    CONF_PANEL,
    DEFAULT_DEVICE_TRACKERS,
    DEFAULT_LANGUAGE,
    DEFAULT_PANEL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    LANGUAGE_AUTO,
    PANEL_COMPONENT,
    PANEL_ICON,
    PANEL_MODULE_IMPORT_URL,
    PANEL_MODULE_URL,
    PANEL_TITLE,
    PANEL_URL_PATH,
    router_language,
)
from .coordinator import CudyM3000Coordinator
from .services import async_register_services, async_unregister_services

_LOGGER = logging.getLogger(__name__)

# I device_tracker dei client sono opzionali: chi ha già un'integrazione di
# scansione della rete non vuole un secondo set di entità per gli stessi
# dispositivi.
BASE_PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]

type CudyConfigEntry = ConfigEntry[CudyM3000Coordinator]


def resolve_language(hass: HomeAssistant, configured: str) -> str:
    """Lingua con cui chiedere le pagine al router.

    Le etichette delle pagine di configurazione le produce il firmware, quindi
    l'unico modo di avere il pannello nella lingua di Home Assistant è chiedere
    al router di servirle in quella lingua.
    """
    if configured and configured != LANGUAGE_AUTO:
        return configured
    return router_language(hass.config.language)


def create_client(
    hass: HomeAssistant,
    host: str,
    username: str,
    password: str,
    language: str = "en",
) -> CudyClient:
    """Crea un client con una sessione HTTP dedicata.

    La sessione ha un cookie jar `unsafe`: il jar di default di aiohttp scarta
    i cookie provenienti da host indicati per indirizzo IP, e senza il cookie
    `sysauth` ogni richiesta successiva al login verrebbe rifiutata.
    """
    session = async_create_clientsession(
        hass,
        verify_ssl=False,
        cookie_jar=aiohttp.CookieJar(unsafe=True),
    )
    return CudyClient(
        session=session,
        host=host,
        password=password,
        username=username,
        timezone=hass.config.time_zone or "UTC",
        language=language,
    )


async def async_setup_entry(hass: HomeAssistant, entry: CudyConfigEntry) -> bool:
    """Configura una istanza dell'integrazione."""
    language = resolve_language(
        hass, entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    )
    client = create_client(
        hass,
        entry.data[CONF_HOST],
        entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
        entry.data[CONF_PASSWORD],
        language,
    )

    try:
        await client.async_login()
    except CudyAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except CudyConnectionError as err:
        raise ConfigEntryNotReady(str(err)) from err

    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    coordinator = CudyM3000Coordinator(hass, entry, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    platforms = _platforms_for(entry)
    if Platform.DEVICE_TRACKER not in platforms:
        _async_purge_device_trackers(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    cudy_ws.async_register(hass)
    async_register_services(hass)
    await _async_setup_panel(hass, entry.options.get(CONF_PANEL, DEFAULT_PANEL))

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def _async_setup_panel(hass: HomeAssistant, enabled: bool) -> None:
    """Registra (o rimuove) il pannello nella barra laterale."""
    registered = PANEL_URL_PATH in hass.data.get("frontend_panels", {})

    if not enabled:
        if registered:
            frontend.async_remove_panel(hass, PANEL_URL_PATH)
        return

    if registered:
        return

    if not hass.data.get(f"{DOMAIN}_static_registered"):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    PANEL_MODULE_URL,
                    hass.config.path(f"custom_components/{DOMAIN}/panel/panel.js"),
                    False,  # il file cambia con l'integrazione: niente cache lunga
                )
            ]
        )
        hass.data[f"{DOMAIN}_static_registered"] = True

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name=PANEL_COMPONENT,
        frontend_url_path=PANEL_URL_PATH,
        module_url=PANEL_MODULE_IMPORT_URL,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=True,
        config={},
    )


@callback
def _async_purge_device_trackers(hass: HomeAssistant, entry: CudyConfigEntry) -> None:
    """Elimina i device_tracker rimasti dopo aver disattivato l'opzione.

    Senza questo resterebbero nel registro come entità non disponibili, che è
    esattamente il disordine che l'opzione vuole evitare.
    """
    registry = er.async_get(hass)
    stale = [
        item.entity_id
        for item in er.async_entries_for_config_entry(registry, entry.entry_id)
        if item.domain == Platform.DEVICE_TRACKER.value
    ]
    for entity_id in stale:
        registry.async_remove(entity_id)
    if stale:
        _LOGGER.debug("Rimossi %d device_tracker non più richiesti", len(stale))


def _platforms_for(entry: CudyConfigEntry) -> list[Platform]:
    """Piattaforme da caricare per questa istanza."""
    platforms = list(BASE_PLATFORMS)
    if entry.options.get(CONF_DEVICE_TRACKERS, DEFAULT_DEVICE_TRACKERS):
        platforms.append(Platform.DEVICE_TRACKER)
    return platforms


async def async_unload_entry(hass: HomeAssistant, entry: CudyConfigEntry) -> bool:
    """Rimuove una istanza dell'integrazione."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, _platforms_for(entry)
    )
    if unloaded and len(hass.config_entries.async_loaded_entries(DOMAIN)) <= 1:
        if PANEL_URL_PATH in hass.data.get("frontend_panels", {}):
            frontend.async_remove_panel(hass, PANEL_URL_PATH)
        async_unregister_services(hass)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: CudyConfigEntry) -> None:
    """Ricarica l'integrazione quando cambiano le opzioni."""
    await hass.config_entries.async_reload(entry.entry_id)
