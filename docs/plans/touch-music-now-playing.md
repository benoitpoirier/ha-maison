# Plan de dev — Carte « Lecture en cours » + automatismes Echo Show (Kiosk Satellite)

## Objectif

1. Nouvelle carte `custom:touch-music-now-playing` (look de la maquette : pochette à gauche,
   titre/artiste/album, barre de progression, transport, rangée d'actions, pastille
   « Lecture en cours », fond flouté issu de la pochette), placée dans la vue
   `http://domopi.maison.arpa/dashboard-kiosk/lecture`.
2. Automatismes HA (catégorie **Kiosk**) pour réveiller l'Echo Show 8 et afficher la vue `lecture`
   pendant la lecture, puis rendre la main à l'économiseur 5 à 10 s après la pause.

## Contraintes et décisions

- **Contexte de lecture d'abord** : seuls les lecteurs Echo Show et Denon AVR-X3500H sont retenus.
  La source peut varier (Spotify Benoît / Sandrine, Ambient Sounds, builtin, Spotify Connect,
  AirPlay, etc.); la carte montre le lecteur et le provider détecté avant de proposer les commandes.
- Pas de backend Python ni de jeton : la carte vit dans `touch-music-card.js` (ressource déjà chargée
  par `add_extra_js_url` du composant `touch_music`).
- Toutes les automatisations portent la catégorie **Kiosk**. Seules les automatisations de cette
  catégorie peuvent être modifiées/supprimées par l'agent ; aucune autre ne doit être touchée.
- La configuration YAML des automatisations se lit/se sauvegarde via REST
  `/api/config/automation/config/{id}`; la catégorie est une métadonnée du registre d'entités,
  affectée par WS `config/entity_registry/update` avec `categories.automation` égal à l'ID Kiosk
  vérifié `01M5HZ29N1SCSCJPJGPJC9179K`.
- Carte, vue Lecture et trois automatisations sont déployées dans HA; `music-browser` n'a pas été
  modifiée. Les trois automatisations sont actives et classées « Kiosk ».

## Phase 0 — Relevé préalable aux automatisations (lecture seule)

> État revalidé le 22 octobre 2026 via l'API HA `2026.10.2` et le panneau Kiosk : tableau de bord
> par défaut « Kiosk / Music Browser », ESPHome activé avec toutes les entités exposées, nœud
> `echoshow8`. Économiseur activé avec un délai de 30 s, mode « Ambiance météo »; extinction du
> panneau après économiseur réglée à 0 min. REST et WebSocket HA ont été testés depuis la page
> authentifiée; aucun jeton n'a été affiché.

| # | À vérifier | Où | Pourquoi |
|---|---|---|---|
| 0.1 | Lecteurs MA : `media_player.echo_show_8_2` et `media_player.denon_avr_x3500h_3` | REST `GET states` | IDs vérifiés; `media_player.echo_show_8` est l'autre entité homonyme et n'est pas la cible MA |
| 0.2 | `active_queue`, `app_id`, `media_content_id`, `source`, position, `shuffle`, `repeat`; le compte/provider provient de `music_assistant.get_queue` | Outils de dev > États / Actions | Les URI `library://` seules ne suffisent pas toujours à identifier Spotify |
| 0.3 | Commandes ESPHome : voir la table ci-dessous | REST `GET states` + registre | Tous les IDs utilisés par A1–A3 ont été vérifiés |
| 0.4 | Défaut `dashboard-kiosk/menu`, économiseur 30 s, mode Ambiance météo, extinction panneau = 0 min | Kiosk Satellite > Home Assistant / Économiseur d'écran | A1/A3 désactivent la gestion auto pendant lecture; A2 la réactive et laisse Kiosk Satellite déclencher après son délai |
| 0.5 | `music_assistant.get_queue` et actions SpotifyPlus favorites; seul le compte Benoît (`media_player.spotifyplus_benoitpoirier_fr`) est enregistré côté SpotifyPlus | Outils de dev > Actions / États | N'afficher le cœur que si le provider courant a un compte de favoris correspondant |
| 0.6 | Catégorie « Kiosk », ID `01M5HZ29N1SCSCJPJGPJC9179K` | WS `config/category_registry/list`, scope `automation` | Revalider l'ID avant toute future affectation |
| 0.7 | Le dashboard live contient `menu`, `lecture`, `music-browser`, `eclairage`, `meteo` | Select `select.echo_show_8_dashboard_view` | Le JSON local est une copie; ne pas republier une configuration dashboard complète obsolète |

