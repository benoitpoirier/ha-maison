# Plan de dev — touch_music : sélection de « music sources » (comptes Spotify via utilisateurs MA)

## Objectif

Permettre de choisir, depuis la carte `custom:touch-music-card-local`, la source musicale active
(un compte Spotify par utilisateur Music Assistant), en mode exclusif, via une rangée de boutons
placée sous le choix du lecteur. La source active filtre les catégories, la recherche et pilote
la lecture, afin de ne jamais solliciter l'autre compte Spotify.

## Décisions déjà prises (ne pas remettre en cause)

- **Aucun backend Python, aucun jeton.** On s'appuie sur le champ `username` des actions HA
  `music_assistant.get_library`, `music_assistant.search` et `music_assistant.play_media`.
  MA applique alors le `provider_filter` de l'utilisateur (filtrage des résultats + choix du compte
  au moment du streaming, via `queue.userid`).
- Utilisateurs MA existants : `kiosk_benoit`, `kiosk_sandrine` (chacun avec un `provider_filter`
  limité à son instance Spotify + sources communes).
- Pas de bouton « Toutes » : une source est toujours active.
- Pas de tuiles manuelles à gérer (seules les catégories `source` sont utilisées).
- La source choisie est **conservée après un refresh** (par appareil).
- Ajouter la langue **française** (`fr`) à la carte et à l'éditeur.
- Sans `music_sources` dans la config : comportement strictement identique à l'actuel.

## Fichiers concernés

- `custom_components/touch_music/www/touch-music-card.js` (seul fichier modifié pour le code)
- `custom_components/touch_music/manifest.json` (version)
- `dashboards/home-assistant/kiosk.json` (exemple de config, vue `decouvrir`) — uniquement si demandé

## État validé côté Music Assistant (2026-10-22, API MA 2.10.7, lecture seule)

| Élément | Valeur |
|---|---|
| Instances Spotify | `spotify--vBxfzzeZ` « Spotify Benoit », `spotify--zo8KgLJX` « Spotify Sandrine » (toutes deux disponibles) |
| Autres sources | `builtin`, `ambient_sounds` |
| `kiosk_benoit` | rôle `user`, activé, `provider_filter: [spotify--vBxfzzeZ]` |
| `kiosk_sandrine` | rôle `user`, activé, `provider_filter: [spotify--zo8KgLJX]` |

- `music/playlists/library_items` avec `user` : listes **différentes** par utilisateur, uniquement
  les playlists ayant un mapping sur le compte de l'utilisateur. ✅
- `music/search` avec `user` : résultats en URI de l'instance de l'utilisateur
  (`spotify--zo8KgLJX://…` pour Sandrine, `spotify--vBxfzzeZ://…` pour Benoît). ✅
- ⚠️ La recherche sur l'instance de Benoît a renvoyé **à vide après ~8 s** sur certaines requêtes
  (timeout côté MA/Spotify, aussi sans filtre utilisateur). La carte doit afficher « Aucun résultat »
  proprement ; ne pas confondre avec un bug du filtre.
- `ambient_sounds` n'est dans aucun `provider_filter` : ces sons ne seront pas visibles quand une
  source est active (à ajouter dans MA si souhaité).

Reste à valider côté Home Assistant (ci-dessous) : l'emprunt d'identité via le champ `username`
des actions HA, et le test de lecture.

## Phase 0 — Validation préalable (bloquante, manuelle, lecture seule)

À faire dans HA > Outils de développement > Actions avant de coder. `config_entry_id` du kiosque :
`01M5A0HX0XF615ZESGP58DV3YW`.

```yaml
action: music_assistant.search
data:
  config_entry_id: 01M5A0HX0XF615ZESGP58DV3YW
  name: Daft Punk
  media_type: [playlist]
  limit: 5
  username: kiosk_benoit
```

```yaml
action: music_assistant.get_library
data:
  config_entry_id: 01M5A0HX0XF615ZESGP58DV3YW
  media_type: playlist
  limit: 10
  username: kiosk_sandrine
```

Critères :
1. Le champ `username` est accepté (sinon : version HA trop ancienne → stop).
2. Pas d'erreur de permission (sinon : le compte de l'intégration n'a pas `users.impersonate` → stop).
3. Les playlists retournées diffèrent entre `kiosk_benoit` et `kiosk_sandrine` (sinon : vérifier les
   `provider_filter` dans MA > Settings > Users).
