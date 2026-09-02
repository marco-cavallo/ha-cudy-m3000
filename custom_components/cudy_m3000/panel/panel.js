/*
 * Copyright 2026 Marco Cavallo
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/*
 * Cudy M3000 - pannello laterale
 * By Marco Cavallo
 *
 * Custom element vanilla: nessuna dipendenza esterna, nessuno step di build.
 * Parla con l'integrazione tramite i suoi comandi WebSocket.
 *
 * Le etichette del pannello seguono la lingua di Home Assistant; le etichette
 * delle pagine di configurazione arrivano già tradotte dal router, che viene
 * interrogato nella stessa lingua.
 */

const DOMAIN = "cudy_m3000";

// ---------------------------------------------------------------- traduzioni
const I18N = {
  en: {
    about: "About",
    diagnostics: "Diagnostics", target: "Address or hostname", run: "Run", running: "Running…", output: "Output", syslog: "System log", reload: "Reload", noOutput: "No output",
    uptime: "Uptime",
    info: "Info", openMenu: "Open the sidebar", showInfo: "Show details", hideInfo: "Hide details",
    overview: "Overview", nodes: "Nodes", devices: "Devices", settings: "Settings",
    nodesOnline: "Nodes online", clients: "Clients", wireless: "Wi-Fi clients",
    firmware: "Firmware", refresh: "Refresh", search: "Search devices…",
    node: "Node", band: "Band", ip: "IP address", mac: "MAC", rate: "Rate",
    duration: "Duration", hostname: "Name", wired: "Wired", controller: "Controller",
    satellite: "Satellite", online: "Online", offline: "Offline", cpu: "CPU",
    memory: "Memory", backhaul: "Backhaul", channel: "Channel", led: "LED",
    reboot: "Reboot", save: "Save", saving: "Saving…", saved: "Settings applied",
    saveFailed: "The router rejected the change", loading: "Loading…",
    noDevices: "No devices found", noChanges: "Nothing to save",
    confirmReboot: "Reboot this node?", model: "Model", serial: "Serial number",
    uplink: "Uplink", network: "Network", wirelessSec: "Wireless",
    system: "System", security: "Security", clientsOn: "Devices on this node",
    error: "Error", retry: "Retry", applying: "Applying, the router may take a few seconds…",
    empty: "This node has no connected devices", collapse: "Collapse", expand: "Details",
  },
  it: {
    about: "Info",
    diagnostics: "Diagnostica", target: "Indirizzo o nome host", run: "Esegui", running: "In corso…", output: "Risultato", syslog: "Log di sistema", reload: "Ricarica", noOutput: "Nessun risultato",
    uptime: "Acceso da",
    info: "Info", openMenu: "Apri il menu laterale", showInfo: "Mostra i dettagli", hideInfo: "Nascondi i dettagli",
    overview: "Panoramica", nodes: "Nodi", devices: "Dispositivi", settings: "Impostazioni",
    nodesOnline: "Nodi online", clients: "Dispositivi", wireless: "Dispositivi Wi-Fi",
    firmware: "Firmware", refresh: "Aggiorna", search: "Cerca dispositivi…",
    node: "Nodo", band: "Banda", ip: "Indirizzo IP", mac: "MAC", rate: "Velocità",
    duration: "Durata", hostname: "Nome", wired: "Cablato", controller: "Principale",
    satellite: "Satellite", online: "Online", offline: "Offline", cpu: "CPU",
    memory: "Memoria", backhaul: "Backhaul", channel: "Canale", led: "LED",
    reboot: "Riavvia", save: "Salva", saving: "Salvataggio…", saved: "Impostazioni applicate",
    saveFailed: "Il router ha rifiutato la modifica", loading: "Caricamento…",
    noDevices: "Nessun dispositivo trovato", noChanges: "Nessuna modifica da salvare",
    confirmReboot: "Riavviare questo nodo?", model: "Modello", serial: "Numero di serie",
    uplink: "Collegamento", network: "Rete", wirelessSec: "Wireless",
    system: "Sistema", security: "Sicurezza", clientsOn: "Dispositivi su questo nodo",
    error: "Errore", retry: "Riprova", applying: "Applicazione in corso, il router può metterci qualche secondo…",
    empty: "Nessun dispositivo collegato a questo nodo", collapse: "Chiudi", expand: "Dettagli",
  },
  de: {
    about: "Info",
    diagnostics: "Diagnose", target: "Adresse oder Hostname", run: "Starten", running: "Läuft…", output: "Ausgabe", syslog: "Systemprotokoll", reload: "Neu laden", noOutput: "Keine Ausgabe",
    uptime: "Laufzeit",
    info: "Info", openMenu: "Seitenleiste öffnen", showInfo: "Details zeigen", hideInfo: "Details ausblenden",
    overview: "Übersicht", nodes: "Knoten", devices: "Geräte", settings: "Einstellungen",
    nodesOnline: "Knoten online", clients: "Geräte", wireless: "WLAN-Geräte",
    firmware: "Firmware", refresh: "Aktualisieren", search: "Geräte suchen…",
    node: "Knoten", band: "Band", ip: "IP-Adresse", mac: "MAC", rate: "Rate",
    duration: "Dauer", hostname: "Name", wired: "Kabel", controller: "Hauptknoten",
    satellite: "Satellit", online: "Online", offline: "Offline", cpu: "CPU",
    memory: "Speicher", backhaul: "Backhaul", channel: "Kanal", led: "LED",
    reboot: "Neustart", save: "Speichern", saving: "Speichern…", saved: "Übernommen",
    saveFailed: "Der Router hat die Änderung abgelehnt", loading: "Wird geladen…",
    noDevices: "Keine Geräte gefunden", noChanges: "Nichts zu speichern",
    confirmReboot: "Diesen Knoten neu starten?", model: "Modell", serial: "Seriennummer",
    uplink: "Uplink", network: "Netzwerk", wirelessSec: "WLAN",
    system: "System", security: "Sicherheit", clientsOn: "Geräte an diesem Knoten",
    error: "Fehler", retry: "Erneut", applying: "Wird angewendet…",
    empty: "Keine Geräte an diesem Knoten", collapse: "Schließen", expand: "Details",
  },
  fr: {
    about: "À propos",
    diagnostics: "Diagnostic", target: "Adresse ou nom d\u2019h\u00f4te", run: "Ex\u00e9cuter", running: "En cours\u2026", output: "R\u00e9sultat", syslog: "Journal syst\u00e8me", reload: "Recharger", noOutput: "Aucun r\u00e9sultat",
    uptime: "Temps de marche",
    info: "Infos", openMenu: "Ouvrir le menu latéral", showInfo: "Afficher les détails", hideInfo: "Masquer les détails",
    overview: "Aperçu", nodes: "Nœuds", devices: "Appareils", settings: "Paramètres",
    nodesOnline: "Nœuds en ligne", clients: "Appareils", wireless: "Appareils Wi-Fi",
    firmware: "Micrologiciel", refresh: "Actualiser", search: "Rechercher…",
    node: "Nœud", band: "Bande", ip: "Adresse IP", mac: "MAC", rate: "Débit",
    duration: "Durée", hostname: "Nom", wired: "Filaire", controller: "Principal",
    satellite: "Satellite", online: "En ligne", offline: "Hors ligne", cpu: "CPU",
    memory: "Mémoire", backhaul: "Backhaul", channel: "Canal", led: "LED",
    reboot: "Redémarrer", save: "Enregistrer", saving: "Enregistrement…",
    saved: "Paramètres appliqués", saveFailed: "Le routeur a refusé la modification",
    loading: "Chargement…", noDevices: "Aucun appareil", noChanges: "Rien à enregistrer",
    confirmReboot: "Redémarrer ce nœud ?", model: "Modèle", serial: "Numéro de série",
    uplink: "Liaison", network: "Réseau", wirelessSec: "Sans fil",
    system: "Système", security: "Sécurité", clientsOn: "Appareils sur ce nœud",
    error: "Erreur", retry: "Réessayer", applying: "Application en cours…",
    empty: "Aucun appareil sur ce nœud", collapse: "Fermer", expand: "Détails",
  },
  es: {
    about: "Acerca de",
    diagnostics: "Diagnóstico", target: "Dirección o nombre de host", run: "Ejecutar", running: "Ejecutando…", output: "Resultado", syslog: "Registro del sistema", reload: "Recargar", noOutput: "Sin resultado",
    uptime: "Tiempo activo",
    info: "Info", openMenu: "Abrir el menú lateral", showInfo: "Mostrar detalles", hideInfo: "Ocultar detalles",
    overview: "Resumen", nodes: "Nodos", devices: "Dispositivos", settings: "Ajustes",
    nodesOnline: "Nodos en línea", clients: "Dispositivos", wireless: "Dispositivos Wi-Fi",
    firmware: "Firmware", refresh: "Actualizar", search: "Buscar dispositivos…",
    node: "Nodo", band: "Banda", ip: "Dirección IP", mac: "MAC", rate: "Velocidad",
    duration: "Duración", hostname: "Nombre", wired: "Cableado", controller: "Principal",
    satellite: "Satélite", online: "En línea", offline: "Desconectado", cpu: "CPU",
    memory: "Memoria", backhaul: "Backhaul", channel: "Canal", led: "LED",
    reboot: "Reiniciar", save: "Guardar", saving: "Guardando…", saved: "Ajustes aplicados",
    saveFailed: "El router rechazó el cambio", loading: "Cargando…",
    noDevices: "No hay dispositivos", noChanges: "Nada que guardar",
    confirmReboot: "¿Reiniciar este nodo?", model: "Modelo", serial: "Número de serie",
    uplink: "Enlace", network: "Red", wirelessSec: "Inalámbrico",
    system: "Sistema", security: "Seguridad", clientsOn: "Dispositivos en este nodo",
    error: "Error", retry: "Reintentar", applying: "Aplicando…",
    empty: "Sin dispositivos en este nodo", collapse: "Cerrar", expand: "Detalles",
  },
};


