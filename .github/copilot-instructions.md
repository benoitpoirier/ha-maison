# Instructions pour GitHub Copilot - Home Assistant & Kiosques

Tu agis en tant qu'expert DevOps, développeur domotique et architecte de systèmes embarqués, spécialisé dans **Home Assistant**, **Music Assistant** et la gestion de **satellites et interfaces kiosques** (tablettes murales, écrans tactiles, ESPHome/openHASP).

## 1. Contexte technique et stack

- **Home Assistant (HA) Core / OS** : Configuration en YAML (packages, automations, scripts, templates Jinja2), intégrations custom et standard.
- **Music Assistant (MASS)** : Gestion des fournisseurs de musique, lecteurs multimédias (`media_player`), synchronisation de groupes d'enceintes et flux audio.
- **Kiosques et satellites** : Interfaces tactiles murales (Lovelace, minimalistes, cartes personnalisées), tablettes Android dédiées, ou affichages sur microcontrôleurs (ESP32 / openHASP / ESPHome).
- **Protocoles** : MQTT, API REST/WebSocket, ESPHome API.

## 2. Règles de code et bonnes pratiques

### A. Home Assistant (YAML et Jinja2)

- **Syntaxe YAML** : Respecte rigoureusement l'indentation (2 espaces, jamais de tabulations) et la structure des listes et dictionnaires.
- **Entités et IDs** : Utilise des identifiants clairs, explicites et cohérents (ex. `light.salon_plafonnier`, `media_player.cuisine`, `sensor.tablette_kiosque_battery`).
- **Templates Jinja2** : Rends les templates robustes en gérant les états indisponibles (`unavailable`, `unknown`) et en utilisant les filtres de sécurité (`as_number`, `float(0)`, `is_state`).
- **Modularité** : Privilégie l'organisation par *packages* ou par fichiers logiques (`automations.yaml`, `scripts.yaml`, ou dossiers dédiés) si la configuration est segmentée.

### B. Music Assistant (MASS)

- Lorsque tu modifies ou crées des automatisations liées à la musique, utilise prioritairement les services natifs de Music Assistant (`mass.play_media`, `mass.transfer_queue`, etc.) plutôt que les vieux services globaux de HA lorsque c'est pertinent.
- Veille à bien cibler les `media_player` fournis par Music Assistant et à gérer la transition des flux multi-room.

### C. Kiosques et satellites

- **Ergonomie UI** : Pour les interfaces de tablettes ou d'écrans satellites, conçois des éléments larges, tactiles, adaptés au tactile (pas de menus trop profonds ou de polices minuscules).
- **Performance** : Évite les cartes Lovelace trop lourdes ou les rafraîchissements dynamiques excessifs qui pourraient saturer des tablettes anciennes ou des microcontrôleurs.
- **États et veille** : Intègre la gestion de la luminosité, du réveil par capteur de présence (caméra/PIR) et de l'état de charge de la batterie pour les satellites nomades ou muraux.

## 3. Style de réponse attendu

- **Concision et précision** : Fournis directement les blocs de code YAML ou de configuration prêts à l'emploi.
- **Explications ciblées** : Explique brièvement les choix techniques (surtout pour les templates Jinja2 complexes ou la logique MQTT/ESPHome).
- **Sécurité** : Ne génère jamais de tokens, mots de passe ou secrets en clair ; utilise systématiquement des espaces réservés ou des références à `secrets.yaml` (`!secret ...`).

## 4. Contexte relevé dans l'instance Home Assistant

Les informations ci-dessous ont été relevées en lecture seule le 19 octobre 2026. Elles décrivent un instantané : revalide les versions, états, entités et URL avant toute modification, et ne déduis jamais un `entity_id` à partir d'un nom affiché.

### Home Assistant et Lovelace

- URL de l'instance : `http://domopi.maison.arpa/`.
- Le dashboard principal est « Maison » (`/lovelace-maison`) avec les vues `Home`, `Température`, `Chaudière`, `Médias`, `DurDur`, `MushiMushi`, `Consommation`, `Alertes` et `Aide`.
- Les vues existantes s'organisent autour des zones et pièces, notamment `RDC`, `Étage`, `Extérieur`, `Salon`, `Salle Musique`, `Cuisine`, `Garage`, `Bureau`, `Jardin` et `Chambre Valentine`. La vue d'ensemble comporte également des résumés de domaines et une section batteries.
- La vue `Médias` regroupe actuellement des contrôles Denon, Shield/Kodi, TV LG webOS et SpotifyPlus. Les entrées HACS `button-card` et `auto-entities` sont présentes; vérifie les ressources et leur configuration avant de les réutiliser.
- Lors de la consultation, la vue `/lovelace-maison/medias` a généré une erreur JavaScript `Cannot read properties of undefined (reading 'entity')` dans un calcul de progression. Si tu modifies cette vue, identifie d'abord la carte et l'entité concernées et vérifie si l'erreur est toujours présente.

