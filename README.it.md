# Cudy M3000

[English](README.md) · **Italiano** · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

*Integrazione Home Assistant per i sistemi mesh Cudy M3000.*

*By Marco Cavallo*

---

## Cos'è

Un'integrazione che dialoga con un sistema mesh Cudy M3000 sulla rete locale e lo porta dentro Home Assistant: ogni nodo come dispositivo a sé, i client connessi, le pagine di stato del router e un pannello laterale che sostituisce l'interfaccia web del router nell'amministrazione quotidiana.

Cudy non pubblica API. L'integrazione si autentica sull'interfaccia LuCI del firmware e legge gli stessi endpoint che usa la UI del router, compreso il feed JSON dietro la pagina della topologia mesh. Nessun servizio cloud e nessuna dipendenza Python: gira tutto sulla tua macchina.

## Cosa fa

**Topologia mesh**  
Ogni nodo diventa un dispositivo di Home Assistant, con i satelliti annidati sotto il controller. Modello, revisione hardware, firmware, numero di serie, IP, MAC, tipo di backhaul e numero di hop sono letti dal router.

**Monitoraggio per nodo**  
Client connessi, carico CPU, uso della memoria, stato del collegamento, canale e larghezza di banda di ciascuna radio.

**Informazioni del router**  
I riquadri di stato della home page del router: firmware e regione, ora locale, tempo di accensione, numero di unità mesh, dispositivi divisi per banda, SSID e canale, indirizzo LAN.

**Configurazione completa**  
Tutte le pagine di impostazioni che il router espone, raggruppate per categoria e generate dalle definizioni dei form del firmware stesso: LAN, WAN, IGMP, IPTV/VLAN, Wake-on-LAN, portale captive, wireless, pianificazione Wi-Fi, WPS, gestione locale, account amministratore, ora di sistema, fuso orario, lingua, controllo LED, riavvio programmato, aggiornamento automatico del firmware e modalità operativa.

**Amministrazione dei nodi**  
LED acceso e spento per nodo, e riavvio, dal pannello o dalle entità di Home Assistant.

**Diagnostica**  
Ping, traceroute e nslookup eseguiti sul router stesso, più il log di sistema.

**Pannello laterale**  
Una pagina per categoria, con le etichette del router nella lingua di Home Assistant.

**Tracciamento dei client**  
Opzionale, disattivato di default. Un `device_tracker` per client, con il nodo a cui è agganciato, la banda, il throughput e la durata della connessione. È disattivato perché nella maggior parte delle installazioni questi dispositivi sono già tracciati da un'altra integrazione.

---

## Entità

Per ogni nodo mesh:

| Entità | Significato |
|---|---|
| `sensor.*_dispositivi_connessi` | Dispositivi agganciati a questo nodo. |
| `sensor.*_carico_cpu` | Percentuale di carico della CPU. |
| `sensor.*_uso_memoria` | Percentuale di memoria usata. |
| `sensor.*_stato_nodo` | `connesso`, `disconnesso`, `in connessione`. |
| `sensor.*_backhaul` | `wired` o `auto`, con MAC del padre, hop e interfaccia negli attributi. |
| `sensor.*_canale_2_4_ghz` | Canale in uso. *Disattivato di default.* |
| `sensor.*_canale_5_ghz` | Canale in uso. *Disattivato di default.* |
| `binary_sensor.*_nodo_online` | Connettività del nodo. |
| `switch.*_led` | LED di stato. |
| `button.*_riavvia` | Riavvia il nodo. |

Sul controller:

| Entità | Significato |
|---|---|
| `sensor.*_dispositivi_totali_mesh` | Client su tutto il mesh. |
| `sensor.*_nodi_online` | Nodi connessi, con il dettaglio per nodo negli attributi. |
| `sensor.*_acceso_da` | Istante di avvio, come timestamp. |
| `sensor.*_dispositivi_2_4_ghz` | Client su 2.4 GHz. |
| `sensor.*_dispositivi_5_ghz` | Client su 5 GHz. |

