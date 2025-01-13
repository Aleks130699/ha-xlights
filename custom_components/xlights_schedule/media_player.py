"""Support for the FPP."""

from __future__ import annotations

import logging
import socket
import urllib.parse

import requests
import aiohttp
import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA as MEDIA_PLAYER_PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    STATE_IDLE,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


DEFAULT_NAME = "xLights Schedule"

PLATFORM_SCHEMA = MEDIA_PLAYER_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=7075): cv.string,
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the xLightSchedule platform."""
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    name = config[CONF_NAME]
    password = config[CONF_PASSWORD]

    xLightsSchedule = xSchedule(host=host, port=port, name=name, password=password)

    add_entities([xLightsSchedule])

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the xLightSchedule platform."""
    # CONF_NAME is only present in imported YAML.
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT)
    name = entry.data.get(CONF_NAME)
    password = entry.data.get(CONF_PASSWORD)
    # base_url: str = (
    #     f"http://{host}:{port}"
    # )
    # url = f"{base_url}/xScheduleStash?Command=Retrieve&Key=uiSettings"
    # async with aiohttp.ClientSession() as session:
    #     response = await session.get(url)
    #     content = await response.json()

    xLightsSchedule = xSchedule(host=host, port=port, name=name, password=password)

    async_add_entities([xLightsSchedule], True)



