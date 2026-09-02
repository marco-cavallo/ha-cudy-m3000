# Cudy M3000

**English** · [Italiano](README.it.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

*Home Assistant integration for Cudy M3000 mesh Wi-Fi systems.*

*By Marco Cavallo*

---

## What it is

A custom integration that talks to a Cudy M3000 mesh system over your local network and brings it into Home Assistant: every node as its own device, the connected clients, the router's own status pages, and a sidebar panel that replaces the router's web interface for day-to-day administration.

Cudy publishes no API. The integration authenticates against the firmware's own LuCI interface and reads the same endpoints the web UI uses, including the JSON feed behind the mesh topology page. No cloud service and no Python dependencies: everything runs on your own machine.

## What it does

**Mesh topology**  
Every node becomes a Home Assistant device, with the satellites nested under the controller. Model, hardware revision, firmware, serial number, IP, MAC, backhaul type and hop count are all read from the router.

**Per-node monitoring**  
Connected clients, CPU load, memory usage, link state, and the channel and bandwidth of each radio.

**Router information**  
The status panels of the router's home page: firmware and region, local time, uptime, mesh unit count, clients split by band, SSID and channel, LAN address.

**Full configuration**  
Every settings page the router exposes, grouped by category and rendered from the firmware's own form definitions: LAN, WAN, IGMP, IPTV/VLAN, Wake-on-LAN, captive portal, wireless, Wi-Fi schedule, WPS, local management, admin account, system time, timezone, language, LED control, timed reboot, firmware auto-update and operation mode.

**Node administration**  
LED on and off per node, and reboot, from the panel or from Home Assistant entities.

**Diagnostics**  
Ping, traceroute and nslookup run on the router itself, plus the system log.

**Sidebar panel**  
One page per category, with the router's own labels in your Home Assistant language.

**Client tracking**  
Optional, off by default. One `device_tracker` per connected client, with the node it is attached to, the band, throughput and connection time. Left off because most setups already track these devices through another integration.

---

## Entities

Per mesh node:

| Entity | Meaning |
|---|---|
| `sensor.*_connected_clients` | Devices attached to this node. |
| `sensor.*_cpu_load` | CPU load percentage. |
| `sensor.*_memory_usage` | Memory usage percentage. |
| `sensor.*_node_state` | `connected`, `disconnected`, `connecting`. |
| `sensor.*_backhaul` | `wired` or `auto`, with parent MAC, hop and uplink interface as attributes. |
| `sensor.*_24_ghz_channel` | Channel in use. *Disabled by default.* |
| `sensor.*_5_ghz_channel` | Channel in use. *Disabled by default.* |
| `binary_sensor.*_node_online` | Connectivity of the node. |
| `switch.*_led` | Status LED. |
| `button.*_reboot` | Restart the node. |

On the controller:

| Entity | Meaning |
|---|---|
| `sensor.*_mesh_total_clients` | Clients across the whole mesh. |
| `sensor.*_online_nodes` | Nodes currently connected, with a per-node breakdown in the attributes. |
| `sensor.*_up_since` | Boot time, as a timestamp. |
| `sensor.*_24_ghz_devices` | Clients on 2.4 GHz. |
| `sensor.*_5_ghz_devices` | Clients on 5 GHz. |

---

## Services

| Service | What it does |
|---|---|
| `cudy_m3000.reboot_node` | Restart one node. On the controller this restarts the whole router. |
| `cudy_m3000.set_led` | Turn a node's status LED on or off. |
| `cudy_m3000.run_diagnostic` | Run ping, traceroute or nslookup and return the output. Uses a response variable. |
| `cudy_m3000.refresh` | Read the router immediately instead of waiting for the next poll. |

Example:

```yaml
action: cudy_m3000.run_diagnostic
data:
  tool: ping
  target: 8.8.8.8
response_variable: result
```

---

## Installation

**HACS**: add this repository as a custom repository of type *Integration*, install it, then restart Home Assistant.

**Manual**: copy `custom_components/cudy_m3000` into your Home Assistant configuration directory and restart.

Then add the integration from *Settings → Devices & services*, giving the IP address of the main mesh node and the administrator password.

## Options

| Option | Default | Meaning |
|---|---|---|
| Update interval | 60 s | How often the router is polled. Low values increase the load on it. |
| Router page language | Auto | Which language the router serves its configuration pages in. *Auto* follows the Home Assistant language. This also changes the language of the router's own web interface. |
| Show the sidebar panel | On | Whether to register the panel. |
| Create entities for connected devices | Off | Whether to create a `device_tracker` per client. Turning it off removes any that were already created. |

---

## How it works

Authentication follows the firmware's own scheme, taken from its `sysauth.js`:

```
GET  /cgi-bin/luci/                -> hidden fields _csrf and salt
POST /cgi-bin/luci/admin/get_token -> single-use token
luci_password = sha256(sha256(password + salt) + token)
POST /cgi-bin/luci/                -> sysauth session cookie
```

The mesh topology page is backed by a JSON endpoint, `/admin/network/mesh/clients`, which carries the whole inventory: nodes, radios, load and client counts. That is the primary data source, so the node information does not depend on HTML parsing.

The configuration pages are standard LuCI CBI forms, all sharing one shape:

```
cbid.<config>.<section>.<option>       field value
cbi.cbe.<config>.<section>.<option>    checkbox presence marker
token + cbi.submit=1                   submit fields
cbi_d_add("<id>", {"<dep>": "<value>"}) conditional visibility
```

Because of that, a single engine reads any page into a declarative schema — fields, types, options, current values, dependencies — and rebuilds the POST the browser would send. Adding a page is one line of configuration, not new code.

Labels come from the router itself, so requesting the pages in the Home Assistant language is what makes the panel multilingual.

## Compatibility

Developed and tested against a Cudy M3000 v1.0 in *Mesh Access Point* mode, firmware 2.5.28. The set of available pages is probed at runtime, so other operation modes and other Cudy models on the same firmware family should work, showing whatever the router actually exposes.

Not affiliated with, endorsed by, or supported by Shenzhen Cudy Technology Co., Ltd.

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).

Copyright 2026 Marco Cavallo. Attribution must not be removed from redistributions or derivative works.