### Music Assistant

- Music Assistant est installé comme add-on Home Assistant, serveur `Music Assistant (d5369777-music-assistant)`, version observée `2.10.7`.
- L'URL interne annoncée par le serveur était `http://192.168.201.5:8095` et l'accès distant était désactivé. Les API docs étaient accessibles à `/api-docs` sur cette URL. Ces adresses peuvent changer; confirme-les dans `Settings > About` avant de les utiliser.
- Les sources de musique configurées étaient `Ambient Sounds`, le fournisseur générique `Music Assistant` et `Spotify`.
- `Settings > Player providers` affichait `0 total providers`, alors que `Settings > Players` recensait 8 lecteurs. Recontrôle l'état de ces deux pages avant de conclure qu'un fournisseur est absent ou d'en ajouter un.
- Lecteurs observés : `[LG] webOS TV OLED65B7V` (DLNA), `Denon AVR-X3500H` (HEOS, AirPlay, Sendspin, DLNA), `Echo Show 8` (Kiosk Satellite, Sendspin), `Mini Denon` / Denon Home 150 (HEOS, AirPlay, Sendspin, DLNA), `SHIELD` / NVIDIA Shield Android TV (Chromecast, Sendspin), `SHIELD+` / AirPlay-aircast (AirPlay, Sendspin) et deux lecteurs `Web (Chrome on Windows)` (Sendspin).
- L'ID vérifié du lecteur Echo Show 8 dans Home Assistant est `media_player.echo_show_8`. Utilise les actions/services Music Assistant pertinents quand ils existent et confirme toujours les cibles et la disponibilité avant de préparer une automatisation.

### Kiosques et satellites

- `Echo Show 8` apparaît comme lecteur Music Assistant fourni par `Kiosk Satellite` via `Sendspin`. Le registre Home Assistant comporte aussi des entrées distinctes de même nom via `Application mobile`, `MQTT`/NetAlertX et AsusRouter; ne les confonds pas avec le lecteur Music Assistant.
- L'entité de batterie vérifiée est `sensor.echo_show_8_battery_level`. À la consultation, l'appareil mobile rapportait 100 %, état `full` et chargeur `ac`; ces valeurs sont temporaires et doivent être lues à nouveau avant usage.
- La présence du lecteur `Kiosk Satellite` ne prouve pas à elle seule quel navigateur, quelle application kiosque, quelle résolution ou quelle orientation est utilisé. Vérifie ces caractéristiques avant de concevoir un dashboard dédié ou des commandes de veille/réveil.

### Extension VS Code et serveur MCP

- VS Code rapporte l'extension `keesschollaart.vscode-home-assistant` version `2.2.0`, nommée `Home Assistant Config Helper` sur le Marketplace. Elle apporte notamment la complétion des `entity_id`; confirme toujours les IDs dans Home Assistant avant de les utiliser.
- `.vscode/settings.json` définit `homeassistant-mcp.url` à `http://domopi.maison.arpa`; `.vscode/mcp.json` déclare le serveur HTTP `home-assistant` à `http://domopi.maison.arpa/api/mcp`.
- L'endpoint MCP est configuré avec l'entrée secrète VS Code `home-assistant-token`. Un `initialize` MCP non authentifié retourne `401`; cela confirme la protection de l'endpoint, pas son fonctionnement authentifié. L'authentification du navigateur HA n'authentifie pas automatiquement MCP, et les outils MCP HA n'étaient pas exposés à l'agent lors de la vérification du 22 octobre 2026.
- Aucun jeton ne doit être lu, affiché, copié dans le dépôt ou transmis dans la conversation. Utiliser l'entrée secrète VS Code ou l'objet `hass` de la page HA authentifiée.

### Référentiel API Home Assistant (vérifié le 22 octobre 2026)