class xSchedule(MediaPlayerEntity):
    """Representation of a xLights Schedule"""

    _attr_supported_features = (
        MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.REPEAT_SET
    )

    def __init__(
        self,
        host: str,
        port: str,
        name: str,
        password: str | None,
    ) -> None:
        """Initialize the Player."""
        self._host: str = host
        self._port: str = port
        self._attr_name: str = name
        self._pass: str | None = password

        self._base_url: str = (
            f"http://{self._host}:{self._port}"
        )
        self._attr_media_content_type = MediaType.MUSIC
        self._attr_unique_id: str = f"media_player_{name}"
        self._playlists = []
        self._available: bool = False
        # self._state = STATE_IDLE
        # self._volume = 0
        # self._media_title = ""
        # self._media_playlist = ""
        # self._playlists = []
        # self._media_duration = 0
        # self._media_position = 0
        # self._media_position_updated_at = datetime.datetime.now()
        # self._attr_unique_id = "media_player_{name}"
        # # self._available = False


    def update(self):
        """Get the latest state from the player."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((self._host, int(self._port)))
        if result != 0:
            self._state = STATE_OFF
            self._available = False
        else:
            # Pulls status even if fppd is not running.
            status_url = f"{self._base_url}/xScheduleQuery?Query=GetPlayingStatus"
            status = requests.get(
                url=status_url,
                timeout=10,
            ).json()

            self._state = status.get("status")
            #self._volume = int(status.get["volume"]) / 100
            self._attr_volume_level = (
                int(status.get("volume")) / 100 if int(status.get("volume")) else 0
            )
            if self._attr_volume_level == 0:
                self._attr_is_volume_muted = True
            else:
                self._attr_is_volume_muted = False

            if self._state == "playing":
                self._attr_media_title = status.get("step")
                self._attr_media_playlist = status.get("playlist")
                if status.get("random") == "true":
                    self._attr_shuffle = True
                else:
                    self._attr_shuffle = False
                if status.get("steplooping") == "true":
                    self._attr_repeat = "one"
                elif status.get("playlistlooping") == "true":
                    self._attr_repeat = "all"
                else:
                    self._attr_repeat = "off"
                self._attr_media_duration = int(status.get("lengthms")) / 1000
                self._attr_media_position = int(status.get("positionms")) / 1000
                self._attr_media_position_updated_at = dt_util.utcnow()

            elif self._state != STATE_PAUSED:
                self._attr_media_title = None
                self._attr_media_playlist = None
                self._attr_media_duration = None
                self._attr_media_position = None
                self._attr_media_position_updated_at = None
                self._attr_media_image_url = None

            playlists_url = f"{self._base_url}/xScheduleQuery?Query=GetPlayLists"
            playlists = requests.get(
                url=playlists_url,
                timeout=10,
            ).json()
            playlists = playlists.get("playlists")
            self._playlists.clear()
            for i in range(len(playlists)):
                self._playlists.append(playlists[i]['name']);
            self._attr_source_list = self._playlists

            self._available = True

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if self._state in [None, STATE_OFF, "stopped"]:
            return MediaPlayerState.OFF
        if self._state == STATE_IDLE:
            return MediaPlayerState.IDLE
        if self._state == STATE_PLAYING:
            return MediaPlayerState.PLAYING
        if self._state == STATE_PAUSED:
            return MediaPlayerState.PAUSED

        return MediaPlayerState.IDLE

    @property
    def available(self) -> bool:
        """Media Device is Available."""
        return self._available

    def turn_off(self) -> None:
        """Stop FFP Daemon."""
        url = f"{self._base_url}/xScheduleCommand?Command=Deactivate all schedules"
        requests.get(
            url=url,
            timeout=10,
        )

    def turn_on(self) -> None:
        """Start FFP Daemon."""
        url = f"{self._base_url}/xScheduleCommand?Command=Activate all schedules"
        requests.get(
            url=url,
            timeout=10,
        )

    def select_source(self, source: str) -> None:
        """Choose a playlist to play."""
        playlist_url = urllib.parse.quote_plus(source, safe='', encoding=None, errors=None)
        url = f"{self._base_url}/xScheduleCommand?Command=Play specified playlist&Parameters={playlist_url}"
        requests.get(
            url=url,
            timeout=10,
        )

    def set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        volume = int(volume * 100)
        #_LOGGER.debug("fpp volume is %s", volume)
        url = f"{self._base_url}/xScheduleCommand?Command=Set volume to&Parameters="f"{volume}"
        requests.get(
            url=url,
            timeout=10,
        )

    def volume_up(self) -> None:
        """Increase volume by 1 step."""
        url = f"{self._base_url}/xScheduleCommand?Command=Adjust volume by&Parameters=1"
        requests.get(
            url=url,
            timeout=10,
        )

    def volume_down(self) -> None:
        """Decrease volume by 1 step."""
        url = f"{self._base_url}/xScheduleCommand?Command=Adjust volume by&Parameters=-1"
        requests.get(
            url=url,
            timeout=10,
        )

    def mute_volume(self, mute: bool) -> None:
        """Decrease volume by 1 step."""
        print(mute)
        if mute == True:
            url = f"{self._base_url}/xScheduleCommand?Command=Set volume to&Parameters=0"
        else:
            if self._attr_volume_level != 0:
                return
            url = f"{self._base_url}/xScheduleCommand?Command=Toggle mute"

        requests.get(
            url=url,
            timeout=10,
        )

    def media_stop(self) -> None:
        """Immediately stop all FPP Sequences playing."""
        url = f"{self._base_url}/xScheduleCommand?Command=Stop"
        requests.get(
            url=url,
            timeout=10,
        )

    def media_play(self) -> None:
        """Resume FPP Sequences playing."""
        url = f"{self._base_url}/xScheduleCommand?Command=Pause"
        requests.get(
            url=url,
            timeout=10,
        )

    def media_pause(self) -> None:
        """Pause FPP Sequences playing."""
        url = f"{self._base_url}/xScheduleCommand?Command=Pause"
        requests.get(
            url=url,
            timeout=10,
        )

    def media_next_track(self) -> None:
        """Next FPP Sequences playing."""
        url = f"{self._base_url}/xScheduleCommand?Command=Next step in current playlist"
        requests.get(
            url=url,
            timeout=10,
        )

    def media_previous_track(self) -> None:
        """Prev FPP Sequences playing."""
        url = f"{self._base_url}/xScheduleCommand?Command=Prior step in current playlist"
        requests.get(
            url=url,
            timeout=10,
        )

    def media_seek(self, position: float) -> None:
        """Seek FPP Sequences playing."""
        position = int(position * 1000)
        url = f"{self._base_url}/xScheduleCommand?Command=Set step position ms&Parameters={position}"
        requests.get(
            url=url,
            timeout=10,
        )
    def set_shuffle(self, shuffle: bool) -> None:
        """Prev FPP Sequences playing."""
        url = f"{self._base_url}/xScheduleCommand?Command=Toggle current playlist random"
        requests.get(
            url=url,
            timeout=10,
        )
    def set_repeat(self, repeat: str) -> None:
        """Prev FPP Sequences playing."""
        if repeat == "one":
            url = f"{self._base_url}/xScheduleCommand?Command=Toggle loop current step"
            requests.get(
                url=url,
                timeout=10,
            )
        if repeat == "all":
            url = f"{self._base_url}/xScheduleCommand?Command=Toggle current playlist loop"
            requests.get(
                url=url,
                timeout=10,
            )
        if repeat == "off" and self._attr_repeat != "off":
            url = f"{self._base_url}/xScheduleCommand?Command=Toggle loop current step"
            requests.get(
                url=url,
                timeout=10,
            )
            url = f"{self._base_url}/xScheduleCommand?Command=Toggle current playlist loop"
            requests.get(
                url=url,
                timeout=10,
            )

