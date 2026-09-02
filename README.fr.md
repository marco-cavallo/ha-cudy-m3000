# Cudy M3000

[English](README.md) · [Italiano](README.it.md) · **Français** · [Deutsch](README.de.md) · [Español](README.es.md)

*Intégration Home Assistant pour les systèmes maillés Cudy M3000.*

*By Marco Cavallo*

---

## Ce que c'est

Une intégration qui dialogue avec un système maillé Cudy M3000 sur le réseau local et l'amène dans Home Assistant : chaque nœud comme appareil distinct, les clients connectés, les pages d'état du routeur et un panneau latéral qui remplace l'interface web du routeur au quotidien.

Cudy ne publie aucune API. L'intégration s'authentifie sur l'interface LuCI du micrologiciel et lit les mêmes points d'accès que l'interface web, y compris le flux JSON derrière la page de topologie maillée. Aucun service cloud, aucune dépendance Python : tout tourne sur votre machine.

## Ce qu'elle fait

**Topologie maillée**  
Chaque nœud devient un appareil Home Assistant, les satellites étant rattachés au contrôleur. Modèle, révision matérielle, micrologiciel, numéro de série, IP, MAC, type de liaison et nombre de sauts proviennent du routeur.

**Surveillance par nœud**  
Clients connectés, charge processeur, mémoire utilisée, état du lien, canal et largeur de bande de chaque radio.

**Informations du routeur**  
Les encadrés d'état de la page d'accueil : micrologiciel et région, heure locale, temps de fonctionnement, nombre d'unités maillées, clients par bande, SSID et canal, adresse LAN.

**Configuration complète**  
Toutes les pages de réglages exposées par le routeur, groupées par catégorie et rendues à partir des définitions de formulaires du micrologiciel : LAN, WAN, IGMP, IPTV/VLAN, Wake-on-LAN, portail captif, sans-fil, planification Wi-Fi, WPS, gestion locale, compte administrateur, heure système, fuseau horaire, langue, contrôle des LED, redémarrage programmé, mise à jour automatique et mode de fonctionnement.

**Administration des nœuds**  
Allumage et extinction de la LED par nœud, et redémarrage, depuis le panneau ou via les entités Home Assistant.

**Diagnostic**  
Ping, traceroute et nslookup exécutés sur le routeur lui-même, plus le journal système.

**Panneau latéral**  
Une page par catégorie, avec les libellés du routeur dans la langue de Home Assistant.

**Suivi des clients**  
Optionnel, désactivé par défaut. Un `device_tracker` par client, avec le nœud de rattachement, la bande, le débit et la durée de connexion. Désactivé car ces appareils sont le plus souvent déjà suivis par une autre intégration.

---

## Entités

Par nœud maillé : clients connectés, charge processeur, mémoire, état du nœud, liaison, canal 2,4 GHz et 5 GHz (désactivés par défaut), capteur de connectivité, interrupteur de LED et bouton de redémarrage.

Sur le contrôleur : clients de tout le maillage, nœuds en ligne, instant de démarrage, clients en 2,4 GHz et en 5 GHz.

## Services

| Service | Effet |
|---|---|
| `cudy_m3000.reboot_node` | Redémarre un nœud. Sur le contrôleur, tout le routeur. |
| `cudy_m3000.set_led` | Allume ou éteint la LED d'état d'un nœud. |
| `cudy_m3000.run_diagnostic` | Exécute ping, traceroute ou nslookup et renvoie le résultat via une variable de réponse. |
| `cudy_m3000.refresh` | Interroge le routeur immédiatement. |

```yaml
action: cudy_m3000.run_diagnostic
data:
  tool: ping
  target: 8.8.8.8
response_variable: resultat
```

---

## Installation

**HACS** : ajoutez ce dépôt comme dépôt personnalisé de type *Intégration*, installez-le, puis redémarrez Home Assistant.

**Manuelle** : copiez `custom_components/cudy_m3000` dans le dossier de configuration et redémarrez.

Ajoutez ensuite l'intégration depuis *Paramètres → Appareils et services*, avec l'adresse IP du nœud principal et le mot de passe administrateur.

## Options

| Option | Défaut | Signification |
|---|---|---|
| Intervalle de mise à jour | 60 s | Fréquence d'interrogation du routeur. Des valeurs faibles augmentent sa charge. |
| Langue des pages du routeur | Auto | Langue dans laquelle le routeur sert ses pages. *Auto* suit celle de Home Assistant et change aussi celle de l'interface web du routeur. |
| Afficher le panneau latéral | Activé | Enregistrement du panneau. |
| Créer des entités pour les appareils connectés | Désactivé | Création d'un `device_tracker` par client. La désactivation supprime ceux déjà créés. |

---

## Compatibilité

Développée et testée sur un Cudy M3000 v1.0 en mode *Mesh Access Point*, micrologiciel 2.5.28. Les pages disponibles sont détectées à l'exécution : d'autres modes et d'autres modèles Cudy de la même famille devraient fonctionner.

Sans lien avec Shenzhen Cudy Technology Co., Ltd., ni approuvée ni soutenue par elle.

## Licence

Apache License 2.0 — voir [LICENSE](LICENSE) et [NOTICE](NOTICE).

Copyright 2026 Marco Cavallo. L'attribution ne doit pas être retirée des redistributions ni des œuvres dérivées.
