import json
import urllib3
from urllib.parse import urlencode
from typing import Optional
from .types import PlaylistRef, Paths, ItemIndices, ColumnsMap
from .helper_funcs import param_value_to_str
from .endpoints import (
    GET_PLAYER_STATE,
    SET_PLAYER_STATE,
    PLAY,
    PLAY_SPECIFIC,
    PLAY_RANDOM,
    PLAY_NEXT,
    PLAY_PREVIOUS,
    PLAYLIST_ITEMS,
    PLAYLIST_QUERY,
    STOP,
    PAUSE,
    PAUSE_TOGGLE,
    SET_CURRENT_PLAYLIST,
    ADD_PLAYLIST,
    UPDATE_PLAYLIST,
    REMOVE_PLAYLIST,
    MOVE_PLAYLIST,
    CLEAR_PLAYLIST,
    BROWSER_ROOTS,
    BROWSER_ENTRIES,
    ADD_PLAYLIST_ITEMS,
    COPY_PLAYLIST_ITEMS,
    COPY_BETWEEN_PLAYLISTS,
    MOVE_PLAYLIST_ITEMS,
    MOVE_BETWEEN_PLAYLISTS,
    REMOVE_PLAYLIST_ITEMS,
    SORT_PLAYLIST_ITEMS,
    GET_ARTWORK,
)
from .models import (
    BrowserEntry,
    Playlists,
    PlaylistInfo,
    PlaylistItems,
    PlayerState,
)
from .exceptions import RequestError


