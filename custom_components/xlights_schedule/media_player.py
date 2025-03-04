"""Support for the xLights Schedule."""
import logging
import requests
import time
import datetime
import voluptuous as vol
import socket

SECONDS_BETWEEN_LIBRARY_REFRESH = 500
CURRENTLY_LOGGING = False

_LOGGER = None
if CURRENTLY_LOGGING:
    _LOGGER = open('./log.txt','w+')#logging.getLogger(__name__)

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    ATTR_MEDIA_ENQUEUE,
    BrowseMedia,
    MediaPlayerEnqueue,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
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


DEFAULT_NAME = "xLights Schedule"

SUPPORT_XLIGHTS = (
    MediaPlayerEntityFeature.BROWSE_MEDIA
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    # | MediaPlayerEntityFeature.REPEAT_SET
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.SHUFFLE_SET
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.TURN_OFF
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
        self._last_update = 0
        self._media_title = ""
        self._media_playlist = ""
        self._playlists = {}
        self._media_duration = 0
        self._media_position = 0
        self._media_position_updated_at = datetime.datetime.now()
        self._attr_unique_id = "media_player_{name}"
        self._attr_shuffle = False
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
                self._attr_shuffle = status["random"].upper() == "TRUE"
            
            # Only update playlists once every UPDATE seconds
            if time.time() - self._last_update < SECONDS_BETWEEN_LIBRARY_REFRESH:
                return 
                
            self._last_update = time.time()
            playlists = requests.get(
                "http://%s/xScheduleQuery?Query=GetPlayLists" % (self._host)
            ).json()
            playlists = playlists["playlists"]
            self._playlists.clear()
            for i in range(len(playlists)):
                name = playlists[i]['name']
                self._playlists[name] = self.all_songs_for_playlist(name)
                log("{}",self._playlists[name])
            log("{}",self._playlists)
                
        
            

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
        log("Media title {}",self._media_title)
        return self._media_title

    @property
    def media_playlist(self):
        """Title of current playlist."""
        log("Playlist {}",self._media_playlist)
        return self._media_playlist

    @property
    def source_list(self):
        """Return available playlists"""
        log("Playlists:{}",self._playlists)
        return list(self._playlists.keys())

    @property
    def source(self):
        """Return the current playlist."""
        log("Playing Playlist:{}",self._media_playlist)
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
    
    @property
    def shuffle(self) -> bool | None:
        """Boolean if shuffle is enabled."""
        return self._attr_shuffle

    def select_source(self, source):
        """Choose a playlist to play."""
        requests.get("http://%s/xScheduleCommand?Command=Play specified playlist&Parameters=%s" % (self._host, source))

    def set_volume_level(self, volume):
        """Set volume level."""
        volume = int(volume * 100)
        #log("New Volume: {}",volume)
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
        
    def set_shuffle(self, shuffle: bool) -> None:
        """Enable/disable shuffle mode."""
        requests.get("http://%s/xScheduleCommand?Command=Toggle current playlist random" % (self._host))
    
    # Used as a STOP button the power button shows up but the STOP button wont
    def turn_off(self) -> None:
        """Send stop command."""
        requests.get("http://%s/xScheduleCommand?Command=Stop" % (self._host)) # url_encode_string(self._media_playlist)
    
    
    def play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: any
    ) -> None:
        """Play a piece of media."""
        log("Playing song:{},{}",media_type,media_id)
        # ID contains the <playlist>,<song>
        (playlist, song) = media_id.split(',')
        req_url = "http://{}/xScheduleCommand?Command={}&Parameters={},{}".format(self._host,url_encode_string("Play playlist starting at step"),url_encode_string(playlist),url_encode_string(song))
        requests.get(req_url)
        
        requests.get

    async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        log("====")
        log("{}\n{}\n{}",self,media_content_type,media_content_id)
        log("====")
        
        if media_content_type == None:
            return self.all_playlists()
        if media_content_type == "playlist":
            log("Returning {} | {}",media_content_id,self._playlists[media_content_id])
            return BrowseMedia(
            can_expand=True,
            can_play=False,
            children_media_class="music",
            media_class="playlist",
            media_content_id=media_content_id,
            media_content_type="playlist",
            title=media_content_id, # Gets the name of the playlist
            thumbnail=None,
            children = self._playlists[media_content_id]
        )
            
        


    def all_playlists(self) -> BrowseMedia:
        return BrowseMedia(
            can_expand=True,
            can_play=False,
            children_media_class="playlist",
            media_class="directory",
            media_content_id="Available Playlists",
            media_content_type="playlist",
            thumbnail=None,
            title="Playlists",
            children= self.all_playlists_payload()
        )
        
    def all_playlists_payload(self)-> list[BrowseMedia]:
        media_list = []
        for name in self._playlists:
            media_list.append(
                BrowseMedia(
            can_expand=True,
            can_play=False,
            children_media_class="music",
            media_class="playlist",
            media_content_id=name,
            media_content_type="playlist",
            title=name, # Gets the name of the playlist
            thumbnail=None,
        ))
        
        return media_list
    
    def all_songs_for_playlist(self, name)-> list[BrowseMedia]:
        log("http://%s/xScheduleQuery?Query=GetPlayListSteps&Parameters=%s" % (self._host,url_encode_string(name)))
        songs = requests.get("http://%s/xScheduleQuery?Query=GetPlayListSteps&Parameters=%s" % (self._host,url_encode_string(name))).json()
        songs = songs["steps"]
        song_list = []
        
        for song in songs:
            song_list.append(BrowseMedia(
            can_expand=False,
            can_play=True,
            media_class="music",
            media_content_id=name + ',' + song["name"], #Encode ID w/ <playlist>,<song>
            media_content_type="music",
            title=song["name"],
            thumbnail=None,
        ))
        #log(song_list)
        return song_list
            
            
def log(string, *args):
    if not CURRENTLY_LOGGING:
        return
    _LOGGER.write(string.format(*args) + "\n")
    _LOGGER.flush()
    
    
    
def _fix_string(string):
  	return string[2:].zfill(2)

def _encode_component(component):
    """Encodes a single URL component (key or value)."""
    if component.isalnum() or component in "-_.~":
        return component
    return "%{}".format(_fix_string(hex(ord(component)))).upper()

def url_encode_string(string):
  total = ""
  for char in string:
    total+=_encode_component(char)
  
  return total