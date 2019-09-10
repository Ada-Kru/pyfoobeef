from collections import namedtuple
from .models import PlayerState, Playlists, PlaylistItems, BrowserEntry

Endpoint = namedtuple("Endpoint", ["method", "endpoint", "model"])

ADD_PLAYLIST = Endpoint("POST", "/playlists/add", None)
ADD_PLAYLIST_ITEMS = Endpoint(
    "POST", "/playlists/{playlist_ref}/items/add", None
)
BROWSER_ENTRIES = Endpoint("GET", "/browser/entries", BrowserEntry)
BROWSER_ROOTS = Endpoint("GET", "/browser/roots", BrowserEntry)
CLEAR_PLAYLIST = Endpoint("POST", "/playlists/{playlist_ref}/clear", None)
COPY_BETWEEN_PLAYLISTS = Endpoint(
    "POST",
    "/playlists/{source_playlist_ref}/{dest_playlist_ref}/items/copy",
    None,
)
COPY_PLAYLIST_ITEMS = Endpoint(
    "POST", "/playlists/{playlist_ref}/items/copy", None
)
GET_ARTWORK = Endpoint("GET", "/artwork/{playlist_ref}/{index}", None)
GET_PLAYER_STATE = Endpoint("GET", "/player", PlayerState)
MOVE_BETWEEN_PLAYLISTS = Endpoint(
    "POST",
    "/playlists/{source_playlist_ref}/{dest_playlist_ref}/items/move",
    None,
)
MOVE_PLAYLIST = Endpoint(
    "POST", "/playlists/move/{playlist_ref}/{new_index}", None
)
MOVE_PLAYLIST_ITEMS = Endpoint(
    "POST", "/playlists/{playlist_ref}/items/move", None
)
PAUSE = Endpoint("POST", "/player/pause", None)
PAUSE_TOGGLE = Endpoint("POST", "/player/pause/toggle", None)
PLAY = Endpoint("POST", "/player/play", None)
PLAYLIST_ITEMS = Endpoint("GET", "/query", PlaylistItems)
PLAYLIST_QUERY = Endpoint("GET", "/query", Playlists)
PLAY_NEXT = Endpoint("POST", "/player/next", None)
PLAY_PREVIOUS = Endpoint("POST", "/player/previous", None)
PLAY_RANDOM = Endpoint("POST", "/player/play/random", None)
PLAY_SPECIFIC = Endpoint("POST", "/player/play/{playlist_ref}/{index}", None)
REMOVE_PLAYLIST = Endpoint("POST", "/playlists/remove/{playlist_ref}", None)
REMOVE_PLAYLIST_ITEMS = Endpoint(
    "POST", "/playlists/{playlist_ref}/items/remove", None
)
SET_CURRENT_PLAYLIST = Endpoint("POST", "/playlists", None)
SET_PLAYER_STATE = Endpoint("POST", "/player", None)
SORT_PLAYLIST_ITEMS = Endpoint(
    "POST", "/playlists/{playlist_ref}/items/sort", None
)
STOP = Endpoint("POST", "/player/stop", None)
UPDATE_PLAYLIST = Endpoint("POST", "/playlists/{playlist_ref}", None)
