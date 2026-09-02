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
"""Costanti dell'integrazione Cudy M3000.

Cudy M3000 - By Marco Cavallo.
"""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "cudy_m3000"
INTEGRATION_NAME: Final = "Cudy M3000"
AUTHOR: Final = "Marco Cavallo"
VERSION: Final = "1.0.0"

CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_LANGUAGE: Final = "language"
CONF_PANEL: Final = "panel"
CONF_DEVICE_TRACKERS: Final = "device_trackers"

DEFAULT_USERNAME: Final = "admin"
DEFAULT_SCAN_INTERVAL: Final = 60
MIN_SCAN_INTERVAL: Final = 15
DEFAULT_PANEL: Final = True
# I client sono già tracciati da altre integrazioni: qui restano opt-in.
DEFAULT_DEVICE_TRACKERS: Final = False

# "auto" segue la lingua di Home Assistant.
LANGUAGE_AUTO: Final = "auto"
DEFAULT_LANGUAGE: Final = LANGUAGE_AUTO

MANUFACTURER: Final = "Cudy"

# Id sintetico che il firmware assegna al nodo principale (controller).
ROOT_NODE_ID: Final = "000000000000"

# Pannello nella barra laterale.
PANEL_URL_PATH: Final = "cudy-m3000"
PANEL_TITLE: Final = "Cudy M3000"
PANEL_ICON: Final = "mdi:access-point-network"
PANEL_COMPONENT: Final = "cudy-m3000-panel"
PANEL_MODULE_URL: Final = f"/{DOMAIN}_panel/panel.js"
PANEL_MODULE_IMPORT_URL: Final = PANEL_MODULE_URL

# Lingue servite dal firmware Cudy. La chiave è il codice Home Assistant.
ROUTER_LANGUAGES: Final[dict[str, str]] = {
    "ar": "ar", "bg": "bg", "bn": "bn", "ca": "ca", "cs": "cs", "de": "de",
    "el": "el", "en": "en", "es": "es", "fr": "fr", "he": "he", "hr": "hr",
    "hu": "hu", "it": "it", "ja": "ja", "km": "km", "ko": "ko", "nl": "nl",
    "no": "no", "nb": "no", "pl": "pl", "pt": "pt", "pt-BR": "pt", "ro": "ro",
    "ru": "ru", "sk": "sk", "sv": "sv", "th": "th", "tr": "tr", "uk": "uk",
    "vi": "vi", "zh-Hans": "zh_cn", "zh-Hant": "zh_tw",
}


def router_language(ha_language: str | None) -> str:
    """Traduce il codice lingua di Home Assistant in quello del firmware."""
    if not ha_language:
        return "en"
    if ha_language in ROUTER_LANGUAGES:
        return ROUTER_LANGUAGES[ha_language]
    # 'it-IT' -> 'it'
    base = ha_language.split("-")[0]
    return ROUTER_LANGUAGES.get(base, "en")
