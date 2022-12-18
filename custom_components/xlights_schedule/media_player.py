"""Support for the xLights Schedule."""
import logging
import requests
import datetime
import voluptuous as vol
import socket

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    DOMAIN,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_STOP,
    SUPPORT_PLAY,
    SUPPORT_PAUSE,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_NEXT_TRACK,
    SUPPORT_SEEK
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    STATE_IDLE,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "xLights Schedule"

SUPPORT_XLIGHTS = (
    SUPPORT_VOLUME_SET | SUPPORT_VOLUME_STEP | SUPPORT_SELECT_SOURCE | SUPPORT_STOP | SUPPORT_PLAY | SUPPORT_PAUSE | SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | SUPPORT_SEEK
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the FPP platform."""

    add_entities([xLightsSchedule(config[CONF_HOST], config[CONF_NAME])])


class xLightsSchedule(MediaPlayerEntity):
    """Representation of a Falcon Pi Player"""

    def __init__(self, host, name):
        """Initialize the Player."""
        self._host = host
        self._name = name
        self._state = STATE_IDLE
        self._volume = 0
        self._media_title = ""
        self._media_playlist = ""
        self._playlists = []
        self._media_duration = 0
        self._media_position = 0
        self._media_position_updated_at = datetime.datetime.now()
        self._attr_unique_id = "media_player_{name}"
        # self._available = False
        

    def update(self):
        """Get the latest state from the player."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        ip, port = self._host.split(":")
        result = sock.connect_ex((ip,int(port)))
        if result != 0:
            self._state = "off"
        else:
            status = requests.get("http://%s/xScheduleQuery?Query=GetPlayingStatus" % (self._host)).json()
    
            self._state = status["status"] 
            self._volume = int(status["volume"]) / 100
            if self._state == "playing":
                self._media_title = status["step"]
                self._media_playlist = status["playlist"]
                self._media_duration = int(status["lengthms"]) / 1000
                self._media_position = int(status["positionms"]) / 1000
                self._media_position_updated_at = datetime.datetime.now()
            
            # self._available = True
    
            playlists = requests.get(
                "http://%s/xScheduleQuery?Query=GetPlayLists" % (self._host)
            ).json()
            playlists = playlists["playlists"]
            self._playlists.clear()
            for i in range(len(playlists)):
                self._playlists.append(playlists[i]['name']);
                
            # self._last_updated = time.time()

    @property
    def name(self):
        """Return the name of the player."""
        return self._name

    @property
    def state(self):
        """Return the state of the device"""
        if self._state is None:
            return STATE_OFF
        if self._state == "off":
            return STATE_OFF
        if self._state == "idle":
            return STATE_IDLE
        if self._state == "playing":
            return STATE_PLAYING
        if self._state == "paused":
            return STATE_PAUSED

        return STATE_IDLE
        
    # @property
    # def available(self):
    #     """Return if we're available"""

    #     diff = round(time.time() - self._last_updated)
    #     return diff < 30

    @property
    def volume_level(self):
        """Return the volume level."""
        return self._volume

    @property
    def supported_features(self):
        """Return media player features that are supported."""
        return SUPPORT_XLIGHTS

    @property
    def media_title(self):
        """Title of current playing media."""
        return self._media_title

    @property
    def media_playlist(self):
        """Title of current playlist."""
        return self._media_playlist

    @property
    def source_list(self):
        """Return available playlists"""
        return self._playlists

    @property
    def source(self):
        """Return the current playlist."""
        return self._media_playlist

    @property
    def media_position(self):
        """Return the position of the current media."""
        return self._media_position
    
    @property
    def media_position_updated_at(self):
        """Return the time the position of the current media was updated."""
        return self._media_position_updated_at
    
    @property
    def media_duration(self):
        """Return the duration of the current media."""
        return self._media_duration

    def select_source(self, source):
        """Choose a playlist to play."""
        requests.get("http://%s/xScheduleCommand?Command=Play specified playlist&Parameters=%s" % (self._host, source))

    def set_volume_level(self, volume):
        """Set volume level."""
        volume = int(volume * 100)
        _LOGGER.info("volume is %s" % (volume))
        requests.get("http://%s/xScheduleCommand?Command=Set volume to&Parameters=%s" % (self._host, volume))

    def volume_up(self):
        """Increase volume by 1 step."""
        requests.get("http://%s/xScheduleCommand?Command=Adjust volume by&Parameters=1" % (self._host))

    def volume_down(self):
        """Decrease volume by 1 step."""
        requests.get("http://%s/xScheduleCommand?Command=Adjust volume by&Parameters=-1" % (self._host))

    def media_stop(self):
        """Immediately stop all FPP Sequences playing"""
        requests.get("http://%s/xScheduleCommand?Command=Stop" % (self._host))
        
    def media_play(self):
        """Resume FPP Sequences playing"""
        requests.get("http://%s/xScheduleCommand?Command=Pause" % (self._host))
        
    def media_pause(self):
        """Pause FPP Sequences playing"""
        requests.get("http://%s/xScheduleCommand?Command=Pause" % (self._host))
        
    def media_next_track(self):
        """Next FPP Sequences playing"""
        requests.get("http://%s/xScheduleCommand?Command=Next step in current playlist" % (self._host))
        
    def media_previous_track(self):
        """Prev FPP Sequences playing"""
        requests.get("http://%s/xScheduleCommand?Command=Prior step in current playlist" % (self._host))
        
    def media_seek(self, position: float) -> None:
        """Seek FPP Sequences playing"""
        position = int(position * 1000)
        requests.get("http://%s/xScheduleCommand?Command=Set step position ms&Parameters=%s" % (self._host, position))