class Client:
    """Synchronous class for interacting with the beefweb plugin."""

    _default_column_map = {
        "%album artist%": "album_artist",
        "%album%": "album",
        "%artist%": "artist",
        "%length%": "length",
        "%length_seconds%": "length_seconds",
        "%path%": "path",
        "%title%": "title",
        "%track artist%": "track_artist",
        "%track number%": "track_number",
    }

    def __init__(
        self,
        base_url: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Init.

        :param base_url: The base URL for beefweb's server.  i.e. "localhost"
        :param port: The port number of beefweb's server.
        :param username: The username to use if authentification is enabled in
            beefweb.
        :param password: The password to use if authentification is enabled in
            beefweb.
        """
        if not base_url.lower().startswith("http"):
            base_url = "http://" + base_url
        self.base_url = base_url
        self.port = port
        self._user_pass = None
        if username is not None and password is not None:
            self._user_pass = ":".join((username, password))
        self._http = urllib3.PoolManager()

    def _request(
        self, endpoint, params=None, paths=None, body=None, original_args=None
    ):
        """
        Send a HTTP request to the beefweb server.

        :param endpoint: The endpoint object containing information about the
            endpoint and the return type.
        :param params: Dict containing the parameters to be added to the
            endpoint url.
        :param paths: Dict to be used for formatting the endpoint url.
        :param body: Object to be added as the requests JSON payload.
        :param original_args: Dict containing the original arguments
            passed to the caller.
        :returns: The return type specified in the object passed to the
            endpoint argument.
        :raises: RequestError if beefweb does not accept the request.
        """
        if paths is not None:
            endpoint_path = endpoint.endpoint.format(**paths)
        else:
            endpoint_path = endpoint.endpoint

        url = f"{self.base_url}:{self.port}/api{endpoint_path}"
        if params:
            url += "?" + urlencode(params)
        if body is not None:
            body = json.dumps(body).encode("utf-8")

        headers = urllib3.util.make_headers(basic_auth=self._user_pass)
        # The beefweb server treats header names as case sensitive...
        if "authorization" in headers:
            headers["Authorization"] = headers.pop("authorization")
        response = self._http.request(
            endpoint.method, url, body=body, headers=headers
        )
        self._http.clear()

        # print(url, response.status, response.data, body)
        if response.status not in (200, 204):
            raise RequestError(
                response.status, json.loads(response.data.decode("utf-8"))
            )
        if endpoint.model is not None:
            data = json.loads(response.data.decode("utf-8"))
            # pprint(data)
            if not original_args or "column_map" not in original_args:
                return endpoint.model(data)
            else:
                return endpoint.model(
                    data, column_map=original_args["column_map"]
                )

    def get_player_state(
        self, column_map: Optional[ColumnsMap] = None
    ) -> PlayerState:
        """
        Get the status of the player.

        :param column_map: Dict, list, tuple, or set where each key
            (for dict, set) or item (for list, tuple) is the active item field
            to request.  If a dict is used each value is the attribute name to
            map that key to the returned Column object.

            Names that would be invalid as Python attrubute names may only be
            accessed through subscripting (i.e. "%title%" or "my custom name").

            Examples-
            {"%track artist%": "artist"} will result in the returned object
            having an active_item.columns.artist attribute containing
            information returned from the active item's %track artist% field.

            ["%title%", "%album%"] will result in the returned object
            bieng subscriptable like active_item.columns["%album%"] which will
            return information returned from the active item's %album% field.
        :returns: PlayerState object
        """
        if column_map is None:
            column_map = self._default_column_map
        params = {"columns": param_value_to_str(column_map)}
        return self._request(
            GET_PLAYER_STATE,
            params=params,
            original_args={"column_map": column_map},
        )

    def set_player_state(
        self,
        volume: Optional[float] = None,
        mute: Optional[bool] = None,
        position: Optional[int] = None,
        relative_position: Optional[int] = None,
        playback_mode: Optional[int] = None,
    ) -> None:
        """
        Set the volume level, playback position, and playback order.

        :param volume: Floating point number to set the player's volume level.
            Value may need to be a negative number to work correctly. Use
            information returned by get_player_state to determine the min and
            max values for the connected media player.
        :param mute: True = muted, False = unmuted, None = no change.
        :param position: Sets the position of the current track in seconds.
        :param relative_position: Seconds to Add or subtract from the current
            position.
        :param playback_mode: Number that sets playback order (repeat,
            random, shuffle, etc.)
        """
        kw_map = {}
        if volume is not None:
            kw_map["volume"] = param_value_to_str(volume)
        if mute is not None:
            kw_map["isMuted"] = param_value_to_str(mute)
        if position is not None:
            kw_map["position"] = param_value_to_str(position)
        if relative_position is not None:
            kw_map["relativePosition"] = param_value_to_str(relative_position)
        if playback_mode is not None:
            kw_map["playbackMode"] = param_value_to_str(playback_mode)

        return self._request(
            SET_PLAYER_STATE, params=kw_map, original_args=locals()
        )

    def play(self) -> None:
        """Start playback."""
        self._request(PLAY)

    def play_specific(self, playlist_ref: PlaylistRef, index: int) -> None:
        """
        Start playback of a specific item.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical index
            of the playlist that contains the media to play.
        :param index: The index number of the item to play.
        """
        playlist_ref = param_value_to_str(playlist_ref)
        self._request(PLAY_SPECIFIC, paths=locals())

    def play_random(self) -> None:
        """Play a random item from the active playlist."""
        self._request(PLAY_RANDOM)

    def play_next(self, by: str = None) -> None:
        """
        Play the next item in the active playlist.

        :param by: The media player field used to determine what counts as
            next (i.e. "%title%").  None = use the items index in the
            playlist.
        """
        kw_map = {"by": by} if by is not None else {}
        self._request(PLAY_NEXT, params=kw_map)

    def play_previous(self, by: str = None) -> None:
        """
        Play the previous item in the active playlist.

        :param by: The media player field used to determine what counts as
            previous (i.e. "%title%").  None = use the items index in the
            playlist.
        """
        kw_map = {"by": by} if by is not None else {}
        self._request(PLAY_PREVIOUS, params=kw_map)

    def stop(self) -> None:
        """Stop playback."""
        self._request(STOP)

    def pause(self) -> None:
        """Pause playback."""
        self._request(PAUSE)

    def pause_toggle(self) -> None:
        """Toggle pause state."""
        self._request(PAUSE_TOGGLE)

    def get_playlists(self) -> Playlists:
        """
        Get an object representing the playlists.

        :returns: A Playlists object
        """
        params = {"playlists": "true"}
        return self._request(PLAYLIST_QUERY, params=params)

    def find_playlist(
        self, title: str = None, search_id: str = None
    ) -> Optional[PlaylistInfo]:
        """
        Get an object representing a specific playlist.

        :param title: String representing the playlist's title.
        :param search_id: The id of the playlist.
        :returns: A PlaylistInfo object or None if not found.
        """
        return self.get_playlists().find_playlist(
            title=title, search_id=search_id
        )

    def get_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        offset: int = 0,
        count: int = 1000000,
        column_map: Optional[ColumnsMap] = None,
    ) -> PlaylistItems:
        """
        Get an object representing the items in a specific playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param offset: The start index of the items to retrieve.
        :param count: The amount of items to retrieve.
        :param column_map: Dict, list, tuple, or set where each key
            (for dict, set) or item (for list, tuple) is the item field
            to request.  If a dict is used each value is the attribute name to
            map that key to the returned Column object.

            Names that would be invalid as Python attrubute names may only be
            accessed through subscripting (i.e. "%title%" or "my custom name").

            Examples-
            {"%track artist%": "artist"} will result in the returned object
            having an artist attribute containing information returned from
            the active item's %track artist% field.

            ["%title%", "%album%"] will result in the returned object bieng
            subscriptable like columns["%album%"] which will return
            information returned from the active item's %album% field.
        :returns: A PlaylistItems object.
        """
        if column_map is None:
            column_map = self._default_column_map
        params = {
            "playlistItems": "true",
            "plref": param_value_to_str(playlist_ref),
            "plrange": f"{offset}:{count}",
            "plcolumns": param_value_to_str(column_map),
        }
        return self._request(
            PLAYLIST_ITEMS,
            params=params,
            original_args={"column_map": column_map},
        )

    def set_current_playlist(self, playlist_ref: PlaylistRef) -> None:
        """
        Set the currently selected playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        """
        params = {"current": param_value_to_str(playlist_ref)}
        return self._request(SET_CURRENT_PLAYLIST, params=params)

    def add_playlist(
        self,
        title: str,
        index: Optional[int] = None,
        return_playlist: Optional[bool] = True,
    ) -> Optional[PlaylistInfo]:
        """
        Create a new playlist.

        :param title: The title of the playlist.
        :param index: The numerical index to insert the new playlist.
            None = last position.
        :param return_playlist: If True automatically makes a second request
            to beefweb to retrieve the playlist info for the new playlist.
            There is a small chance that the incorrect playlist will be
            returned during the second request (i.e. if a playlist is added or
            removed between api calls).  In this case an AssertionError will
            be raised.
        :returns: A PlaylistInfo namedtuple if return_playlist is True else
            None
        """
        params = {}
        if index is not None:
            params["index"] = index
        if title is not None:
            params["title"] = title
        self._request(ADD_PLAYLIST, params=params)

        playlist = None
        if return_playlist and index is None:
            playlist = self.get_playlists().find_playlist(
                title=title, find_last=True
            )
        elif return_playlist:
            playlist = self.get_playlists()[index]

        if playlist and playlist.title != title:
            raise AssertionError("Wrong playlist returned from request!")
        return playlist

    def set_playlist_title(
        self, playlist_ref: PlaylistRef, title: str
    ) -> None:
        """
        Change a playlist's title.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param title: The new title of the playlist.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {"title": title}
        self._request(UPDATE_PLAYLIST, paths=paths, params=params)

    def remove_playlist(self, playlist_ref: PlaylistRef) -> None:
        """
        Remove a playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        return self._request(REMOVE_PLAYLIST, paths=paths)

    def move_playlist(self, playlist_ref: PlaylistRef, new_index: int) -> None:
        """
        Move a playlist to a new index.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param index: The new index of the playlist. Negative value for last
            position.
        """
        paths = {
            "playlist_ref": param_value_to_str(playlist_ref),
            "new_index": new_index,
        }
        return self._request(MOVE_PLAYLIST, paths=paths)

    def clear_playlist(self, playlist_ref: PlaylistRef) -> None:
        """
        Remove all items from a playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        return self._request(CLEAR_PLAYLIST, paths=paths)

    def get_browser_roots(self) -> BrowserEntry:
        """
        Get all the files and directories accessable by beefweb.

        :returns: A BrowserEntry object.
        """
        return self._request(BROWSER_ROOTS)

    def get_browser_entries(self, path: str) -> BrowserEntry:
        r"""
        Get files and directories from a specific path.

        :param path: The path to the directory or file to retrieve.  Note that
            even in windows the path including the drive letter is case
            sensitive  (r"C:\Music" will work r"c:\Music" will not).
        :returns: A BrowserEntry object.
        """
        params = {}
        if path is not None:
            params["path"] = path
        return self._request(BROWSER_ENTRIES, params=params)

    def add_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        items: Paths,
        dest_index: Optional[int] = None,
        asynchronous: bool = False,
    ) -> None:
        """
        Add items to a playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param items: A list or tuple of strings containing the paths of
            files and/or directories to add.  Note that the paths are case
            sensitive even in windows.
        :param dest_index: The index in the playlist to insert the new items.
        :param asynchronous: Set to True to make the request asynchronously
            and not wait for the items to finish processing before returning.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {"async": param_value_to_str(asynchronous)}
        if dest_index is not None:
            params["index"] = param_value_to_str(dest_index)
        content = {"items": items}
        return self._request(
            ADD_PLAYLIST_ITEMS, params=params, paths=paths, body=content
        )

    def copy_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        item_indices: ItemIndices,
        dest_index: Optional[int] = None,
    ) -> None:
        """
        Copy items to the same playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param item_indices: Indices of the items to be copied.
        :param dest_index: The index in the playlist to insert the copies.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {}
        if dest_index is not None:
            params["targetIndex"] = dest_index
        content = {"items": item_indices}
        return self._request(
            COPY_PLAYLIST_ITEMS, params=params, paths=paths, body=content
        )

    def copy_between_playlists(
        self,
        source_playlist: PlaylistRef,
        dest_playlist: PlaylistRef,
        item_indices: ItemIndices,
        dest_index: Optional[int] = None,
    ) -> None:
        """
        Copy items to a different playlist.

        :param source_playlist: The PlaylistInfo object, ID, or numerical
            playlist index of the source.
        :param source_playlist: The PlaylistInfo object, ID, or numerical
            playlist index of the destination.
        :param item_indices: Indices of the items to be copied.
        :param dest_index: The index in the playlist to insert the copies.
        """
        paths = {
            "source_playlist_ref": param_value_to_str(source_playlist),
            "dest_playlist_ref": param_value_to_str(dest_playlist),
        }
        params = {}
        if dest_index is not None:
            params["targetIndex"] = dest_index
        content = {"items": item_indices}
        return self._request(
            COPY_BETWEEN_PLAYLISTS, params=params, paths=paths, body=content
        )

    def move_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        item_indices: ItemIndices,
        dest_index: Optional[int] = None,
    ) -> None:
        """
        Move items to a different index in the same playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param item_indices: Indices of the items to be moved.
        :param dest_index: The index in the playlist to move the items.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {}
        if dest_index is not None:
            params["targetIndex"] = dest_index
        content = {"items": item_indices}
        return self._request(
            MOVE_PLAYLIST_ITEMS, params=params, paths=paths, body=content
        )

    def move_between_playlists(
        self,
        source_playlist: PlaylistRef,
        dest_playlist: PlaylistRef,
        item_indices: ItemIndices,
        dest_index: Optional[int] = None,
    ) -> None:
        """
        Move items to a different playlist.

        :param source_playlist: The PlaylistInfo object, ID, or numerical
            playlist index of the source.
        :param source_playlist: The PlaylistInfo object, ID, or numerical
            playlist index of the destination.
        :param item_indices: Indices of the items to be moved.
        :param dest_index: The index in the playlist to insert the items.
        """
        paths = {
            "source_playlist_ref": param_value_to_str(source_playlist),
            "dest_playlist_ref": param_value_to_str(dest_playlist),
        }
        params = {}
        if dest_index is not None:
            params["targetIndex"] = dest_index
        content = {"items": item_indices}
        return self._request(
            MOVE_BETWEEN_PLAYLISTS, params=params, paths=paths, body=content
        )

    def remove_playlist_items(
        self, playlist_ref: PlaylistRef, item_indices: ItemIndices
    ) -> None:
        """
        Remove items from a playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param item_indices: Indices of the items to be removed.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {}
        content = {"items": item_indices}
        return self._request(
            REMOVE_PLAYLIST_ITEMS, params=params, paths=paths, body=content
        )

    def sort_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        by: str,
        desc: bool = False,
        random: bool = False,
    ) -> None:
        """
        Sort the items in a playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param by: The media player field to sort by (i.e. "%title%").
        :param desc: Sort in descending order.
        :param random: Sort in random order.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {
            "by": by,
            "desc": param_value_to_str(desc),
            "random": param_value_to_str(random),
        }
        return self._request(SORT_PLAYLIST_ITEMS, params=params, paths=paths)

    def get_artwork(self, playlist_ref: PlaylistRef, index: int) -> None:
        """
        Get an items artwork.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        :param index: The index of the item to get artwork for.
        """
        paths = {
            "playlist_ref": param_value_to_str(playlist_ref),
            "index": index,
        }
        params = {}
        return self._request(GET_ARTWORK, params=params, paths=paths)