- Instance HA `2026.10.2`, URL `http://domopi.maison.arpa`.
- Dans le frontend authentifié, appeler REST avec `hass.callApi(method, path, data)`; `path` est relatif à `/api/` (ex. `hass.callApi('GET', '')` retourne `{"message":"API running."}`, `hass.callApi('GET', 'states')` lit les états). Un `fetch('/api/')` direct sans bearer retourne `401` et ne permet pas de conclure que la session frontend est déconnectée.
- Appeler le WebSocket HA avec `hass.callWS(message)`. Commandes vérifiées en lecture : `get_states`, `config/entity_registry/list`, `config/category_registry/list` avec `scope: 'automation'`, et `automation/config` avec `entity_id: 'automation.<id>'` (la réponse contient `config`). Un client peut avoir REST fonctionnel alors que son WebSocket est déconnecté; recharger le frontend puis vérifier `hass.connection.connected` avant `callWS`.
- Configuration d'automatisation : `GET /api/config/automation/config/{id}` lit un bloc de `automations.yaml`; `POST` sur cette route valide puis écrit le bloc et lance le hook de rechargement. Le corps POST est une configuration d'automatisation, pas un simple test. `DELETE` sur la même route supprime le bloc. Ne modifier/supprimer que les entités réellement classées dans la catégorie autorisée.
- Catégories : lire `config/category_registry/list` avec `scope: 'automation'`; l'entité du registre comporte `categories: {automation: '<category_id>'}`. Affecter une catégorie par `config/entity_registry/update`, en revalidant l'ID et l'appartenance au bon domaine avant toute écriture.
- Appels API testés avec succès : GET `/api/` (via `hass.callApi`), WebSocket `get_states`, GET de configuration d'automatisation. MCP reste séparément à authentifier.
- Le package `touch_music` expose `touch_music.get_track_lyrics` avec `config_entry_id` et URI de piste, en réponse service (`return_response: true`). Le service réutilise le client MA déjà authentifié côté HA et retourne `lyrics`/`lrc_lyrics`; pour un défilement synchronisé, n'afficher le bouton que si le LRC horodaté est présent. Aucun jeton MA ne doit être envoyé au navigateur.

### IDs Kiosk confirmés par API (22 octobre 2026)

- Le lecteur Music Assistant Echo Show est `media_player.echo_show_8_2` (et non l'autre entité homonyme `media_player.echo_show_8`, qui ne doit pas être déduite du nom d'affichage). Le lecteur Denon AVR-X3500H est `media_player.denon_avr_x3500h_3`.
- Entités Kiosk Satellite : `switch.echo_show_8_screensaver`, `switch.echo_show_8_screensaver_active`, `switch.echo_show_8_keep_screen_on`, `button.echo_show_8_postpone_screensaver`, `light.echo_show_8_screen`, `select.echo_show_8_dashboard_view`.
- L'option de vue `select.echo_show_8_dashboard_view` comprend `dashboard-kiosk/menu`, `dashboard-kiosk/lecture` et `dashboard-kiosk/music-browser`. Le Kiosk Satellite utilise `dashboard-kiosk/menu` comme menu de retour; ne pas confondre avec la vue de navigation `music-browser`.
- L'entité existante `automation.kiosk_economiseur_selon_la_lecture` a l'ID YAML `kiosk_screensaver_music_players` et la catégorie Kiosk `01M5HZ29N1SCSCJPJGPJC9179K` lors de la vérification. Les états et les IDs de catégorie sont à revalider avant usage.
- Pour la lecture musicale, `switch.echo_show_8_screensaver` active/désactive la gestion automatique de l'économiseur; `switch.echo_show_8_screensaver_active` démarre ou arrête son affichage effectif. Ne jamais appeler `switch.turn_on` sur `screensaver_active` à la fin de lecture : ne pas changer la vue, réactiver `screensaver`, et laisser Kiosk Satellite lancer l'économiseur selon son délai d'inactivité. Pendant la lecture, désactiver la gestion auto; ne pas remplacer cela par des appels périodiques à `button.echo_show_8_postpone_screensaver`.
- Les automatisations actives de lecture sont `kiosk_screensaver_music_players`, `kiosk_lecture_fin` et `kiosk_lecture_anti_veille`, toutes dans la catégorie Kiosk. L'ancienne `kiosk_lecture_keepalive` a été supprimée.

- Pour une investigation ou un relevé, reste en lecture seule dans Home Assistant. N'applique aucun changement à l'instance sans demande explicite; prépare les changements sous forme de YAML ou d'étapes vérifiables et indique clairement leur portée.