---

## Servizi

| Servizio | Cosa fa |
|---|---|
| `cudy_m3000.reboot_node` | Riavvia un nodo. Sul controller riavvia l'intero router. |
| `cudy_m3000.set_led` | Accende o spegne il LED di stato di un nodo. |
| `cudy_m3000.run_diagnostic` | Esegue ping, traceroute o nslookup e restituisce il risultato tramite variabile di risposta. |
| `cudy_m3000.refresh` | Legge subito il router senza attendere il ciclo successivo. |

Esempio:

```yaml
action: cudy_m3000.run_diagnostic
data:
  tool: ping
  target: 8.8.8.8
response_variable: risultato
```

---

## Installazione

**HACS**: aggiungi questo repository come repository personalizzato di tipo *Integrazione*, installalo e riavvia Home Assistant.

**Manuale**: copia `custom_components/cudy_m3000` nella cartella di configurazione di Home Assistant e riavvia.

Poi aggiungi l'integrazione da *Impostazioni → Dispositivi e servizi*, indicando l'indirizzo IP del nodo principale e la password di amministrazione.

## Opzioni

| Opzione | Default | Significato |
|---|---|---|
| Intervallo di aggiornamento | 60 s | Ogni quanto viene interrogato il router. Valori bassi ne aumentano il carico. |
| Lingua delle pagine del router | Auto | In che lingua il router serve le pagine di configurazione. *Auto* segue la lingua di Home Assistant. Cambia anche la lingua dell'interfaccia web del router. |
| Mostra il pannello nella barra laterale | Attivo | Se registrare il pannello. |
| Crea entità per i dispositivi connessi | Disattivo | Se creare un `device_tracker` per client. Disattivandolo, quelli già creati vengono rimossi. |

---

## Come funziona

L'autenticazione segue lo schema del firmware, ricavato dal suo `sysauth.js`:

```
GET  /cgi-bin/luci/                -> campi nascosti _csrf e salt
POST /cgi-bin/luci/admin/get_token -> token monouso
luci_password = sha256(sha256(password + salt) + token)
POST /cgi-bin/luci/                -> cookie di sessione sysauth
```

La pagina della topologia mesh si alimenta da un endpoint JSON, `/admin/network/mesh/clients`, che contiene l'intero inventario: nodi, radio, carico e conteggio dei client. È la fonte dati principale, quindi le informazioni sui nodi non dipendono dal parsing dell'HTML.

Le pagine di configurazione sono form CBI standard di LuCI, tutte con la stessa forma:

```
cbid.<config>.<sezione>.<opzione>       valore del campo
cbi.cbe.<config>.<sezione>.<opzione>    marcatore di presenza
token + cbi.submit=1                    campi di submit
cbi_d_add("<id>", {"<dip>": "<valore>"}) visibilità condizionale
```

Per questo un unico motore legge qualsiasi pagina trasformandola in uno schema dichiarativo — campi, tipi, opzioni, valori correnti, dipendenze — e ricostruisce il POST che invierebbe il browser. Aggiungere una pagina è una riga di configurazione, non codice nuovo.

Le etichette le produce il router, quindi è chiedendogli le pagine nella lingua di Home Assistant che il pannello diventa multilingua.

## Compatibilità

Sviluppata e provata su un Cudy M3000 v1.0 in modalità *Mesh Access Point*, firmware 2.5.28. L'elenco delle pagine disponibili viene sondato a runtime, quindi altre modalità operative e altri modelli Cudy della stessa famiglia di firmware dovrebbero funzionare, mostrando quello che il router espone davvero.

Non affiliata, approvata o supportata da Shenzhen Cudy Technology Co., Ltd.

## Licenza

Apache License 2.0 — vedi [LICENSE](LICENSE) e [NOTICE](NOTICE).

Copyright 2026 Marco Cavallo. L'attribuzione non va rimossa da ridistribuzioni o lavori derivati.
