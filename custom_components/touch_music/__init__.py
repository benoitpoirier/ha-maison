from pathlib import Path

import voluptuous as vol
from homeassistant.components.music_assistant.helpers import get_music_assistant_client
from homeassistant.components.frontend import add_extra_js_url, remove_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv
from music_assistant_models.media_items import Track

DOMAIN = "touch_music"
CARD_URL = "/touch_music/touch-music-card.js"
WWW_PATH = Path(__file__).parent / "www"
SERVICE_GET_TRACK_LYRICS = "get_track_lyrics"


async def _async_get_track_lyrics(call: ServiceCall) -> dict[str, str | None]:
    mass = get_music_assistant_client(call.hass, call.data["config_entry_id"])
    item = await mass.music.get_item_by_uri(call.data["uri"])
    if not isinstance(item, Track):
        return {"lyrics": None, "lrc_lyrics": None}
    lyrics, lrc_lyrics = await mass.send_command("metadata/get_track_lyrics", track=item)
    return {"lyrics": lyrics, "lrc_lyrics": lrc_lyrics}


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/touch_music", str(WWW_PATH), cache_headers=False)]
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TRACK_LYRICS,
        _async_get_track_lyrics,
        schema=vol.Schema(
            {
                vol.Required("config_entry_id"): cv.string,
                vol.Required("uri"): cv.string,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    add_extra_js_url(hass, CARD_URL)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    remove_extra_js_url(hass, CARD_URL)
    return True