Entités Kiosk (à compléter en 0.3) :

| Rôle | Entité |
|---|---|
| Lecteur MA Echo Show | `media_player.echo_show_8_2` |
| Lecteur Denon AVR-X3500H | `media_player.denon_avr_x3500h_3` |
| Écran on/off | `light.echo_show_8_screen` |
| Économiseur activé / actif | `switch.echo_show_8_screensaver` / `switch.echo_show_8_screensaver_active` |
| Maintien écran / reporter économiseur | `switch.echo_show_8_keep_screen_on` / `button.echo_show_8_postpone_screensaver` |
| Navigation | `select.echo_show_8_dashboard_view` |

Valeurs du select confirmées : `dashboard-kiosk/menu`, `dashboard-kiosk/lecture` et
`dashboard-kiosk/music-browser`. La navigation est ainsi testée sans capteur d'URL supplémentaire.

## Phase 1 — Vue `lecture` dans le dashboard kiosque

Carte et vue Lecture sont en place dans HA. Seule la configuration de `lecture` a été changée;
`music-browser` conserve son rôle de navigation dans la bibliothèque.

Ajout dans `dashboards/home-assistant/kiosk.json` (après `music-browser`) :

```json
{
  "title": "Lecture",
  "path": "lecture",
  "icon": "mdi:play-circle-outline",
  "type": "panel",
  "cards": [
    {
      "type": "custom:touch-music-now-playing",
      "height": 520,
      "config_entry_id": "01M5A0HX0XF615ZESGP58DV3YW",
      "players": ["media_player.echo_show_8_2", "media_player.denon_avr_x3500h_3"],
      "browser_path": "/dashboard-kiosk/menu"
    }
  ]
}
```

## Phase 2 — Contexte de lecture (sans helper dédié)

Le capteur Template initialement envisagé n'a pas été créé. La carte et les automatisations lisent
directement les deux lecteurs autorisés; les triggers de pause vérifient que ni l'un ni l'autre ne
joue encore. Le provider et le compte Spotify sont lus depuis la réponse MA `get_queue` lorsqu'ils
sont disponibles.

## Phase 3 — Carte `custom:touch-music-now-playing`

Dans le dépôt, la carte est enregistrée comme `custom:touch-music-now-playing` dans le bundle HACS
`touch_music` (JS `2.5.0-local.13`, manifest `1.1.11`); elle n'a pas d'éditeur séparé. Le service
`touch_music.get_track_lyrics` utilise le client MA authentifié de HA pour récupérer le LRC, sans
exposer de jeton au navigateur. Le code est local et doit être déployé; HA doit redémarrer pour
enregistrer le nouveau service backend.

### 3.1 Sélection du lecteur
1. La carte observe seulement les deux lecteurs déclarés dans la vue.
2. Si plusieurs lecteurs jouent, elle montre une rangée de boutons pour choisir le contexte; le
  choix reste actif tant que ce lecteur joue.
3. Sinon, elle choisit le lecteur en pause le plus récemment changé, puis affiche « Rien en lecture »
  si aucun des deux n'est actif. Le bouton Menu ouvre `browser_path`.

### 3.2 Rendu (maquette)
- Fond : pochette (`entity_picture`) en `background` flouté (`filter: blur(40px) saturate(1.2)`),
  voile sombre ; pas d'animation continue (perf Echo Show).
- Pochette 1:1 coins arrondis, à gauche ; à droite : titre (2 lignes max, ellipsis), artiste,
  album.
- Pastille haut-droite : « Lecture en cours » / « En pause » + nom du lecteur + icône provider
  (Spotify + compte, radio, externe).
- Barre de progression : placée juste au-dessus des boutons transport; position calculée
  `media_position + (now - media_position_updated_at)` si lecture active, rafraîchie 1×/s avec un
  timer relancé à la reconnexion de la carte; seek au toucher (`media_player.media_seek`).
