# Cudy M3000

[English](README.md) · [Italiano](README.it.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Español**

*Integración de Home Assistant para los sistemas mesh Cudy M3000.*

*By Marco Cavallo*

---

## Qué es

Una integración que habla con un sistema mesh Cudy M3000 en la red local y lo trae a Home Assistant: cada nodo como dispositivo propio, los clientes conectados, las páginas de estado del router y un panel lateral que sustituye a la interfaz web del router en la administración diaria.

Cudy no publica ninguna API. La integración se autentica en la interfaz LuCI del firmware y lee los mismos puntos finales que usa la interfaz web, incluido el JSON que alimenta la página de topología mesh. Sin servicios en la nube ni dependencias de Python: todo se ejecuta en tu propia máquina.

## Qué hace

**Topología mesh**  
Cada nodo se convierte en un dispositivo de Home Assistant, con los satélites anidados bajo el controlador. Modelo, revisión de hardware, firmware, número de serie, IP, MAC, tipo de enlace y número de saltos se leen del router.

**Supervisión por nodo**  
Clientes conectados, carga de CPU, uso de memoria, estado del enlace, canal y ancho de banda de cada radio.

**Información del router**  
Los recuadros de estado de la página de inicio: firmware y región, hora local, tiempo encendido, número de unidades mesh, clientes por banda, SSID y canal, dirección LAN.

**Configuración completa**  
Todas las páginas de ajustes que expone el router, agrupadas por categoría y generadas a partir de las definiciones de formulario del propio firmware: LAN, WAN, IGMP, IPTV/VLAN, Wake-on-LAN, portal cautivo, inalámbrico, programación Wi-Fi, WPS, gestión local, cuenta de administrador, hora del sistema, zona horaria, idioma, control de LED, reinicio programado, actualización automática y modo de funcionamiento.

**Administración de nodos**  
Encender y apagar el LED por nodo, y reiniciar, desde el panel o mediante entidades de Home Assistant.

**Diagnóstico**  
Ping, traceroute y nslookup ejecutados en el propio router, además del registro del sistema.

**Panel lateral**  
Una página por categoría, con las etiquetas del router en el idioma de Home Assistant.

**Seguimiento de clientes**  
Opcional, desactivado por defecto. Un `device_tracker` por cliente, con el nodo al que está conectado, la banda, el rendimiento y la duración de la conexión. Desactivado porque en la mayoría de instalaciones estos dispositivos ya los sigue otra integración.

---

## Entidades

Por nodo mesh: clientes conectados, carga de CPU, uso de memoria, estado del nodo, enlace, canal de 2,4 GHz y de 5 GHz (desactivados por defecto), sensor de conectividad, interruptor de LED y botón de reinicio.

En el controlador: clientes de todo el mesh, nodos en línea, momento de arranque, clientes en 2,4 GHz y en 5 GHz.

## Servicios

| Servicio | Qué hace |
|---|---|
| `cudy_m3000.reboot_node` | Reinicia un nodo. En el controlador, todo el router. |
| `cudy_m3000.set_led` | Enciende o apaga el LED de estado de un nodo. |
| `cudy_m3000.run_diagnostic` | Ejecuta ping, traceroute o nslookup y devuelve el resultado en una variable de respuesta. |
| `cudy_m3000.refresh` | Lee el router de inmediato. |

```yaml
action: cudy_m3000.run_diagnostic
data:
  tool: ping
  target: 8.8.8.8
response_variable: resultado
```

---

## Instalación

**HACS**: añade este repositorio como repositorio personalizado de tipo *Integración*, instálalo y reinicia Home Assistant.

**Manual**: copia `custom_components/cudy_m3000` en la carpeta de configuración y reinicia.

Después añade la integración desde *Ajustes → Dispositivos y servicios*, indicando la dirección IP del nodo principal y la contraseña de administrador.

## Opciones

| Opción | Predeterminado | Significado |
|---|---|---|
| Intervalo de actualización | 60 s | Cada cuánto se consulta el router. Valores bajos aumentan su carga. |
| Idioma de las páginas del router | Auto | En qué idioma sirve el router sus páginas. *Auto* sigue el de Home Assistant y cambia también el de la interfaz web del router. |
| Mostrar el panel lateral | Activado | Si se registra el panel. |
| Crear entidades para los dispositivos conectados | Desactivado | Si se crea un `device_tracker` por cliente. Al desactivarlo se eliminan los ya creados. |

---

## Compatibilidad

Desarrollada y probada con un Cudy M3000 v1.0 en modo *Mesh Access Point*, firmware 2.5.28. Las páginas disponibles se detectan en tiempo de ejecución, así que otros modos y otros modelos Cudy de la misma familia deberían funcionar.

Sin vinculación con Shenzhen Cudy Technology Co., Ltd., ni respaldada ni apoyada por ella.

## Licencia

Apache License 2.0 — véanse [LICENSE](LICENSE) y [NOTICE](NOTICE).

Copyright 2026 Marco Cavallo. La atribución no debe eliminarse de redistribuciones ni obras derivadas.