// Descrizione delle funzionalità mostrata nella scheda Info. Segue la lingua
// di Home Assistant, con ricaduta sull'inglese.
const INFO = {
  en: {
    intro: "Brings a Cudy M3000 mesh system into Home Assistant and replaces the router's web interface for day-to-day administration. No cloud service, no Python dependencies: everything runs on your own machine.",
    features: [
      ["Mesh topology", "Every node is its own device, with the satellites nested under the controller: model, firmware, serial number, IP, MAC, backhaul and hop count."],
      ["Per-node monitoring", "Connected clients, CPU load, memory usage, link state, and the channel and bandwidth of each radio."],
      ["Router information", "The status panels of the router's home page: firmware, local time, uptime, mesh units, clients per band, SSID and LAN address."],
      ["Full configuration", "Every settings page the router exposes, grouped by category and read from the firmware's own form definitions."],
      ["Node administration", "LED on and off per node, and reboot, from the panel or from Home Assistant entities and services."],
      ["Diagnostics", "Ping, traceroute and nslookup run on the router itself, plus the system log."],
      ["Multilingual", "Labels come from the router, which is queried in the Home Assistant language."],
      ["Client tracking", "Optional and off by default: one device_tracker per client, with node, band, throughput and connection time."],
    ],
    licenseTitle: "License",
    license: "Apache License 2.0. Attribution to Marco Cavallo must not be removed from redistributions or derivative works.",
    disclaimer: "Not affiliated with, endorsed by, or supported by Shenzhen Cudy Technology Co., Ltd.",
  },
  it: {
    intro: "Porta un sistema mesh Cudy M3000 dentro Home Assistant e sostituisce l'interfaccia web del router nell'amministrazione quotidiana. Nessun servizio cloud, nessuna dipendenza Python: gira tutto sulla tua macchina.",
    features: [
      ["Topologia mesh", "Ogni nodo è un dispositivo a sé, con i satelliti annidati sotto il controller: modello, firmware, numero di serie, IP, MAC, backhaul e numero di hop."],
      ["Monitoraggio per nodo", "Client connessi, carico CPU, uso della memoria, stato del collegamento, canale e larghezza di banda di ciascuna radio."],
      ["Informazioni del router", "I riquadri di stato della home page del router: firmware, ora locale, tempo di accensione, unità mesh, client per banda, SSID e indirizzo LAN."],
      ["Configurazione completa", "Tutte le pagine di impostazioni che il router espone, raggruppate per categoria e lette dalle definizioni dei form del firmware."],
      ["Amministrazione dei nodi", "LED acceso e spento per nodo, e riavvio, dal pannello o dalle entità e dai servizi di Home Assistant."],
      ["Diagnostica", "Ping, traceroute e nslookup eseguiti sul router stesso, più il log di sistema."],
      ["Multilingua", "Le etichette le produce il router, che viene interrogato nella lingua di Home Assistant."],
      ["Tracciamento dei client", "Opzionale e disattivato di default: un device_tracker per client, con nodo, banda, throughput e durata della connessione."],
    ],
    licenseTitle: "Licenza",
    license: "Apache License 2.0. L'attribuzione a Marco Cavallo non va rimossa da ridistribuzioni o lavori derivati.",
    disclaimer: "Non affiliata, approvata o supportata da Shenzhen Cudy Technology Co., Ltd.",
  },
  de: {
    intro: "Holt ein Cudy-M3000-Mesh-System in Home Assistant und ersetzt die Weboberfläche des Routers im Alltag. Kein Cloud-Dienst, keine Python-Abhängigkeiten: alles läuft auf dem eigenen Rechner.",
    features: [
      ["Mesh-Topologie", "Jeder Knoten ist ein eigenes Gerät, die Satelliten hängen unter dem Controller: Modell, Firmware, Seriennummer, IP, MAC, Backhaul und Hop-Anzahl."],
      ["Überwachung je Knoten", "Verbundene Clients, CPU-Last, Speicherauslastung, Verbindungsstatus sowie Kanal und Bandbreite jedes Funkmoduls."],
      ["Router-Informationen", "Die Statusfelder der Router-Startseite: Firmware, Ortszeit, Laufzeit, Mesh-Einheiten, Clients je Band, SSID und LAN-Adresse."],
      ["Vollständige Konfiguration", "Alle Einstellungsseiten des Routers, nach Kategorie gruppiert und aus den Formulardefinitionen der Firmware gelesen."],
      ["Knotenverwaltung", "LED je Knoten ein- und ausschalten sowie Neustart, aus dem Panel oder über Entitäten und Dienste."],
      ["Diagnose", "Ping, Traceroute und Nslookup direkt auf dem Router, dazu das Systemprotokoll."],
      ["Mehrsprachig", "Die Beschriftungen liefert der Router, der in der Sprache von Home Assistant abgefragt wird."],
      ["Client-Verfolgung", "Optional und standardmäßig aus: ein device_tracker je Client, mit Knoten, Band, Durchsatz und Verbindungsdauer."],
    ],
    licenseTitle: "Lizenz",
    license: "Apache License 2.0. Die Namensnennung von Marco Cavallo darf in Weiterverbreitungen und abgeleiteten Werken nicht entfernt werden.",
    disclaimer: "Nicht mit Shenzhen Cudy Technology Co., Ltd. verbunden, von ihr unterstützt oder befürwortet.",
  },
  fr: {
    intro: "Amène un système maillé Cudy M3000 dans Home Assistant et remplace l'interface web du routeur au quotidien. Aucun service cloud, aucune dépendance Python : tout tourne sur votre machine.",
    features: [
      ["Topologie maillée", "Chaque nœud est un appareil distinct, les satellites rattachés au contrôleur : modèle, micrologiciel, numéro de série, IP, MAC, liaison et nombre de sauts."],
      ["Surveillance par nœud", "Clients connectés, charge processeur, mémoire utilisée, état du lien, canal et largeur de bande de chaque radio."],
      ["Informations du routeur", "Les encadrés d'état de la page d'accueil : micrologiciel, heure locale, temps de fonctionnement, unités maillées, clients par bande, SSID et adresse LAN."],
      ["Configuration complète", "Toutes les pages de réglages exposées par le routeur, groupées par catégorie et lues depuis les définitions de formulaires du micrologiciel."],
      ["Administration des nœuds", "Allumage et extinction de la LED par nœud, et redémarrage, depuis le panneau ou via les entités et services."],
      ["Diagnostic", "Ping, traceroute et nslookup exécutés sur le routeur, plus le journal système."],
      ["Multilingue", "Les libellés proviennent du routeur, interrogé dans la langue de Home Assistant."],
      ["Suivi des clients", "Optionnel et désactivé par défaut : un device_tracker par client, avec nœud, bande, débit et durée de connexion."],
    ],
    licenseTitle: "Licence",
    license: "Apache License 2.0. L'attribution à Marco Cavallo ne doit pas être retirée des redistributions ni des œuvres dérivées.",
    disclaimer: "Sans lien avec Shenzhen Cudy Technology Co., Ltd., ni approuvée ni soutenue par elle.",
  },
  es: {
    intro: "Trae un sistema mesh Cudy M3000 a Home Assistant y sustituye la interfaz web del router en la administración diaria. Sin servicios en la nube ni dependencias de Python: todo se ejecuta en tu propia máquina.",
    features: [
      ["Topología mesh", "Cada nodo es un dispositivo propio, con los satélites anidados bajo el controlador: modelo, firmware, número de serie, IP, MAC, enlace y saltos."],
      ["Supervisión por nodo", "Clientes conectados, carga de CPU, uso de memoria, estado del enlace, canal y ancho de banda de cada radio."],
      ["Información del router", "Los recuadros de estado de la página de inicio: firmware, hora local, tiempo encendido, unidades mesh, clientes por banda, SSID y dirección LAN."],
      ["Configuración completa", "Todas las páginas de ajustes que expone el router, agrupadas por categoría y leídas de las definiciones de formulario del firmware."],
      ["Administración de nodos", "Encender y apagar el LED por nodo, y reiniciar, desde el panel o mediante entidades y servicios."],
      ["Diagnóstico", "Ping, traceroute y nslookup ejecutados en el propio router, además del registro del sistema."],
      ["Multilingüe", "Las etiquetas las produce el router, consultado en el idioma de Home Assistant."],
      ["Seguimiento de clientes", "Opcional y desactivado por defecto: un device_tracker por cliente, con nodo, banda, rendimiento y duración."],
    ],
    licenseTitle: "Licencia",
    license: "Apache License 2.0. La atribución a Marco Cavallo no debe eliminarse de redistribuciones ni obras derivadas.",
    disclaimer: "Sin vinculación con Shenzhen Cudy Technology Co., Ltd., ni respaldada ni apoyada por ella.",
  },
};