- Transport : précédent / lecture-pause (gros bouton blanc, ≥ 64 px) / suivant.
- Rangée d'actions (≥ 48 px) : volume, ♥ favori si un compte correspondant est disponible,
  aléatoire, répétition (états actifs colorés), file d'attente. Volume en bas avec curseur et pas de 5 %.
- Paroles : bouton affiché seulement si MA renvoie du LRC horodaté; bascule la zone de pochette vers
  les lignes de paroles et centre automatiquement la ligne correspondant à la position du morceau.
  Si aucun LRC n'est disponible, le bouton reste masqué.

### 3.3 Actions selon le contexte
| Bouton | `origine = music_assistant` | `origine = externe` |
|---|---|---|
| Transport, seek, volume | `media_player.*` sur le lecteur | idem si `supported_features` le permet, sinon masqué |
| Aléatoire / répétition | `media_player.shuffle_set` / `repeat_set` si supporté | idem si supporté |
| ♥ Favori | SpotifyPlus `save_track_favorites` / `remove_track_favorites` pour le compte associé au provider | masqué |
| File | `music_assistant.get_queue` (`return_response`) → panneau liste | masqué |
| Paroles | `touch_music.get_track_lyrics` → MA `metadata/get_track_lyrics`; affichage LRC synchronisé si disponible | masqué |

Gestion des `supported_features` par bit (pas par nom de lecteur) ; si une action échoue,
toast court, pas de blocage UI.

### 3.4 Configuration
La vue fournit directement les lecteurs, le chemin du menu et l'entrée MA; la carte n'a pas encore
d'éditeur visuel distinct.

## Phase 4 — Automatisations (catégorie « Kiosk »)

Trois automatisations sont actives et classées dans la catégorie Kiosk (`01M5HZ29N1SCSCJPJGPJC9179K`).
Pendant lecture, elles peuvent désactiver la gestion automatique et réveiller l'écran; en fin de lecture,
elles réactivent la gestion automatique. Elles ne déclenchent jamais directement l'économiseur.
L'entité du lecteur Denon est surveillée, mais c'est l'Echo Show qui est réveillé et navigué.

### A1 — Musique démarre → réveil + vue Lecture
```yaml
alias: Kiosk - Économiseur selon la lecture
id: kiosk_screensaver_music_players
mode: restart
triggers:
  - trigger: state
    entity_id: [media_player.echo_show_8_2, media_player.denon_avr_x3500h_3]
    to: playing
  - trigger: state
    entity_id: [media_player.echo_show_8_2, media_player.denon_avr_x3500h_3]
    to: buffering
  - trigger: homeassistant
    event: start
actions:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ states('media_player.echo_show_8_2') in ['playing', 'buffering'] or states('media_player.denon_avr_x3500h_3') in ['playing', 'buffering'] }}"
          - condition: template
            value_template: "{{ states('select.echo_show_8_dashboard_view') != 'dashboard-kiosk/music-browser' }}"
        sequence:
          - action: switch.turn_off
            target: { entity_id: switch.echo_show_8_screensaver_active }
            continue_on_error: true
          - action: switch.turn_off
            target: { entity_id: switch.echo_show_8_screensaver }
          - action: light.turn_on
            target: { entity_id: light.echo_show_8_screen }
          - action: select.select_option
            target: { entity_id: select.echo_show_8_dashboard_view }
            data: { option: dashboard-kiosk/lecture }
```
Active. Si l'Echo est déjà sur `music-browser`, le second choix ne s'exécute pas. Sinon,
l'automatisation désactive la gestion automatique, réveille l'écran et ouvre Lecture.

### A2 — Musique arrêtée → gestion auto de l'économiseur
```yaml
alias: Kiosk - Lecture terminée : gestion auto screensaver
id: kiosk_lecture_fin
initial_state: true
mode: restart
triggers:
  - trigger: state
    entity_id: [media_player.echo_show_8_2, media_player.denon_avr_x3500h_3]
    from: [playing, buffering]
    to: [paused, idle, off, standby]
conditions:
  - condition: template
    value_template: "{{ states('media_player.echo_show_8_2') not in ['playing', 'buffering'] and states('media_player.denon_avr_x3500h_3') not in ['playing', 'buffering'] }}"
actions:
  - action: switch.turn_on
    target: { entity_id: switch.echo_show_8_screensaver }
```
Active. La règle réactive la gestion automatique sans changer la vue; elle ne bascule pas
`switch.echo_show_8_screensaver_active` à `on`. Kiosk Satellite déclenche l'économiseur selon son
délai d'inactivité configuré (30 s observés). Une navigation après la pause reste donc en place.