4. Un `play_media` avec `username: kiosk_benoit` sur `media_player.echo_show_8_2` ne déconnecte pas
   le compte Spotify de Sandrine (vérifier dans l'app Spotify).

## Phase 1 — Modèle de configuration

Nouvelle clé optionnelle :

```yaml
music_sources:
  - name: Benoît
    username: kiosk_benoit
    icon: mdi:spotify
  - name: Sandrine
    username: kiosk_sandrine
    icon: mdi:account-music
```

- `name` : libellé (title du bouton), `username` : obligatoire, `icon` : optionnel (défaut `mdi:spotify`).
- Ignorer les entrées sans `username`.

## Phase 2 — État de la carte (`MusicAssistantTouchCard`)

1. `setConfig(config)` : calculer `this._sources = (config.music_sources || []).filter((s) => s && s.username)`
   puis restaurer la sélection (voir persistance). Ne pas lever d'erreur si la liste est vide.
2. Helpers :
   - `_sourceCfg()` → source active ou `null` si aucune source configurée.
   - `_user()` → `this._sourceCfg()?.username` ou `undefined`.
   - `_avecUser(data)` → ajoute `username` à l'objet `data` seulement si `_user()` est défini.
3. Persistance :
   - Clé `localStorage` : `touch_music:source:${config_entry_id}:${location.pathname}`.
   - Valeur stockée : le **`username`** (pas l'index, pour résister au réordonnancement).
   - À la restauration : si le `username` stocké n'existe plus dans `this._sources`, prendre l'index 0.
   - Encapsuler les accès `localStorage` dans `try/catch` (navigateurs kiosque en mode privé).

## Phase 3 — Interface (rangée de boutons sous les lecteurs)

1. `_bouw()` : juste après `<div class="zones" id="zones"></div>`, ajouter
   `<div class="zones sources" id="sources" style="--zn:${this._sources.length}"></div>`,
   rendu **uniquement** si `this._sources.length > 0`.
2. CSS (`STYLE`) : réutiliser `.zones` ; ajouter seulement `.sources { margin-top:6px; }`.
   Vérifier que la colonne gauche tient toujours sur l'Echo Show 8 (la zone `.np` est flexible).
3. `_tekenSources()` calqué sur `_tekenZones()` :
   `<button data-act="src" data-i="${i}" title="${esc(s.name)}" class="${i === this._src ? 'on' : ''}">${svg(s.icon || 'mdi:spotify')}</button>`.
   Appeler depuis `_bouw()` après `_tekenZones()`.
4. `_klik()` : `else if (a === 'src') this._wisselSource(i);`
5. `_wisselSource(i)` :
   - si `i === this._src` → return ;
   - `this._src = i` ; persister le `username` ;
   - vider `this._bron`, `this._bezigBron`, `this._res`, `this._det` ; `this._mode = 'home'` ;
   - `_tekenSources()`, `_tekenRechts()`, puis `_vulAan()`.
   - Ne **pas** interrompre la lecture en cours.

## Phase 4 — Appels Music Assistant

| Endroit | Modification |
|---|---|
| `_bronSleutel(b)` | Préfixer la clé par `this._user() || ''` |
| `_bronHaal(b)` | `service_data: this._avecUser(data)` pour `get_library` |
| `_zoek()` | `service_data: this._avecUser({...})` pour `search` |
| `_speel()` | `this._avecUser({ media_id, enqueue, radio_mode })` pour `play_media` |
| `_speelLijst()` | `username` sur le premier `play_media` **et** sur les `enqueue: 'add'` (fonction `bij`) |
| `_wisselZone()` | `username` sur le `play_media` de repli (quand `transfer_queue` échoue) |
| `_open()` | Inchangé (`browse_media` n'accepte pas d'utilisateur ; la lecture qui suit passe par `play_media`) |

Ne pas ajouter `username` aux actions `media_player.*` ni à `transfer_queue` (non supporté).

## Phase 5 — Éditeur (`MusicAssistantTouchCardEditor`)

1. Nouvelle section « Sources musicales », insérée entre la section lecteurs (`zVak`) et les
   catégories (`cVak`), même structure que la section lecteurs :
   - schéma : grid `[name (text), icon (icon)]` puis `username` (text, required) ;
   - `ED_HINT.username = 'usernameHint'` ;
   - bouton « Ajouter une source » ; suppression via `_paneel(..., weg)` ; supprimer la clé
     `music_sources` quand la liste devient vide.
2. Ajouter l'option `{ value: 'fr', label: 'Français' }` dans le select `language`.

## Phase 6 — Traductions

1. Ajouter dans `TAAL.en.ed` et `TAAL.nl.ed` : `sources`, `sourceToe`, `username`, `usernameHint`.
   - en : `'Music sources'`, `'Add source'`, `'Music Assistant user'`,
     `'Username of a Music Assistant user whose provider filter selects the account to use.'`
2. Ajouter `TAAL.fr` complet (toutes les clés de `en`, y compris `soort` et `ed`), traduit en
   français. Aucune clé manquante : comparer les clés de `en` et `fr`.

## Phase 7 — Version

- `VERSIE` → `'2.5.0-local.1'` ; `manifest.json` `version` → `"1.1.0"`.

## Contraintes de code

- Respecter le style existant (noms néerlandais pour les membres internes, pas de framework,
  `esc()` sur toute valeur de config injectée dans le HTML).
- Pas de secret, pas de jeton, pas d'appel direct à MA (port 8095).
- Commentaires : une ligne max, seulement si le code ne parle pas de lui-même.
- Ne pas modifier l'instance HA/MA ; ne pas modifier `kiosk.json` sans demande.

## Critères d'acceptation

1. Config sans `music_sources` : rendu et appels identiques à la version actuelle
   (aucun `username` envoyé, pas de rangée de sources).
2. Avec 2 sources : rangée de 2 boutons sous les lecteurs, un seul `on` à la fois.
3. Changer de source recharge les catégories et vide la recherche ; les playlists affichées
   correspondent au compte choisi.
4. Refresh de la page : la source précédemment choisie est toujours active.
5. Lecture lancée depuis une source : l'app Spotify de l'autre compte n'est pas sollicitée.
6. Éditeur : ajout/suppression/édition des sources fonctionnent, sans perte de focus à la saisie.
7. `language: fr` (ou HA en français) : toute l'interface et l'éditeur sont en français.
8. Aucune erreur console sur la vue `decouvrir`.

## Risques connus (à tester, pas à coder)

- MA bascule sur un autre compte du même service si le compte préféré échoue ou n'a plus de flux
  disponible (deux lecteurs simultanés sur le même compte).
- `transfer_queue` : vérifier que la file conserve l'utilisateur après changement de lecteur.
- « Récemment joués » dépend de l'historique de chaque utilisateur MA (vide au départ).