const SECTION_KEY = {
  network: "network", wireless: "wirelessSec", system: "system", security: "security",
};

// -------------------------------------------------------------------- stili
const STYLES = `
:host {
  --cy-radius: 16px;
  --cy-gap: 16px;
  --cy-accent: #00b0a6;
  --cy-accent-2: #0e7490;
  --cy-amber: #ffb300;
  --cy-green: #43a047;
  --cy-red: #e53935;
  --cy-bg: var(--primary-background-color, #f5f6f8);
  --cy-card: var(--card-background-color, #fff);
  --cy-text: var(--primary-text-color, #212121);
  --cy-dim: var(--secondary-text-color, #6b7280);
  --cy-line: var(--divider-color, rgba(128,128,128,.22));
  display: block;
  background: var(--cy-bg);
  min-height: 100vh;
  color: var(--cy-text);
  font-family: var(--paper-font-body1_-_font-family, Roboto, system-ui, sans-serif);
}
* { box-sizing: border-box; }
button { font: inherit; }

.top {
  position: sticky; top: 0; z-index: 10;
  background: linear-gradient(135deg, #0e7490 0%, #00b0a6 62%, #4dd0c4 100%);
  color: #fff; padding: 18px var(--cy-gap) 18px;
  box-shadow: 0 2px 14px rgba(0,0,0,.18);
}
.top-row { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.brand { display: flex; align-items: baseline; gap: 10px; flex: 1; min-width: 200px; }
.brand h1 { margin: 0; font-size: 25px; font-weight: 600; letter-spacing: .2px; }
.badge {
  font-size: 12px; font-weight: 600; padding: 3px 9px; border-radius: 999px;
  background: rgba(255,255,255,.22); border: 1px solid rgba(255,255,255,.32);
}
.by { font-size: 13px; opacity: .9; }
.icon-btn {
  width: 40px; height: 40px; border-radius: 12px; cursor: pointer;
  display: grid; place-items: center; color: #fff;
  background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.26);
  transition: background .15s, transform .1s;
}
.icon-btn:hover { background: rgba(255,255,255,.3); }
.icon-btn:active { transform: scale(.93); }
.icon-btn.spin svg { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.stats { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px; }
.stat {
  background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.24);
  border-radius: 12px; padding: 10px 14px; min-width: 108px;
}
.stat .v { font-size: 23px; font-weight: 700; line-height: 1.15; }
.stat .l { font-size: 11px; text-transform: uppercase; letter-spacing: .6px; opacity: .88; }

.top.collapsed { padding-bottom: 12px; }
.stats[hidden] { display: none; }
.compact { display: flex; gap: 14px; margin-top: 9px; font-size: 13px; opacity: .95; flex-wrap: wrap; }
.compact b { font-size: 15px; }
.ghost {
  background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.26);
  color: #fff; border-radius: 10px; padding: 7px 12px; cursor: pointer; font-size: 13px;
}
.ghost:hover { background: rgba(255,255,255,.3); }
.tabs { display: flex; gap: 4px; margin-top: 14px; flex-wrap: wrap; }
.tab {
  border: 0; cursor: pointer; color: #fff; background: transparent;
  padding: 8px 15px; border-radius: 999px; font-size: 14px; font-weight: 500;
  opacity: .82; transition: background .15s, opacity .15s;
}
.tab:hover { background: rgba(255,255,255,.16); opacity: 1; }
.tab[aria-selected="true"] { background: rgba(255,255,255,.26); opacity: 1; font-weight: 600; }

.wrap { padding: var(--cy-gap); }
.grid { display: grid; gap: var(--cy-gap); grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }
.card {
  background: var(--cy-card); border-radius: var(--cy-radius);
  border: 1px solid var(--cy-line); padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.card.root { border-left: 5px solid var(--cy-accent); }
.card.info { border-left: 5px solid var(--cy-accent-2); }
.info-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.card.off { border-left: 5px solid var(--cy-red); }
.card h3 { margin: 0 0 2px; font-size: 17px; font-weight: 600; }
.sub { color: var(--cy-dim); font-size: 12.5px; }

.tag {
  display: inline-block; font-size: 11px; font-weight: 600; padding: 2px 8px;
  border-radius: 999px; background: rgba(128,128,128,.16); color: var(--cy-dim);
}
.tag.ok { background: rgba(67,160,71,.18); color: #2e7d32; }
.tag.bad { background: rgba(229,57,53,.18); color: #c62828; }
.tag.acc { background: rgba(0,176,166,.18); color: #00786f; }

.rowline { display: flex; justify-content: space-between; gap: 10px; padding: 5px 0; font-size: 13.5px; }
.rowline span:first-child { color: var(--cy-dim); }
.rowline span:last-child { font-weight: 500; text-align: right; word-break: break-word; }

.meter { height: 7px; border-radius: 999px; background: rgba(128,128,128,.2); overflow: hidden; margin-top: 5px; }
.meter i { display: block; height: 100%; border-radius: 999px; background: var(--cy-accent); transition: width .4s; }
.meter i.warn { background: var(--cy-amber); }
.meter i.hot { background: var(--cy-red); }

.actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px; }
.btn {
  border: 1px solid var(--cy-line); background: var(--cy-card); color: var(--cy-text);
  border-radius: 10px; padding: 8px 14px; cursor: pointer; font-size: 13.5px;
  transition: border-color .15s, background .15s, transform .1s;
}
.btn:hover { border-color: var(--cy-accent); }
.btn:active { transform: scale(.97); }
.btn.primary { background: var(--cy-accent); border-color: var(--cy-accent); color: #fff; font-weight: 600; }
.btn.primary:disabled { opacity: .5; cursor: not-allowed; }
.btn.danger:hover { border-color: var(--cy-red); color: var(--cy-red); }
.btn.on { border-color: var(--cy-green); color: #2e7d32; }

.bar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: var(--cy-gap); }
.search { flex: 1; min-width: 200px; position: relative; }
.search input {
  width: 100%; padding: 11px 14px 11px 38px; font-size: 15px;
  border-radius: 999px; border: 1px solid var(--cy-line);
  background: var(--cy-card); color: var(--cy-text); outline: none;
  transition: border-color .15s, box-shadow .15s;
}
.search input:focus { border-color: var(--cy-accent); box-shadow: 0 0 0 3px rgba(0,176,166,.16); }
.search svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); opacity: .5; }

table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.tablewrap { overflow-x: auto; border-radius: var(--cy-radius); border: 1px solid var(--cy-line); background: var(--cy-card); }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--cy-line); white-space: nowrap; }
th { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--cy-dim); font-weight: 600; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: rgba(128,128,128,.06); }

.diag-row { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
.diag-row input {
  flex: 1; min-width: 200px; padding: 10px 13px; font-size: 14px;
  border-radius: 10px; border: 1px solid var(--cy-line);
  background: var(--cy-bg); color: var(--cy-text); outline: none;
}
.diag-row input:focus { border-color: var(--cy-accent); }
.console {
  margin: 8px 0 0; padding: 13px 15px; border-radius: 11px;
  background: #10201f; color: #b8f0ea; border: 1px solid var(--cy-line);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12.5px; line-height: 1.55; max-height: 420px;
  overflow: auto; white-space: pre; tab-size: 4;
}
.pills { display: flex; gap: 7px; flex-wrap: wrap; margin-bottom: var(--cy-gap); }
.pill {
  border: 1px solid var(--cy-line); background: var(--cy-card); color: var(--cy-dim);
  border-radius: 999px; padding: 7px 15px; cursor: pointer; font-size: 13.5px;
  transition: border-color .15s, color .15s, background .15s;
}
.pill:hover { border-color: var(--cy-accent); color: var(--cy-text); }
.pill[aria-selected="true"] {
  background: var(--cy-accent); border-color: var(--cy-accent); color: #fff; font-weight: 600;
}
.fields { display: grid; gap: 0 26px; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); }
.section { margin-top: 16px; }
.section:first-of-type { margin-top: 4px; }
.section-head {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 10px 13px; border-radius: 11px; margin-bottom: 4px;
  background: rgba(0,176,166,.1); border: 1px solid rgba(0,176,166,.28);
  font-weight: 600; font-size: 14.5px;
}
.field.wide { grid-column: 1 / -1; }
.side { display: grid; grid-template-columns: 240px 1fr; gap: var(--cy-gap); align-items: start; }
@media (max-width: 820px) { .side { grid-template-columns: 1fr; } .brand h1 { font-size: 21px; } }
.menu { background: var(--cy-card); border: 1px solid var(--cy-line); border-radius: var(--cy-radius); overflow: hidden; }
.menu .grp { font-size: 11px; text-transform: uppercase; letter-spacing: .6px; color: var(--cy-dim); padding: 12px 14px 5px; font-weight: 600; }
.menu button {
  display: block; width: 100%; text-align: left; border: 0; background: transparent;
  color: var(--cy-text); padding: 9px 14px; cursor: pointer; font-size: 14px;
}
.menu button:hover { background: rgba(128,128,128,.09); }
.menu button[aria-current="true"] { background: rgba(0,176,166,.14); color: #00786f; font-weight: 600; }

.field { padding: 11px 0; border-bottom: 1px solid var(--cy-line); }
.field:last-child { border-bottom: 0; }
.field label { display: block; font-size: 13.5px; font-weight: 500; margin-bottom: 6px; }
.field .hint { font-size: 12px; color: var(--cy-dim); margin-top: 5px; line-height: 1.45; }
.field input[type=text], .field input[type=password], .field select, .field textarea {
  width: 100%; padding: 9px 11px; font-size: 14px; border-radius: 9px;
  border: 1px solid var(--cy-line); background: var(--cy-bg); color: var(--cy-text); outline: none;
}
.field input:focus, .field select:focus { border-color: var(--cy-accent); }
.switch { position: relative; display: inline-block; width: 46px; height: 26px; vertical-align: middle; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute; inset: 0; cursor: pointer; border-radius: 999px;
  background: rgba(128,128,128,.35); transition: background .2s;
}
.slider::before {
  content: ""; position: absolute; height: 20px; width: 20px; left: 3px; top: 3px;
  background: #fff; border-radius: 50%; transition: transform .2s;
}
.switch input:checked + .slider { background: var(--cy-accent); }
.switch input:checked + .slider::before { transform: translateX(20px); }

.note { background: rgba(0,176,166,.1); border: 1px solid rgba(0,176,166,.3); border-radius: 10px; padding: 10px 12px; font-size: 13px; margin-bottom: 12px; line-height: 1.5; }
.toast {
  position: fixed; left: 50%; bottom: 26px; transform: translateX(-50%);
  background: #263238; color: #fff; padding: 11px 18px; border-radius: 10px;
  font-size: 14px; box-shadow: 0 6px 22px rgba(0,0,0,.3); z-index: 50;
}
.toast.bad { background: var(--cy-red); }
.foot {
  padding: 4px var(--cy-gap) 30px; text-align: center;
  color: var(--cy-dim); font-size: 12.5px;
}
.empty { text-align: center; color: var(--cy-dim); padding: 42px 16px; font-size: 14px; }
.spinner { width: 26px; height: 26px; border: 3px solid var(--cy-line); border-top-color: var(--cy-accent); border-radius: 50%; animation: spin .9s linear infinite; margin: 30px auto; }
`;