### A3 — Veille déclenchée pendant la lecture → vue Lecture
```yaml
alias: Kiosk - Veille pendant lecture vers Lecture
id: kiosk_lecture_anti_veille
initial_state: true
mode: restart
triggers:
  - trigger: state
    entity_id: switch.echo_show_8_screensaver_active
    to: "on"
  - trigger: state
    entity_id: light.echo_show_8_screen
    to: "off"
conditions:
  - condition: template
    value_template: "{{ states('media_player.echo_show_8_2') in ['playing', 'buffering'] or states('media_player.denon_avr_x3500h_3') in ['playing', 'buffering'] }}"
actions:
  - action: switch.turn_off
    target: { entity_id: switch.echo_show_8_screensaver }
  - action: switch.turn_off
    target: { entity_id: switch.echo_show_8_screensaver_active }
  - action: light.turn_on
    target: { entity_id: light.echo_show_8_screen }
  - action: select.select_option
    target: { entity_id: select.echo_show_8_dashboard_view }
    data: { option: dashboard-kiosk/lecture }
```
Active. Si l'utilisateur navigue manuellement vers une autre vue pendant la lecture, aucune action ne
la redirige; seule une mise en veille effective réaffiche Lecture. L'automatisation ne presse pas le
bouton de report.

L'ancienne règle `kiosk_lecture_keepalive` qui pressait `button.echo_show_8_postpone_screensaver`
a été supprimée. La gestion de l'inactivité appartient maintenant au Kiosk Satellite.

### Affectation de la catégorie
Catégorie vérifiée par `config/entity_registry/list` : les trois automatisations ci-dessus portent
`categories.automation = 01M5HZ29N1SCSCJPJGPJC9179K`. Aucune autre automatisation n'a été modifiée.

## Phase 5 — Recette (sur l'Echo Show)

| # | Scénario | Attendu |
|---|---|---|
| 1 | Echo en veille, lancement Spotify Benoît sur Echo via MA | Réveil, vue Lecture, pastille « Spotify · Benoît » |
| 2 | Echo en veille, lecture sur Denon (compte Sandrine) | Réveil, vue Lecture, lecteur Denon affiché |
| 3 | Echo sur `music-browser`, lancement d'un titre | Aucune navigation |
| 4 | Lecture en cours, attendre le délai d'économiseur | Gestion auto désactivée; si la veille démarre malgré tout, A3 réveille et affiche Lecture |
| 5 | Pause puis navigation utilisateur | La vue choisie reste affichée; gestion auto réactivée immédiatement et déclenchement confié à Kiosk Satellite |
| 6 | Pause puis reprise en < 7 s | Pas de veille |
| 7 | Deux lecteurs actifs | Puces de choix, lecteur prioritaire = Echo |
| 8 | Source externe (Spotify Connect / AirPlay direct) | Carte affichée, boutons MA masqués |
| 9 | Lecteur `unavailable` en cours de lecture | Pas d'erreur JS, état vide propre |
| 10 | Reboot HA / redémarrage app Kiosk | Pas de navigation intempestive (A1 ne part que de `off`) |

## Décisions intégrées

- **Lecteurs :** Echo Show + Denon AVR-X3500H uniquement.
- **Q2** Pendant la lecture, si l'utilisateur navigue vers `eclairage`/`meteo`, faut-il le ramener
  sur Lecture ? **Non : respecter la navigation manuelle. Seule la mise en veille pendant lecture
  renvoie vers Lecture.**
- **Après pause :** ne pas changer la vue; réactiver immédiatement la gestion automatique et laisser Kiosk Satellite déclencher l'économiseur.
- **Paroles :** bouton et vue LRC uniquement quand le service MA renvoie des lignes horodatées.
