import asyncio
from json import loads as parse_json
from urllib3.util import make_headers
from aiohttp_sse_client import client as sse_client
from aiohttp import ClientSession, ClientTimeout, ClientConnectionError
from datetime import timedelta
from collections import namedtuple
from urllib.parse import urlencode
from typing import Optional, Callable
from .models import Playlists, PlaylistItems, PlayerState
from .client import param_value_to_str, PlaylistRef, ColumnsMap


InfoHandler = namedtuple(
    "InfoHandler", ["return_type", "attach_attr", "column_map", "callbacks"]
)


class EventListener:
    """A listener class for the beefweb server's eventsource."""

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

    _info_name_map = {
        "player_state": "player",
        "playlist_items": "playlistItems",
        "playlists": "playlists",
    }

    def __init__(
        self,
        base_url: str,
        port: int,
        active_item_column_map: Optional[ColumnsMap] = None,
        no_active_item_ignore_time: Optional[float] = 0.25,
        playlist_ref: Optional[PlaylistRef] = None,
        playlist_items_column_map: Optional[ColumnsMap] = None,
        offset: Optional[int] = 0,
        count: Optional[int] = 1000000,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Init.

        :param base_url: The base URL of the beefweb server
            (i.e. "localhost").
        :param port: The port number of the beefweb server.
        :param active_item_column_map: Dict, list, tuple, or set where each key
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
        :param no_active_item_ignore_time: When switching between playlist
            items the media player will briefly report that there is no active
            item before updating with the information of the next item.  This
            argument is the amount of time in seconds that these updates will
            be ignored.  If another update comes in during the ignored period
            and that update shows an active item then the previous update
            showing no active item will be completely ignored. Set to 0 to
            disable.
        :param playlist_ref: The ID or numerical index of the playlist to
            retrieve items from.  If left as None will not retrieve any items.
        :param playlist_items_column_map: Dict, list, tuple, or set where each
            key (for dict, set) or item (for list, tuple) is the item field
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
        :param offset: The index offset to retrieve playlist items from when
            playlist_ref is not set to None.
        :param count: The number of playlist items to retrieve when
            playlist_ref is not set to None.
        :param username: The username to use when using authentication with
            beefweb.
        :param password: The password to use when using authentication with
            beefweb.
        """
        self.player_state = None
        """
        A PlayerState object representing the current state of the player
        including the currently active item.  Set to None when the listener
        is not connected.
        """
        self.playlists = None
        """
        A Playlists object representing the current playlists.  Set to None
        when the listener is not connected.
        """

        self._connection = None
        self._event_reader = None
        self._session = None
        self._no_active_item_ignore_time = no_active_item_ignore_time
        self._player_state_update_timeout = None

        if not base_url.lower().startswith("http"):
            base_url = "http://" + base_url
        user_pass = None
        if username is not None and password is not None:
            user_pass = ":".join((username, password))
        self._headers = make_headers(basic_auth=user_pass)
        # The beefweb server treats header names as case sensitive...
        if "authorization" in self._headers:
            self._headers["Authorization"] = self._headers.pop("authorization")

        if active_item_column_map is None:
            active_item_column_map = self._default_column_map
        if playlist_items_column_map is None:
            playlist_items_column_map = self._default_column_map

        self._handlers = {
            "player": InfoHandler(
                return_type=PlayerState,
                attach_attr="player_state",
                column_map=active_item_column_map,
                callbacks=set(),
            ),
            "playlistItems": InfoHandler(
                return_type=PlaylistItems,
                attach_attr=None,
                column_map=playlist_items_column_map,
                callbacks=set(),
            ),
            "playlists": InfoHandler(
                return_type=Playlists,
                attach_attr="playlists",
                column_map=None,
                callbacks=set(),
            ),
        }

        param_dict = {
            "player": param_value_to_str(True),
            "trcolumns": param_value_to_str(active_item_column_map),
            "playlists": param_value_to_str(True),
        }

        if playlist_ref is not None:
            param_dict.update(
                {
                    "playlistItems": param_value_to_str(True),
                    "plref": param_value_to_str(playlist_ref),
                    "plcolumns": param_value_to_str(playlist_items_column_map),
                    "plrange": f"{offset}:{count}",
                }
            )
        self._url = (
            f"{base_url}:{port}/api/query/updates?{urlencode(param_dict)}"
        )

    async def connect(self, reconnect_time: Optional[float] = 5):
        """
        Connect to the beefweb eventsource.

        :param reconnect_time: The number of seconds to wait between
            reconnection attempts.
        """
        if self.is_connected():
            return
        reconnect_time = timedelta(seconds=reconnect_time)

        # necessary to prevent connection from timing out after 5 minutes
        timeout = ClientTimeout(sock_read=0)
        self._session = ClientSession(timeout=timeout)

        self._connection = sse_client.EventSource(
            self._url,
            session=self._session,
            headers=self._headers,
            reconnection_time=reconnect_time,
            max_connect_retry=1000000000,
            on_error=self._connection_error_handler,
        )

        loop = asyncio.get_event_loop()
        self._event_reader = loop.create_task(self._read_events())

    async def _read_events(self):
        async with self._connection:
            try:
                async for event in self._connection:
                    self._process_event(event)
            except ConnectionError as err:
                print("Connection error: ", err)

    def _connection_error_handler(self):
        for handler in self._handlers.values():
            if handler.attach_attr is not None:
                setattr(self, handler.attach_attr, None)

    def _process_event(self, evt):
        data = parse_json(evt.data)

        for i, key in enumerate(data):
            if key in self._handlers:
                handler = self._handlers[key]
                processed_item = handler.return_type(
                    data=data, column_map=handler.column_map
                )
                if key == "player":
                    self._process_player_state(processed_item)
                else:
                    if handler.attach_attr is not None:
                        setattr(self, handler.attach_attr, processed_item)
                    for callback in handler.callbacks:
                        callback(processed_item)

    def _process_player_state(self, new_state):
        if (
            self._player_state_update_timeout is not None
            and not self._player_state_update_timeout.cancelled()
        ):
            self._player_state_update_timeout.cancel()
        self._player_state_update_timeout = None

        if (
            new_state.active_item.index == -1
            and self._no_active_item_ignore_time != 0
            and self.player_state is not None
        ):
            self._player_state_update_timeout = asyncio.ensure_future(
                self._delayed_player_state_update(new_state)
            )
        else:
            self._update_player_state(new_state)

    async def _delayed_player_state_update(self, new_state):
        await asyncio.sleep(self._no_active_item_ignore_time)
        self._update_player_state(new_state)

    def _update_player_state(self, new_state):
        self.player_state = new_state
        for callback in self._handlers["player"].callbacks:
            callback(new_state)
        self._player_state_update_timeout = None

    async def disconnect(self):
        """Disconnect from the beefweb eventsource."""
        if self._connection is not None:
            await self._connection.close()
        if self._session is not None:
            await self._session.close()
        if (
            self._event_reader is not None
            and not self._event_reader.cancelled()
        ):
            try:
                await self._event_reader
            except ClientConnectionError:
                pass
        self._connection = None
        self._event_reader = None
        self._session = None
        self.player_state = None
        self.playlists = None

    def is_connected(self):
        """
        Return True if the listener is connected to beefweb.

        :returns: True if the connected to the eventsource, False if
            disconnected or in the process of connecting.
        """
        if self._connection is not None:
            return self._connection.ready_state == sse_client.READY_STATE_OPEN
        return False

    def add_callback(self, info_type: str, callback_func: Callable):
        """
        Add a callback for when certain types of information are received.

        :param info_type: The type of data that will cause the callback to
            run.  Possible values: "player_state", "playlist_items",
            "playlists"
        :param callback_func: A reference to the function to use as a
            callback.  Callbacks will receive the following argument when run
            depending on the info_type:
            "player_state" = A PlayerState object,
            "playlist_items" = A PlaylistItems object,
            "playlists" = A Playlists object
        """
        if info_type not in self._info_name_map:
            raise AttributeError("Invalid info type: " + info_type)
        handler_key = self._info_name_map[info_type]
        self._handlers[handler_key].callbacks.add(callback_func)

    def remove_callback(self, info_type: str, callback_func: Callable):
        """
        Remove a callback.

        :param info_type: The type of data to remove the callback from.
            Possible values: "player_state", "playlist_items", "playlists"
        :param callback_func: A reference to the callback function to remove.
        """
        if info_type not in self._info_name_map:
            raise AttributeError("Invalid info type: " + info_type)
        handler_key = self._info_name_map[info_type]
        self._handlers[handler_key].callbacks.discard(callback_func)

    def remove_all_callbacks(self):
        """Remove all callbacks."""
        for handler in self._handlers.values():
            handler.callbacks.clear()