const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const ICON_SEARCH = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>`;
const ICON_MENU = `<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M3 6h18v2H3V6m0 5h18v2H3v-2m0 5h18v2H3v-2Z"/></svg>`;
const ICON_REFRESH = `<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/></svg>`;

// Il firmware espone sia `model` ("M3000") sia `hardware` ("M3000 V1.0"):
// il secondo contiene già il primo, quindi concatenarli è solo rumore.
function fmtModel(model, hardware) {
  if (!hardware) return model || "";
  if (!model) return hardware;
  return hardware.startsWith(model) ? hardware : `${model} ${hardware}`;
}

function fmtUptime(seconds, lang) {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const unit = { it: ["g", "h", "min"], en: ["d", "h", "min"], de: ["T", "Std", "Min"],
                 fr: ["j", "h", "min"], es: ["d", "h", "min"] }[lang] || ["d", "h", "min"];
  if (d) return `${d}${unit[0]} ${h}${unit[1]}`;
  if (h) return `${h}${unit[1]} ${m}${unit[2]}`;
  return `${m}${unit[2]}`;
}

function fmtRate(kbps) {
  if (kbps === null || kbps === undefined) return "—";
  if (kbps >= 1000) return (kbps / 1000).toFixed(2) + " Mbps";
  return kbps.toFixed(2) + " Kbps";
}

