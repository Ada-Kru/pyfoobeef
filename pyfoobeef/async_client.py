import aiohttp
from typing import Optional
from .type_helpers import PlaylistRef, Paths, ItemIndices, ColumnsMap
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
from .exceptions import ConnectError, RequestError


class AsyncClient:
    """
    Asynchronous class for interacting with the beefweb plugin.

    :param base_url: The base URL for beefweb's server.  i.e. "localhost"
    :param port: The port number of beefweb's server.
    :param username: The username to use if authentification is enabled in
        beefweb.
    :param password: The password to use if authentification is enabled in
        beefweb.
    :param timeout: The maximum amount of time to wait when making a http
        request.
    """

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
        timeout: float = 10.0,
    ):
        if not base_url.lower().startswith("http"):
            base_url = "http://" + base_url
        self.base_url = base_url
        self.port = port
        self.auth = None
        if username is not None and password is not None:
            self.auth = aiohttp.BasicAuth(login=username, password=password)
        self._timeout = aiohttp.ClientTimeout(
            connect=timeout, sock_read=timeout
        )

    async def _request(
        self, endpoint, params=None, paths=None, body=None, original_args=None
    ):
        """
        Send a HTTP request to the beefweb server.

        :param Endpoint endpoint: The endpoint object containing information
            about the endpoint and the return type.
        :param dict params: Dict containing the parameters to be added to the
            endpoint url.
        :param dict paths: Dict to be used for formatting the endpoint url.
        :param dict body: Object to be added as the requests JSON payload.
        :param dict original_args: Dict containing the original arguments
            passed to the caller.
        :returns: The return type specified in the object passed to the
            endpoint argument.
        :raises: ConnectError if the script cannot connect to the beefweb
            server.
        :raises: RequestError if beefweb returns an error.
        """
        if paths is not None:
            endpoint_path = endpoint.endpoint.format(**paths)
        else:
            endpoint_path = endpoint.endpoint

        url = f"{self.base_url}:{self.port}/api{endpoint_path}"

        async with aiohttp.ClientSession(
            auth=self.auth, timeout=self._timeout
        ) as session:
            try:
                async with session.request(
                    method=endpoint.method, url=url, params=params, json=body
                ) as response:

                    if response.status not in (200, 202, 204):
                        raise RequestError(
                            response.status, await response.json()
                        )
                    if endpoint.model is not None:
                        data = await response.json()
                        if (
                            not original_args
                            or "column_map" not in original_args
                        ):
                            return endpoint.model(data)
                        else:
                            return endpoint.model(
                                data, column_map=original_args["column_map"]
                            )
            except (
                aiohttp.ClientResponseError,
                aiohttp.ClientConnectionError,
            ) as err:
                raise ConnectError(err)

    async def get_player_state(
        self, column_map: Optional[ColumnsMap] = None
    ) -> PlayerState:
        """
        Get the status of the player.

        :param Optional[ColumnsMap] column_map: Dict, list, tuple, or set
            where each key (for dict, set) or item (for list, tuple) is the
            active item field to request.  If a dict is used each value is the
            attribute name to map that key to the returned Column object.

            If this argument is not specified a default column map will be
            used.

            .. note:: Names that would be invalid as Python attrubute names
                may only be accessed through subscripting (i.e. "%title%" or
                "my custom name").


                Examples-
                {"%track artist%": "artist"} will result in the returned
                object having an active_item.columns.artist attribute
                containing information returned from the active item's
                %track artist% field.

                ["%title%", "%album%"] will result in the returned object
                bieng subscriptable like active_item.columns["%album%"] which
                will return information returned from the active item's
                %album% field.
        :returns: PlayerState object
        :rtype: PlayerState
        """
        if column_map is None:
            column_map = self._default_column_map
        params = {"columns": param_value_to_str(column_map)}
        return await self._request(
            GET_PLAYER_STATE,
            params=params,
            original_args={"column_map": column_map},
        )

    async def set_player_state(
        self,
        volume: Optional[float] = None,
        mute: Optional[bool] = None,
        position: Optional[int] = None,
        relative_position: Optional[int] = None,
        playback_mode: Optional[int] = None,
    ) -> None:
        """
        Set the volume level, playback position, and playback order.

        .. note:: Note that the value for the volume parameter may need to be
            a negative number to work correctly. Use information returned by
            get_player_state to determine the min and max values for the
            connected media player.

        :param Optional[float] volume: Floating point number to set the
            player's volume level. Value may need to be a negative number to
            work correctly. Use information returned by get_player_state to
            determine the min and max values for the connected media player.
        :param Optional[bool] mute: True = muted, False = unmuted, None = no
            change.
        :param Optional[float] position: Sets the position of the current
            track in seconds.
        :param Optional[float] relative_position: Seconds to Add or subtract
            from the current position.
        :param Optional[int] playback_mode: Numerical mode that sets playback
            order (repeat, random, shuffle, etc.).  Use the playback_modes
            attribute from get_player_state() to determine the possible
            choices.
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

        return await self._request(
            SET_PLAYER_STATE, params=kw_map, original_args=locals()
        )

    async def play(self) -> None:
        """
        Start playback.

        .. note:: Note that the item played will be from the last playlist
            that an item was played from even if another playlist is set as
            current.  Use the play_specific method first to play an item from a
            specific playlist.
        """
        await self._request(PLAY)

    async def play_specific(
        self, playlist_ref: PlaylistRef, index: int
    ) -> None:
        """
        Start playback of a specific item from a specific playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical index of the playlist that contains the media to play.
        :param int index: The index number of the item to play.
        """
        playlist_ref = param_value_to_str(playlist_ref)
        await self._request(PLAY_SPECIFIC, paths=locals())

    async def play_random(self) -> None:
        """
        Play a random item from the last played playlist.

        .. note:: Note that the item played will be from the last playlist
            that an item was played from even if another playlist is set as
            current.  Use the play_specific method first to play an item from a
            specific playlist.
        """
        await self._request(PLAY_RANDOM)

    async def play_next(self, by: str = None) -> None:
        """
        Play the next item in the last played playlist.

        .. note:: Note that the item played will be from the last playlist
            that an item was played from even if another playlist is set as
            current.  Use the play_specific method first to play an item from a
            specific playlist.

        :param str by: The media player field used to determine what counts as
            next (i.e. "%title%").  None = use the items index in the playlist.
        """
        kw_map = {"by": by} if by is not None else {}
        await self._request(PLAY_NEXT, params=kw_map)

    async def play_previous(self, by: str = None) -> None:
        """
        Play the previous item in the last played playlist.

        .. note:: Note that the item played will be from the last playlist
            that an item was played from even if another playlist is set as
            current.  Use the play_specific method first to play an item from a
            specific playlist.

        :param str by: The media player field used to determine what counts as
            previous (i.e. "%title%").  None = use the items index in the
            playlist.
        """
        kw_map = {"by": by} if by is not None else {}
        await self._request(PLAY_PREVIOUS, params=kw_map)

    async def stop(self) -> None:
        """Stop playback."""
        await self._request(STOP)

    async def pause(self) -> None:
        """Pause playback."""
        await self._request(PAUSE)

    async def pause_toggle(self) -> None:
        """Toggle pause state."""
        await self._request(PAUSE_TOGGLE)

    async def get_playlists(self) -> Playlists:
        """
        Get an object representing the playlists.

        :returns: A Playlists object
        :rtype: Playlists
        """
        params = {"playlists": "true"}
        return await self._request(PLAYLIST_QUERY, params=params)

    async def find_playlist(
        self, title: Optional[str] = None, search_id: Optional[str] = None
    ) -> Optional[PlaylistInfo]:
        """
        Get an object representing a specific playlist.

        :param Optional[str] title: String representing the playlist's title.
        :param Optional[str] search_id: The id of the playlist.
        :returns: A PlaylistInfo namedtuple or None if not found.
        :rtype: Optional[PlaylistInfo]
        """
        return (await self.get_playlists()).find_playlist(
            title=title, search_id=search_id
        )

    async def get_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        offset: int = 0,
        count: int = 1000000,
        column_map: Optional[ColumnsMap] = None,
    ) -> PlaylistItems:
        """
        Get an object representing the items in a specific playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param int offset: The start index of the items to retrieve.
        :param int count: The amount of items to retrieve.
        :param Optional[ColumnsMap] column_map: Dict, list, tuple, or set where
            each key (for dict, set) or item (for list, tuple) is the item
            field to request.  If a dict is used each value is the attribute
            name to map that key to the returned Column object.

            If this argument is not specified a default column map will be
            used.

            .. note:: Names that would be invalid as Python attrubute names
                may only be accessed through subscripting (i.e. "%title%" or
                "my custom name").

                Examples-
                {"%track artist%": "artist"} will result in the returned
                object having an active_item.columns.artist attribute
                containing information returned from the active item's
                %track artist% field.

                ["%title%", "%album%"] will result in the returned object
                bieng subscriptable like active_item.columns["%album%"] which
                will return information returned from the active item's
                %album% field.

        :returns: A PlaylistItems object.
        :rtype: PlaylistItems
        """
        if column_map is None:
            column_map = self._default_column_map
        params = {
            "playlistItems": "true",
            "plref": param_value_to_str(playlist_ref),
            "plrange": f"{offset}:{count}",
            "plcolumns": param_value_to_str(column_map),
        }
        return await self._request(
            PLAYLIST_ITEMS,
            params=params,
            original_args={"column_map": column_map},
        )

    async def set_current_playlist(self, playlist_ref: PlaylistRef) -> None:
        """
        Set the currently selected playlist.

        :param playlist_ref: The PlaylistInfo object, ID, or numerical
            playlist index.
        """
        params = {"current": param_value_to_str(playlist_ref)}
        return await self._request(SET_CURRENT_PLAYLIST, params=params)

    async def add_playlist(
        self,
        title: str,
        index: Optional[int] = None,
        return_playlist: Optional[bool] = True,
    ) -> Optional[PlaylistInfo]:
        """
        Create a new playlist.

        :param str title: The title of the playlist.
        :param Optional[int] index: The numerical index to insert the new
            playlist. None = last position.
        :param Optional[bool] return_playlist: If True automatically makes a
            second request to beefweb to retrieve the playlist info for the
            new playlist. There is a small chance that the incorrect playlist
            will be returned during the second request (i.e. if a playlist is
            added or removed between api calls).  In this case an
            AssertionError will be raised.
        :returns: A PlaylistInfo namedtuple if return_playlist is True else
            None
        :rtype: Optional[PlaylistInfo]
        """
        params = {}
        if index is not None:
            params["index"] = index
        if title is not None:
            params["title"] = title
        await self._request(ADD_PLAYLIST, params=params)

        playlist = None
        if return_playlist and index is None:
            playlist = (await self.get_playlists()).find_playlist(
                title=title, find_last=True
            )
        elif return_playlist:
            playlist = (await self.get_playlists())[index]

        if playlist and playlist.title != title:
            raise AssertionError("Wrong playlist returned from request!")
        return playlist

    async def set_playlist_title(
        self, playlist_ref: PlaylistRef, title: str
    ) -> None:
        """
        Change a playlist's title.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param str title: The new title of the playlist.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {"title": title}
        await self._request(UPDATE_PLAYLIST, paths=paths, params=params)

    async def remove_playlist(self, playlist_ref: PlaylistRef) -> None:
        """
        Remove a playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        return await self._request(REMOVE_PLAYLIST, paths=paths)

    async def move_playlist(
        self, playlist_ref: PlaylistRef, new_index: int
    ) -> None:
        """
        Move a playlist to a new index.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param int index: The new index of the playlist. Negative value to
            make it the last playlist.
        """
        paths = {
            "playlist_ref": param_value_to_str(playlist_ref),
            "new_index": new_index,
        }
        return await self._request(MOVE_PLAYLIST, paths=paths)

    async def clear_playlist(self, playlist_ref: PlaylistRef) -> None:
        """
        Remove all items from a playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        return await self._request(CLEAR_PLAYLIST, paths=paths)

    async def get_browser_roots(self) -> BrowserEntry:
        """
        Get all the files and directories accessable by beefweb.

        :returns: A BrowserEntry object.
        :rtype: BrowserEntry
        """
        return await self._request(BROWSER_ROOTS)

    async def get_browser_entries(self, path: str) -> BrowserEntry:
        r"""
        Get files and directories from a specific path.

        :param str path: The path to the directory or file to retrieve.  Note
            that even in windows the path including the drive letter is case
            sensitive (r"C:\\Music" will work, r"c:\\Music" will not).

        .. warning:: Even in windows the path including the drive letter is
            case sensitive (r"C:\\Music" will work, r"c:\\Music" will not).

        :returns: A BrowserEntry object.
        :rtype: BrowserEntry
        """
        params = {}
        if path is not None:
            params["path"] = path
        return await self._request(BROWSER_ENTRIES, params=params)

    async def add_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        items: Paths,
        dest_index: Optional[int] = None,
        asynchronous: bool = False,
    ) -> None:
        """
        Add items to a playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param Paths items: A list or tuple of strings or FileSystemEntry
            objects containing the paths of files and/or directories to add.
            Note that the paths including the drive letter are case sensitive
            even in Windows.
        :param Optional[int] dest_index: The index in the playlist to insert
            the new items.
        :param bool asynchronous: Set to True to not wait for the
            media player to finish processing the added items before
            returning.  Default = False.

        .. warning:: The paths including the drive letter are case sensitive
            even in windows.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {"async": param_value_to_str(asynchronous)}
        if dest_index is not None:
            params["index"] = param_value_to_str(dest_index)
        content = {"items": [param_value_to_str(item) for item in items]}
        return await self._request(
            ADD_PLAYLIST_ITEMS, params=params, paths=paths, body=content
        )

    async def copy_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        item_indices: ItemIndices,
        dest_index: Optional[int] = None,
    ) -> None:
        """
        Copy items to the same playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param ItemIndices item_indices: List or tuple of the indices of the
            items to be copied.
        :param Optional[int] dest_index: The index in the playlist to insert
            the copies. None = copy to the end of the playlist.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {}
        if dest_index is not None:
            params["targetIndex"] = dest_index
        content = {"items": item_indices}
        return await self._request(
            COPY_PLAYLIST_ITEMS, params=params, paths=paths, body=content
        )

    async def copy_between_playlists(
        self,
        source_playlist: PlaylistRef,
        dest_playlist: PlaylistRef,
        item_indices: ItemIndices,
        dest_index: Optional[int] = None,
    ) -> None:
        """
        Copy items to a different playlist.

        :param PlaylistRef source_playlist: The PlaylistInfo object, ID, or
            numerical playlist index of the source.
        :param PlaylistRef dest_playlist: The PlaylistInfo object, ID, or
            numerical playlist index of the destination.
        :param ItemIndices item_indices: List or tuple of the indices of the
            items to be copied.
        :param Optional[int] dest_index: The index in the playlist to insert
            the copies. None = copy to the end of the playlist.
        """
        paths = {
            "source_playlist_ref": param_value_to_str(source_playlist),
            "dest_playlist_ref": param_value_to_str(dest_playlist),
        }
        params = {}
        if dest_index is not None:
            params["targetIndex"] = dest_index
        content = {"items": item_indices}
        return await self._request(
            COPY_BETWEEN_PLAYLISTS, params=params, paths=paths, body=content
        )

    async def move_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        item_indices: ItemIndices,
        dest_index: Optional[int] = None,
    ) -> None:
        """
        Move items to a different index in the same playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param ItemIndices item_indices: List or tuple of the indices of the
            items to be moved.
        :param Optional[int] dest_index: The index in the playlist to insert
            the copies. None = copy to the end of the playlist.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {}
        if dest_index is not None:
            params["targetIndex"] = dest_index
        content = {"items": item_indices}
        return await self._request(
            MOVE_PLAYLIST_ITEMS, params=params, paths=paths, body=content
        )

    async def move_between_playlists(
        self,
        source_playlist: PlaylistRef,
        dest_playlist: PlaylistRef,
        item_indices: ItemIndices,
        dest_index: Optional[int] = None,
    ) -> None:
        """
        Move items to a different playlist.

        :param PlaylistRef source_playlist: The PlaylistInfo object, ID, or
            numerical playlist index of the source.
        :param PlaylistRef dest_playlist: The PlaylistInfo object, ID, or
            numerical playlist index of the destination.
        :param ItemIndices item_indices: List or tuple of the indices of the
            items to be moved.
        :param Optional[int] dest_index: The index in the playlist to insert
            the copies. None = copy to the end of the playlist.
        """
        paths = {
            "source_playlist_ref": param_value_to_str(source_playlist),
            "dest_playlist_ref": param_value_to_str(dest_playlist),
        }
        params = {}
        if dest_index is not None:
            params["targetIndex"] = dest_index
        content = {"items": item_indices}
        return await self._request(
            MOVE_BETWEEN_PLAYLISTS, params=params, paths=paths, body=content
        )

    async def remove_playlist_items(
        self, playlist_ref: PlaylistRef, item_indices: ItemIndices
    ) -> None:
        """
        Remove items from a playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param ItemIndices item_indices: List or tuple of the indices of the
            items to be removed.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {}
        content = {"items": item_indices}
        return await self._request(
            REMOVE_PLAYLIST_ITEMS, params=params, paths=paths, body=content
        )

    async def sort_playlist_items(
        self,
        playlist_ref: PlaylistRef,
        by: str,
        desc: bool = False,
        random: bool = False,
    ) -> None:
        """
        Sort the items in a playlist.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param str by: The media player field to sort by (i.e. "%title%").
        :param bool desc: Sort in descending order.
        :param bool random: Sort in random order.
        """
        paths = {"playlist_ref": param_value_to_str(playlist_ref)}
        params = {
            "by": by,
            "desc": param_value_to_str(desc),
            "random": param_value_to_str(random),
        }
        return await self._request(
            SORT_PLAYLIST_ITEMS, params=params, paths=paths
        )

    async def get_artwork(self, playlist_ref: PlaylistRef, index: int) -> None:
        """
        Get an items artwork.

        :param PlaylistRef playlist_ref: The PlaylistInfo object, ID, or
            numerical playlist index.
        :param int index: The index of the item to get artwork for.
        """
        paths = {
            "playlist_ref": param_value_to_str(playlist_ref),
            "index": index,
        }
        params = {}
        return await self._request(GET_ARTWORK, params=params, paths=paths)
