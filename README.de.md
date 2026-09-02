# Cudy M3000

[English](README.md) · [Italiano](README.it.md) · [Français](README.fr.md) · **Deutsch** · [Español](README.es.md)

*Home-Assistant-Integration für Cudy-M3000-Mesh-WLAN-Systeme.*

*By Marco Cavallo*

---

## Was es ist

Eine Integration, die im lokalen Netz mit einem Cudy-M3000-Mesh-System spricht und es in Home Assistant holt: jeder Knoten als eigenes Gerät, die verbundenen Clients, die Statusseiten des Routers und ein Seitenleisten-Panel, das die Weboberfläche des Routers im Alltag ersetzt.

Cudy veröffentlicht keine API. Die Integration meldet sich an der LuCI-Oberfläche der Firmware an und liest dieselben Endpunkte wie die Weboberfläche, einschließlich des JSON-Feeds hinter der Mesh-Topologieseite. Kein Cloud-Dienst, keine Python-Abhängigkeiten: alles läuft auf dem eigenen Rechner.

## Was es kann

**Mesh-Topologie**  
Jeder Knoten wird ein Home-Assistant-Gerät, die Satelliten hängen unter dem Controller. Modell, Hardwarerevision, Firmware, Seriennummer, IP, MAC, Backhaul-Typ und Hop-Anzahl kommen vom Router.

**Überwachung je Knoten**  
Verbundene Clients, CPU-Last, Speicherauslastung, Verbindungsstatus sowie Kanal und Bandbreite jedes Funkmoduls.

**Router-Informationen**  
Die Statusfelder der Router-Startseite: Firmware und Region, Ortszeit, Laufzeit, Anzahl der Mesh-Einheiten, Clients nach Band getrennt, SSID und Kanal, LAN-Adresse.

**Vollständige Konfiguration**  
Alle Einstellungsseiten des Routers, nach Kategorie gruppiert und aus den Formulardefinitionen der Firmware erzeugt: LAN, WAN, IGMP, IPTV/VLAN, Wake-on-LAN, Captive Portal, WLAN, WLAN-Zeitplan, WPS, lokale Verwaltung, Administratorkonto, Systemzeit, Zeitzone, Sprache, LED-Steuerung, zeitgesteuerter Neustart, automatische Firmware-Aktualisierung und Betriebsmodus.

**Knotenverwaltung**  
LED je Knoten ein- und ausschalten sowie Neustart, aus dem Panel oder über Home-Assistant-Entitäten.

**Diagnose**  
Ping, Traceroute und Nslookup direkt auf dem Router, dazu das Systemprotokoll.

**Seitenleisten-Panel**  
Eine Seite je Kategorie, mit den Beschriftungen des Routers in der Sprache von Home Assistant.

**Client-Verfolgung**  
Optional, standardmäßig aus. Ein `device_tracker` je Client, mit Knoten, Band, Durchsatz und Verbindungsdauer. Standardmäßig aus, weil diese Geräte meist schon über eine andere Integration erfasst werden.

---

## Entitäten

Je Mesh-Knoten: verbundene Clients, CPU-Last, Speicherauslastung, Knotenstatus, Backhaul, Kanal 2,4 GHz und 5 GHz (standardmäßig deaktiviert), Konnektivitätssensor, LED-Schalter und Neustart-Schaltfläche.

Auf dem Controller: Clients im gesamten Mesh, Knoten online, Startzeitpunkt, Clients auf 2,4 GHz und auf 5 GHz.

## Dienste

| Dienst | Wirkung |
|---|---|
| `cudy_m3000.reboot_node` | Startet einen Knoten neu. Auf dem Controller den ganzen Router. |
| `cudy_m3000.set_led` | Schaltet die Status-LED eines Knotens ein oder aus. |
| `cudy_m3000.run_diagnostic` | Führt Ping, Traceroute oder Nslookup aus und gibt die Ausgabe über eine Antwortvariable zurück. |
| `cudy_m3000.refresh` | Liest den Router sofort, ohne auf den nächsten Zyklus zu warten. |

```yaml
action: cudy_m3000.run_diagnostic
data:
  tool: ping
  target: 8.8.8.8
response_variable: ergebnis
```

---

## Installation

**HACS**: dieses Repository als benutzerdefiniertes Repository vom Typ *Integration* hinzufügen, installieren, Home Assistant neu starten.

**Manuell**: `custom_components/cudy_m3000` in das Konfigurationsverzeichnis kopieren und neu starten.

Danach unter *Einstellungen → Geräte & Dienste* hinzufügen, mit der IP-Adresse des Hauptknotens und dem Administratorkennwort.

## Optionen

| Option | Standard | Bedeutung |
|---|---|---|
| Aktualisierungsintervall | 60 s | Wie oft der Router abgefragt wird. Niedrige Werte erhöhen seine Last. |
| Sprache der Routerseiten | Auto | In welcher Sprache der Router die Konfigurationsseiten liefert. *Auto* folgt der Sprache von Home Assistant und ändert auch die Sprache der Router-Weboberfläche. |
| Panel in der Seitenleiste anzeigen | An | Ob das Panel registriert wird. |
| Entitäten für verbundene Geräte anlegen | Aus | Ob je Client ein `device_tracker` erzeugt wird. Beim Ausschalten werden bereits angelegte entfernt. |

---

## Kompatibilität

Entwickelt und getestet mit einem Cudy M3000 v1.0 im Modus *Mesh Access Point*, Firmware 2.5.28. Die verfügbaren Seiten werden zur Laufzeit ermittelt, daher sollten auch andere Betriebsmodi und weitere Cudy-Modelle derselben Firmware-Familie funktionieren.

Nicht mit Shenzhen Cudy Technology Co., Ltd. verbunden, von ihr unterstützt oder befürwortet.

## Lizenz

Apache License 2.0 — siehe [LICENSE](LICENSE) und [NOTICE](NOTICE).

Copyright 2026 Marco Cavallo. Die Namensnennung darf in Weiterverbreitungen und abgeleiteten Werken nicht entfernt werden.