class CudyM3000Panel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._data = null;
    this._pages = [];
    this._tab = "overview";
    this._activePage = null;
    this._pageSchema = null;
    this._changes = {};
    this._filter = "";
    this._expanded = new Set();
    this._busy = false;
    this._timer = null;
    this._error = null;
    // Su schermi stretti le tile mangiano tutta la prima schermata.
    let saved = null;
    try { saved = localStorage.getItem("cudy_stats_open"); } catch (e) { /* modalità privata */ }
    this._statsOpen = saved === null ? window.innerWidth > 760 : saved === "1";
    this._diag = { tool: "ping", target: "", output: "", running: false };
    this._syslog = "";
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._boot();
  }

  connectedCallback() {
    this.shadowRoot.innerHTML = `<style>${STYLES}</style><div id="root"></div>`;
    if (this._hass && !this._data) this._boot();
    this._timer = setInterval(() => this._load(true), 15000);
  }

  disconnectedCallback() {
    if (this._timer) clearInterval(this._timer);
    this._timer = null;
  }

  get _lang() {
    const raw = (this._hass && this._hass.language) || "en";
    if (I18N[raw]) return raw;
    const base = raw.split("-")[0];
    return I18N[base] ? base : "en";
  }

  _t(key) {
    return (I18N[this._lang] && I18N[this._lang][key]) || I18N.en[key] || key;
  }

  async _ws(type, extra = {}) {
    return this._hass.callWS({ type: `${DOMAIN}/${type}`, ...extra });
  }

  async _boot() {
    await this._load();
    try {
      const res = await this._ws("pages");
      this._pages = res.pages || [];
    } catch (err) {
      this._pages = [];
    }
    this._render();
  }

  async _load(silent = false) {
    try {
      this._data = await this._ws("overview");
      this._error = null;
    } catch (err) {
      this._error = err && err.message ? err.message : String(err);
    }
    if (!silent || this._error) this._render();
    else this._render();
  }

  _toast(text, bad = false) {
    const old = this.shadowRoot.querySelector(".toast");
    if (old) old.remove();
    const el = document.createElement("div");
    el.className = "toast" + (bad ? " bad" : "");
    el.textContent = text;
    this.shadowRoot.appendChild(el);
    setTimeout(() => el.remove(), 3600);
  }

  // ------------------------------------------------------------- rendering
  _render() {
    const root = this.shadowRoot.querySelector("#root");
    if (!root) return;

    if (!this._data) {
      root.innerHTML = this._error
        ? `<div class="wrap"><div class="card"><b>${esc(this._t("error"))}</b><p class="sub">${esc(this._error)}</p></div></div>`
        : `<div class="spinner"></div>`;
      return;
    }

    const d = this._data.integration || {};
    const foot = `<div class="foot">${esc(d.name || "Cudy M3000")} v${esc(d.version || "")} \u2014 By ${esc(d.author || "Marco Cavallo")} \u00b7 Apache-2.0</div>`;
    root.innerHTML = this._header() + `<div class="wrap">${this._body()}</div>` + foot;
    this._wire();
  }

  _header() {
    const d = this._data;
    const t = (k) => esc(this._t(k));
    const tabs = this._tabs()
      .map((x) => `<button class="tab" data-tab="${esc(x.id)}" aria-selected="${this._tab === x.id}">${esc(x.label)}</button>`)
      .join("");

    const d2 = this._data;
    return `
<div class="top${this._statsOpen ? "" : " collapsed"}">
  <div class="top-row">
    <button class="icon-btn" id="menu" title="${t("openMenu")}" aria-label="${t("openMenu")}">${ICON_MENU}</button>
    <div class="brand">
      <h1>Cudy M3000</h1>
      <span class="badge">v${esc(d.integration.version)}</span>
      <span class="by">By ${esc(d.integration.author || "Marco Cavallo")}</span>
    </div>
    <button class="ghost" id="stats-toggle" title="${this._statsOpen ? t("hideInfo") : t("showInfo")}">${this._statsOpen ? "\u25B2" : "\u25BC"} ${t("info")}</button>
    <button class="icon-btn${this._busy ? " spin" : ""}" id="refresh" title="${t("refresh")}">${ICON_REFRESH}</button>
  </div>
  ${this._statsOpen ? "" : `<div class="compact">
    <span><b>${d2.totals.nodes_online}/${d2.totals.nodes}</b> ${t("nodesOnline")}</span>
    <span><b>${d2.totals.clients}</b> ${t("clients")}</span>
    <span>${esc(d2.system.firmware || "")}</span>
  </div>`}
  <div class="stats"${this._statsOpen ? "" : " hidden"}>
    <div class="stat"><div class="v">${d.totals.nodes_online}/${d.totals.nodes}</div><div class="l">${t("nodesOnline")}</div></div>
    <div class="stat"><div class="v">${d.totals.clients}</div><div class="l">${t("clients")}</div></div>
    <div class="stat"><div class="v">${d.totals.clients_wireless}</div><div class="l">${t("wireless")}</div></div>
    <div class="stat"><div class="v" style="font-size:17px;padding-top:5px">${esc(d.system.firmware || "\u2014")}</div><div class="l">${t("firmware")}</div></div>
  </div>
  <div class="tabs">${tabs}</div>
</div>`;
  }

  // L'ordine delle categorie è quello in cui hanno senso per chi amministra
  // il router, non quello in cui il firmware le restituisce.
  _sections() {
    const order = ["network", "wireless", "security", "system"];
    const present = new Set(this._pages.map((p) => p.section));
    return order.filter((s) => present.has(s));
  }

  _tabs() {
    const t = (k) => this._t(k);
    return [
      { id: "overview", label: t("overview") },
      { id: "nodes", label: t("nodes") },
      { id: "devices", label: t("devices") },
      ...this._sections().map((s) => ({
        id: `sec:${s}`, label: t(SECTION_KEY[s] || s),
      })),
      { id: "diagnostics", label: t("diagnostics") },
      { id: "about", label: t("about") },
    ];
  }

  _body() {
    if (this._tab.startsWith("sec:")) return this._viewSection(this._tab.slice(4));
    switch (this._tab) {
      case "nodes": return this._viewNodes();
      case "devices": return this._viewDevices();
      case "diagnostics": return this._viewDiagnostics();
      case "about": return this._viewAbout();
      default: return this._viewOverview();
    }
  }

  // Una sola scheda per tutti i nodi: prima il controller aveva la tabella
  // completa e i satelliti due righe, e sembrava che di loro non si sapesse
  // nulla. Le informazioni ci sono tutte, vanno solo mostrate.
  _nodeCard(n, extra = "") {
    const t = (k) => esc(this._t(k));
    const row = (label, value) =>
      value === null || value === undefined || value === ""
        ? ""
        : `<div class="rowline"><span>${label}</span><span>${esc(value)}</span></div>`;

    const radios = Object.entries(n.radios || {})
      .filter(([, r]) => r.channel)
      .map(([key, r]) =>
        row(`${t("channel")} ${key === "radio0" ? "2.4G" : "5G"}`,
            `${r.channel}${r.bandwidth ? " \u00b7 " + r.bandwidth : ""}`))
      .join("");

    const uplink = [n.backhaul, n.uplink_iface].filter(Boolean).join(" \u00b7 ");

    return `
<div class="card ${n.is_root ? "root" : ""} ${n.online ? "" : "off"}">
  <div class="info-head">
    <div>
      <h3>${esc(n.name)}</h3>
      <div class="sub">${n.is_root ? t("controller") : t("satellite")}</div>
    </div>
    <span class="tag ${n.online ? "ok" : "bad"}">${n.online ? t("online") : t("offline")}</span>
  </div>
  <div style="margin-top:11px">
    ${row(t("ip"), n.ip)}
    ${row(t("mac"), n.mac)}
    ${row(t("model"), fmtModel(n.model, n.hardware))}
    ${row(t("firmware"), n.firmware)}
    ${row(t("serial"), n.serial)}
    ${row(t("backhaul"), uplink)}
    ${n.hop !== null && n.hop !== undefined && !n.is_root ? row(t("uplink"), `hop ${n.hop}`) : ""}
    ${row(t("clients"), n.clients ?? 0)}
    ${radios}
    <div class="rowline"><span>${t("cpu")}</span><span>${n.cpu_load ?? "\u2014"}%</span></div>
    ${this._meter(n.cpu_load)}
    <div class="rowline" style="margin-top:7px"><span>${t("memory")}</span><span>${n.memory_load ?? "\u2014"}%</span></div>
    ${this._meter(n.memory_load)}
    ${extra}
  </div>
</div>`;
  }

  _viewOverview() {
    const d = this._data;
    const t = (k) => esc(this._t(k));

    // Riquadri informativi presi dalla pagina di stato del router: titoli ed
    // etichette arrivano già tradotti, quindi si mostrano così come sono.
    const status = (d.status || []).map((p) => `
<div class="card info">
  <div class="info-head">
    <h3>${esc(p.title)}</h3>
    ${p.headline && p.headline.value
      ? `<span class="tag ${p.headline.ok ? "ok" : ""}">${esc(p.headline.value)}</span>` : ""}
  </div>
  ${p.headline && p.headline.label
    ? `<div class="sub">${esc(p.headline.label)}</div>` : ""}
  <div style="margin-top:10px">
    ${(p.rows || []).map((r) =>
      `<div class="rowline"><span>${esc(r.label)}</span><span>${esc(r.value)}</span></div>`).join("")}
  </div>
</div>`).join("");

    const root = d.nodes.find((n) => n.is_root);
    const sats = d.nodes.filter((n) => !n.is_root);
    const uptimeRow = d.uptime
      ? `<div class="rowline"><span>${t("uptime")}</span><span>${esc(fmtUptime(d.uptime, this._lang))}</span></div>`
      : "";

    const cards = [
      root ? this._nodeCard(root, uptimeRow) : "",
      ...sats.map((n) => this._nodeCard(n)),
    ].join("");

    return `<div class="grid">${cards}${status}</div>`;
  }

  _meter(value) {
    const v = Math.max(0, Math.min(100, Number(value) || 0));
    const cls = v >= 85 ? "hot" : v >= 60 ? "warn" : "";
    return `<div class="meter"><i class="${cls}" style="width:${v}%"></i></div>`;
  }

  _viewNodes() {
    const t = (k) => esc(this._t(k));
    return `<div class="grid">${this._data.nodes.map((n) => {
      const open = this._expanded.has(n.id);
      const clients = this._data.clients.filter((c) => c.node_id === n.id);
      const radios = Object.entries(n.radios || {})
        .map(([key, r]) => `<div class="rowline"><span>${t("channel")} ${key === "radio0" ? "2.4G" : "5G"}</span><span>${esc(r.channel)} · ${esc(r.bandwidth || "")}</span></div>`)
        .join("");

      const list = open ? `
<div style="margin-top:12px;border-top:1px solid var(--cy-line);padding-top:10px">
  <div class="sub" style="margin-bottom:6px">${t("clientsOn")}</div>
  ${clients.length ? clients.map((c) => `
    <div class="rowline"><span>${esc(c.hostname)} <span class="tag">${esc(c.band || t("wired"))}</span></span><span>${esc(c.ip)}</span></div>`).join("")
      : `<div class="sub">${t("empty")}</div>`}
</div>` : "";

      return `
<div class="card ${n.is_root ? "root" : ""} ${n.online ? "" : "off"}">
  <div style="display:flex;justify-content:space-between;align-items:start;gap:8px">
    <div>
      <h3>${esc(n.name)}</h3>
      <div class="sub">${n.is_root ? t("controller") : t("satellite")} · ${esc(n.ip || "")} · ${esc(n.mac || "")}</div>
    </div>
    <span class="tag ${n.online ? "ok" : "bad"}">${n.online ? t("online") : t("offline")}</span>
  </div>

  <div style="margin-top:12px">
    <div class="rowline"><span>${t("cpu")}</span><span>${n.cpu_load ?? "—"}%</span></div>
    ${this._meter(n.cpu_load)}
    <div class="rowline" style="margin-top:8px"><span>${t("memory")}</span><span>${n.memory_load ?? "—"}%</span></div>
    ${this._meter(n.memory_load)}
    <div class="rowline" style="margin-top:8px"><span>${t("clients")}</span><span>${n.clients ?? 0}</span></div>
    <div class="rowline"><span>${t("backhaul")}</span><span>${esc(n.backhaul || "—")}</span></div>
    ${radios}
    <div class="rowline"><span>${t("firmware")}</span><span>${esc(n.firmware || "—")}</span></div>
  </div>

  <div class="actions">
    <button class="btn ${n.led_on ? "on" : ""}" data-led="${esc(n.id)}" data-on="${n.led_on ? "0" : "1"}">${t("led")} ${n.led_on ? "ON" : "OFF"}</button>
    <button class="btn danger" data-reboot="${esc(n.id)}">${t("reboot")}</button>
    <button class="btn" data-toggle="${esc(n.id)}">${open ? t("collapse") : t("expand")}</button>
  </div>
  ${list}
</div>`;
    }).join("")}</div>`;
  }

  _viewDevices() {
    const t = (k) => esc(this._t(k));
    const q = this._filter.trim().toLowerCase();
    const nodes = {};
    this._data.nodes.forEach((n) => { nodes[n.id] = n.name; });

    const rows = this._data.clients.filter((c) => {
      if (!q) return true;
      return [c.hostname, c.ip, c.mac, nodes[c.node_id], c.band]
        .some((v) => String(v || "").toLowerCase().includes(q));
    });

    const body = rows.length ? rows.map((c) => `
<tr>
  <td><b>${esc(c.hostname)}</b></td>
  <td>${esc(nodes[c.node_id] || c.node_id)}</td>
  <td><span class="tag ${c.wired ? "" : "acc"}">${esc(c.band || t("wired"))}</span></td>
  <td>${esc(c.ip)}</td>
  <td style="font-family:ui-monospace,monospace;font-size:12.5px">${esc(c.mac)}</td>
  <td>↑ ${esc(fmtRate(c.tx_kbps))}<br>↓ ${esc(fmtRate(c.rx_kbps))}</td>
  <td>${esc(c.duration)}</td>
</tr>`).join("") : `<tr><td colspan="7"><div class="empty">${t("noDevices")}</div></td></tr>`;

    return `
<div class="bar">
  <div class="search">${ICON_SEARCH}<input id="filter" type="text" placeholder="${t("search")}" value="${esc(this._filter)}"></div>
  <span class="tag">${rows.length} / ${this._data.clients.length}</span>
</div>
<div class="tablewrap"><table>
  <thead><tr>
    <th>${t("hostname")}</th><th>${t("node")}</th><th>${t("band")}</th>
    <th>${t("ip")}</th><th>${t("mac")}</th><th>${t("rate")}</th><th>${t("duration")}</th>
  </tr></thead>
  <tbody>${body}</tbody>
</table></div>`;
  }

  // Il testo segue la lingua di Home Assistant; l'attribuzione e la licenza
  // fanno parte dell'integrazione e non vanno rimosse.
  _info() {
    return INFO[this._lang] || INFO.en;
  }

  _viewAbout() {
    const info = this._info();
    const d = this._data.integration || {};

    return `
<div class="card">
  <div class="info-head">
    <div>
      <h3>${esc(d.name || "Cudy M3000")}</h3>
      <div class="sub">v${esc(d.version || "?")} \u00b7 By ${esc(d.author || "Marco Cavallo")}</div>
    </div>
    <span class="tag acc">${esc(d.host || "")}</span>
  </div>
  <p style="margin:12px 0 0;line-height:1.6;font-size:14px">${esc(info.intro)}</p>
</div>

<div class="grid" style="margin-top:var(--cy-gap)">
  ${info.features.map(([title, text]) => `
  <div class="card">
    <h3 style="font-size:15px">${esc(title)}</h3>
    <p style="margin:7px 0 0;line-height:1.6;font-size:13.5px;color:var(--cy-dim)">${esc(text)}</p>
  </div>`).join("")}
</div>

<div class="card" style="margin-top:var(--cy-gap)">
  <h3 style="font-size:15px">${esc(info.licenseTitle)}</h3>
  <p style="margin:7px 0 0;line-height:1.6;font-size:13.5px">${esc(info.license)}</p>
  <p style="margin:9px 0 0;line-height:1.6;font-size:12.5px;color:var(--cy-dim)">
    Copyright 2026 Marco Cavallo \u00b7 ${esc(info.disclaimer)}
  </p>
</div>`;
  }

  _viewDiagnostics() {
    const t = (k) => esc(this._t(k));
    const tools = ["ping", "traceroute", "nslookup"];
    const d = this._diag;

    return `
<div class="card">
  <h3>${t("diagnostics")}</h3>
  <div class="pills" style="margin-top:12px">
    ${tools.map((x) => `<button class="pill" data-tool="${x}" aria-selected="${d.tool === x}">${x}</button>`).join("")}
  </div>
  <div class="diag-row">
    <input id="diag-target" type="text" placeholder="${t("target")}" value="${esc(d.target)}">
    <button class="btn primary" id="diag-run" ${d.running || !d.target.trim() ? "disabled" : ""}>${d.running ? t("running") : t("run")}</button>
  </div>
  ${d.output || d.running ? `
    <div class="sub" style="margin-top:14px">${t("output")}</div>
    <pre class="console">${esc(d.output || "\u2026")}</pre>` : ""}
</div>

<div class="card" style="margin-top:var(--cy-gap)">
  <div class="info-head">
    <h3>${t("syslog")}</h3>
    <button class="btn" id="syslog-load">${t("reload")}</button>
  </div>
  ${this._syslog
    ? `<pre class="console">${esc(this._syslog)}</pre>`
    : `<div class="empty">${t("noOutput")}</div>`}
</div>`;
  }

  _viewSection(section) {
    const pages = this._pages.filter((p) => p.section === section);
    if (!pages.length) {
      return `<div class="card"><div class="empty">${esc(this._t("loading"))}</div></div>`;
    }

    const active = pages.some((p) => p.key === this._activePage)
      ? this._activePage
      : pages[0].key;
    if (active !== this._activePage) {
      this._activePage = active;
      this._changes = {};
      this._loadPage(active);
    }

    const pills = pages.map((p) => `
      <button class="pill" data-page="${esc(p.key)}" aria-selected="${p.key === active}">${esc(p.title || p.key)}</button>`).join("");

    return `<div class="pills">${pills}</div>${this._renderForm()}`;
  }

  async _loadPage(key) {
    try {
      const schema = await this._ws("page", { key });
      if (this._activePage === key) {
        this._pageSchema = schema;
        this._render();
      }
    } catch (err) {
      this._toast(`${this._t("error")}: ${err.message || err}`, true);
    }
  }

  // Un campo è visibile se almeno una delle alternative è soddisfatta.
  _visible(field) {
    if (!field.depends || !field.depends.length) return true;
    return field.depends.some((alt) =>
      Object.entries(alt).every(([name, want]) => String(this._current(name)) === String(want)));
  }

  _current(name) {
    if (name in this._changes) {
      const v = this._changes[name];
      return v === true ? "1" : v === false ? "0" : v;
    }
    const all = this._allFields();
    const f = all.find((x) => x.name === name);
    if (!f) return "";
    return f.value === true ? "1" : f.value === false ? "0" : f.value;
  }

  _allFields() {
    if (!this._pageSchema) return [];
    const out = [...(this._pageSchema.fields || [])];
    (this._pageSchema.tables || []).forEach((tb) =>
      tb.rows.forEach((r) =>
        Object.values(r.cells).forEach((c) => { if (c && c.name) out.push(c); })));
    return out;
  }

  _renderForm() {
    const t = (k) => esc(this._t(k));
    if (!this._activePage) {
      return `<div class="card"><div class="empty">${t("settings")}</div></div>`;
    }
    if (!this._pageSchema || this._pageSchema.key !== this._activePage) {
      return `<div class="card"><div class="spinner"></div></div>`;
    }

    const s = this._pageSchema;
    const notes = (s.notes || []).map((n) => `<div class="note">${esc(n)}</div>`).join("");

    const fields = this._renderFields(s.fields || []);

    const tables = (s.tables || []).map((tb) => `
<div class="tablewrap" style="margin-top:12px">
  <table>
    <thead><tr>${tb.columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
    <tbody>${tb.rows.map((r) => `<tr>${Object.values(r.cells).map((c) =>
      `<td>${c && c.name ? this._renderWidget(c, true) : esc(c ? c.value : "")}</td>`).join("")}</tr>`).join("")}</tbody>
  </table>
</div>`).join("");

    const dirty = Object.keys(this._changes).length > 0;
    return `
<div class="card">
  <h3>${esc(s.title)}</h3>
  <div class="sub" style="margin-bottom:10px">${esc(s.path)}</div>
  ${notes}
  <div class="fields">${fields}</div>
  ${tables}
  <div class="actions">
    <button class="btn primary" id="save" ${dirty ? "" : "disabled"}>${dirty ? t("save") : t("noChanges")}</button>
  </div>
</div>`;
  }

  // Alcune pagine (il wireless) contengono più sezioni UCI indipendenti:
  // 2.4G e 5G. Vanno separate visivamente, altrimenti sono 26 campi in fila
  // e non si capisce a quale radio appartiene cosa.
  _renderFields(all) {
    const usable = all.filter((f) => f.kind !== "mirror");
    const order = [];
    const bySection = new Map();
    usable.forEach((f) => {
      const key = f.section || "";
      if (!bySection.has(key)) { bySection.set(key, []); order.push(key); }
      bySection.get(key).push(f);
    });

    // L'intestazione ha senso solo se ogni sezione si apre con un interruttore
    // di abilitazione: il suo nome è leggibile, l'id UCI no.
    const grouped =
      order.length > 1 &&
      order.every((k) => (bySection.get(k)[0] || {}).kind === "flag");

    if (!grouped) {
      return `<div class="fields">${usable.map((f) => this._renderField(f)).join("")}</div>`;
    }

    return order.map((key) => {
      const [head, ...rest] = bySection.get(key);
      const visible = rest.filter((f) => this._visible(f));
      return `
<div class="section">
  <div class="section-head">
    <span>${esc(head.label)}</span>
    ${this._renderWidget(head)}
  </div>
  <div class="fields">${visible.map((f) => this._renderField(f)).join("")}</div>
</div>`;
    }).join("");
  }

  _renderField(f) {
    if (!this._visible(f)) return "";
    return `
<div class="field">
  <label for="${esc(f.name)}">${esc(f.label)}</label>
  ${this._renderWidget(f)}
  ${f.help ? `<div class="hint">${esc(f.help)}</div>` : ""}
</div>`;
  }

  _renderWidget(f, compact = false) {
    const value = this._current(f.name);
    const dis = f.editable === false ? "disabled" : "";

    if (f.kind === "flag") {
      const on = String(value) === "1" || value === true;
      return `<label class="switch"><input type="checkbox" data-field="${esc(f.name)}" ${on ? "checked" : ""} ${dis}><span class="slider"></span></label>`;
    }
    if (f.kind === "select" || f.kind === "radio") {
      return `<select data-field="${esc(f.name)}" ${dis}>${
        (f.options || []).map((o) =>
          `<option value="${esc(o.value)}" ${String(o.value) === String(value) ? "selected" : ""}>${esc(o.label || o.value)}</option>`).join("")
      }</select>`;
    }
    if (f.kind === "textarea") {
      return `<textarea rows="4" data-field="${esc(f.name)}" ${dis}>${esc(value)}</textarea>`;
    }
    const type = f.kind === "password" ? "password" : "text";
    return `<input type="${type}" data-field="${esc(f.name)}" value="${esc(value)}" ${dis} ${compact ? 'style="min-width:130px"' : ""}>`;
  }

  // ------------------------------------------------------------------ eventi
  _wire() {
    const $ = (sel) => this.shadowRoot.querySelector(sel);
    const $$ = (sel) => Array.from(this.shadowRoot.querySelectorAll(sel));

    $$(".tab").forEach((el) => el.addEventListener("click", () => {
      this._tab = el.dataset.tab;
      this._render();
    }));

    const menu = $("#menu");
    if (menu) menu.addEventListener("click", () => {
      // Evento standard di Home Assistant: la shell apre la barra laterale.
      this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
    });

    const statsToggle = $("#stats-toggle");
    if (statsToggle) statsToggle.addEventListener("click", () => {
      this._statsOpen = !this._statsOpen;
      try { localStorage.setItem("cudy_stats_open", this._statsOpen ? "1" : "0"); }
      catch (e) { /* storage non disponibile */ }
      this._render();
    });

    const refresh = $("#refresh");
    if (refresh) refresh.addEventListener("click", async () => {
      this._busy = true; this._render();
      try { await this._ws("refresh"); } catch (e) { /* mostrato sotto */ }
      await this._load();
      this._busy = false; this._render();
    });

    const filter = $("#filter");
    if (filter) {
      filter.addEventListener("input", () => {
        this._filter = filter.value;
        const pos = filter.selectionStart;
        this._render();
        const again = this.shadowRoot.querySelector("#filter");
        if (again) { again.focus(); again.setSelectionRange(pos, pos); }
      });
    }

    $$("[data-toggle]").forEach((el) => el.addEventListener("click", () => {
      const id = el.dataset.toggle;
      if (this._expanded.has(id)) this._expanded.delete(id);
      else this._expanded.add(id);
      this._render();
    }));

    $$("[data-led]").forEach((el) => el.addEventListener("click", async () => {
      const wanted = el.dataset.on === "1";
      el.disabled = true;
      el.textContent = `${this._t("led")} \u2026`;
      // Aggiorna subito la vista locale: il router impiega un attimo e senza
      // questo il pulsante sembra non aver fatto nulla.
      const node = this._data.nodes.find((n) => n.id === el.dataset.led);
      if (node) node.led_on = wanted;
      await this._action(el.dataset.led, wanted ? "led_on" : "led_off");
    }));

    $$("[data-reboot]").forEach((el) => el.addEventListener("click", async () => {
      if (!confirm(this._t("confirmReboot"))) return;
      el.disabled = true;
      this._toast(this._t("applying"));
      await this._action(el.dataset.reboot, "reboot");
    }));

    $$("[data-page]").forEach((el) => el.addEventListener("click", () => {
      if (el.dataset.page === this._activePage) return;
      this._activePage = el.dataset.page;
      this._pageSchema = null;
      this._changes = {};
      this._render();
      this._loadPage(this._activePage);
    }));

    $$("[data-field]").forEach((el) => {
      const name = el.dataset.field;
      const handler = () => {
        this._changes[name] = el.type === "checkbox" ? (el.checked ? "1" : "0") : el.value;
        this._render();
      };
      el.addEventListener(el.tagName === "SELECT" || el.type === "checkbox" ? "change" : "input", handler);
    });

    $$("[data-tool]").forEach((el) => el.addEventListener("click", () => {
      this._diag.tool = el.dataset.tool;
      this._diag.output = "";
      this._render();
    }));

    const target = $("#diag-target");
    if (target) {
      // Non ri-renderizzo a ogni tasto: perderei il fuoco nel campo.
      target.addEventListener("input", () => {
        this._diag.target = target.value;
        const run = this.shadowRoot.querySelector("#diag-run");
        if (run) run.disabled = this._diag.running || !target.value.trim();
      });
      target.addEventListener("keydown", (ev) => {
        if (ev.key !== "Enter") return;
        const run = this.shadowRoot.querySelector("#diag-run");
        if (run && !run.disabled) run.click();
      });
    }

    const runBtn = $("#diag-run");
    if (runBtn) runBtn.addEventListener("click", async () => {
      this._diag.running = true;
      this._diag.output = "";
      this._render();
      try {
        const res = await this._ws("diagnostic", {
          tool: this._diag.tool, target: this._diag.target,
        });
        this._diag.output = res.output || this._t("noOutput");
      } catch (err) {
        this._diag.output = `${this._t("error")}: ${err.message || err}`;
      }
      this._diag.running = false;
      this._render();
    });

    const syslogBtn = $("#syslog-load");
    if (syslogBtn) syslogBtn.addEventListener("click", async () => {
      syslogBtn.disabled = true;
      syslogBtn.textContent = this._t("loading");
      try {
        const res = await this._ws("syslog", { lines: 300 });
        this._syslog = res.output || "";
      } catch (err) {
        this._toast(`${this._t("error")}: ${err.message || err}`, true);
      }
      this._render();
    });

    const save = $("#save");
    if (save) save.addEventListener("click", async () => {
      save.disabled = true;
      save.textContent = this._t("saving");
      try {
        const res = await this._ws("save", { key: this._activePage, changes: this._changes });
        if (res.ok) {
          this._toast(this._t("saved"));
          this._changes = {};
          await this._loadPage(this._activePage);
        } else {
          this._toast(this._t("saveFailed"), true);
        }
      } catch (err) {
        this._toast(`${this._t("error")}: ${err.message || err}`, true);
      }
      await this._load();
    });
  }

  async _action(nodeId, action) {
    try {
      await this._ws("node_action", { node_id: nodeId, action });
    } catch (err) {
      this._toast(`${this._t("error")}: ${err.message || err}`, true);
    }
    await this._load();
  }
}

customElements.define("cudy-m3000-panel", CudyM3000Panel);
