from collections import namedtuple
from keyword import iskeyword
from typing import Optional, Union, List
from time import time
from .helper_funcs import (
    process_column_map,
    seconds_to_hhmmss,
    seconds_to_mmss,
)


IndexItem = namedtuple("IndexItem", ["index", "item"])
PlaybackMode = namedtuple("PlaybackMode", ["number", "mode"])
PlayerInfo = namedtuple(
    "PlayerInfo", ["name", "title", "version", "plugin_version"]
)
PlaylistInfo = namedtuple(
    "PlaylistInfo",
    ["id", "index", "title", "is_current", "item_count", "total_time"],
)
Volume = namedtuple("Volume", ["type", "min", "max", "value", "is_muted"])


class ActiveItem:
    """A class with information about the media player's active item."""

    def __init__(
        self, playlist_id, playlist_index, index, position, duration, columns
    ):
        self.playlist_id = playlist_id
        """The ID of currently selected playlist."""
        self.playlist_index = playlist_index
        """The numerical index of the currently selected playlist."""
        self.index = index
        """The numerical index of the active item. Will be -1 if no item is
           active.
        """
        self.position = position
        """The playback position of the active item in seconds."""
        self.duration = duration
        """The duration of the active item in seconds."""
        self.columns = columns
        """A Columns object containing information about the active item's
           informaiton fields.
        """

    def has_columns(self) -> bool:
        """:returns: If the active item returned column information."""
        return self.columns is not None

    def position_hhmmss(self) -> str:
        """:returns: The playback position of the active item as hh:mm:ss."""
        return seconds_to_hhmmss(self.position)

    def position_mmss(self) -> str:
        """:returns: The playback position of the active item as mm:ss."""
        return seconds_to_mmss(self.position)

    def duration_hhmmss(self) -> str:
        """:returns: The active item's duration as hh:mm:ss."""
        return seconds_to_hhmmss(self.duration)

    def duration_mmss(self) -> str:
        """:returns: The active item's duration as mm:ss."""
        return seconds_to_mmss(self.duration)

    def __repr__(self):
        pairs = []
        for key, val in self.__dict__.items():
            if type(val) == str:
                val = f"'{val}'"
            pairs.append(f"{key}={val}")
        return f'(Active Item: {" ".join(pairs)})'

    def __str__(self):
        return self.__repr__()


class Columns:
    """
    Represents information returned about an items data fields.

    Can be iterated over, subscripted, or addressed by attributes
    i.e. (columns.title or columns['title'])
    """

    _reserved_attributes = set(("_reserved_attributes", "_num_columns"))

    def __init__(self, column_map, returned_columns):
        column_map = process_column_map(column_map)
        self._num_columns = len(returned_columns)
        for i, key in enumerate(column_map.keys()):
            attribute_name = column_map[key]
            if (
                attribute_name not in self._reserved_attributes
                and not iskeyword(attribute_name)
            ):
                setattr(self, attribute_name, returned_columns[i])
            else:
                raise NameError(
                    f'Attribute name "{attribute_name}"'
                    f" is resesrved and cannot be used."
                )

    def items(self) -> tuple:
        """Generate key, value pairs for the columns similar to dict.items."""
        for key, val in self.__dict__.items():
            if key not in self._reserved_attributes:
                yield (key, val)

    def __repr__(self):
        pairs = [
            f"{key}={val}"
            for key, val in self.__dict__.items()
            if key not in self._reserved_attributes
        ]
        return f'Columns({", ".join(pairs)})'

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return self._num_columns

    def __getitem__(self, i):
        if i in self._reserved_attributes:
            raise AttributeError(f"{i} should not be addressed this way.")
        return self.__dict__[i]

    def __iter__(self):
        for key in self.__dict__.keys():
            if key not in self._reserved_attributes:
                yield key


class PlayerState:
    """A class representing the state of the player."""

    def __init__(self, data, column_map=None):

        self._creation_time = time()

        info = data["player"]["info"]
        self.info = PlayerInfo(
            name=info["name"],
            title=info["title"],
            version=info["version"],
            plugin_version=info["pluginVersion"],
        )
        """A PlayerInfo namedtuple with information about the media player."""

        active = data["player"]["activeItem"]
        columns = None
        if len(active["columns"]):
            columns = Columns(column_map, active["columns"])

        self.active_item = ActiveItem(
            playlist_id=active["playlistId"],
            playlist_index=active["playlistIndex"],
            index=active["index"],
            position=active["position"],
            duration=active["duration"],
            columns=columns,
        )
        """
        An ActiveItem object with information about the current active item.
        """

        vol = data["player"]["volume"]
        self.volume = Volume(
            type=vol["type"],
            min=vol["min"],
            max=vol["max"],
            value=vol["value"],
            is_muted=vol["isMuted"],
        )
        """A Volume namedtuple with information about the volume level."""

        self.playback_state = data["player"]["playbackState"]
        """
        A string with information about the playback state (i.e. "paused").
        """

        self.playback_modes = tuple(
            PlaybackMode(number=i, mode=mode)
            for i, mode in enumerate(data["player"]["playbackModes"])
        )
        """
        A tuple of PlaybackMode namedtuples that indicate the possible playback
        modes and their number.
        """
        self.playback_mode = self.playback_modes[
            data["player"]["playbackMode"]
        ]
        """
        An PlaybackMode namedtuple that indicates the current playback mode.
        """

        self.parsed_response = data
        """The original parsed JSON response from beefweb."""

    def estimated_position(self) -> float:
        """
        Get the estimated playback position since the last update.

        :returns: The estimated playback position in seconds of the active
            item since this playback object was created.  If the estimated
            position is greater than the active item's duration will return
            the active item's duration.  If the playback state is not
            "playing" will return the active item's position.
        """
        if self.playback_state == "playing":
            est_pos = time() - self._creation_time + self.active_item.position
            return min((est_pos, self.active_item.duration))
        else:
            return self.active_item.position

    def estimated_position_hhmmss(self) -> str:
        """:returns: Output of the estimated_position method as hh:mm:ss."""
        return seconds_to_hhmmss(self.estimated_position())

    def estimated_position_mmss(self) -> str:
        """:returns: Output of the estimated_position method as mm:ss."""
        return seconds_to_mmss(self.estimated_position())


class Playlists:
    """
    Represents the media player's playlists.

    Iterable and subscriptable.
    """

    def __init__(self, data, column_map=None):

        self._playlists = []
        if "playlists" in data:
            for raw_plist in data["playlists"]:
                plist_info = PlaylistInfo(
                    id=raw_plist["id"],
                    index=raw_plist["index"],
                    title=raw_plist["title"],
                    is_current=raw_plist["isCurrent"],
                    item_count=raw_plist["itemCount"],
                    total_time=raw_plist["totalTime"],
                )
                self._playlists.append(plist_info)

    def find_playlist(
        self,
        title: Optional[str] = None,
        search_id: Optional[str] = None,
        find_last: Optional[bool] = False,
    ) -> Optional[PlayerInfo]:
        """
        Search for a specific playlist playlist.

        :param title: The title of the playlist to find.
        :param search_id: The ID of the playlist to search for.
        :param find_last: If true returns the last item found.

        :returns: A PlaylistInfo namedtuple if found else None.
        """
        plsts = self._playlists if not find_last else reversed(self._playlists)
        for playlist in plsts:
            if playlist.title == title or playlist.id == search_id:
                return playlist
        return None

    def __getitem__(self, i):
        return self._playlists[i]

    def __len__(self):
        return len(self._playlists)

    def __iter__(self):
        for item in self._playlists:
            yield item


class PlaylistItems:
    """
    An iterable and subscriptable class representing the items in a playlist.

    Iterating or subscripting will return Columns objects.
    """

    def __init__(self, data, column_map=None):

        self._items = []
        self.total_count = 0
        """The total amount of items in the playlist."""
        self.offset = 0
        """The offset of the first item's index for the items returned."""
        if "playlistItems" in data:
            self.offset = data["playlistItems"]["offset"]
            self.total_count = data["playlistItems"]["totalCount"]
            for raw_column in data["playlistItems"]["items"]:
                columns = Columns(column_map, raw_column["columns"])
                self._items.append(columns)

    def find_item(
        self,
        case_sens: Optional[bool] = False,
        return_index: Optional[bool] = False,
        **kwargs: Union[str, int, float],
    ) -> Union[List[Columns], List[IndexItem]]:
        """
        Search for a specific item.  Accepts attributes of the columns objects
        as argument names (i.e
        items.find_item(title="The Song Title", artist="The Song Artist")).

        :param case_sens:    If true perform a case sensitive search.
        :param return_index: If true returns the item's index in the playlist.

        :returns: A list of Columns objects or IndexItem namedtuples if
                  return_index is true.
        """

        results = []
        for index, item in enumerate(self._items):
            match = True
            for keyword in kwargs:
                try:
                    column = getattr(item, keyword)
                    search_str = kwargs[keyword]
                    if not case_sens:
                        column = column.lower()
                        search_str = search_str.lower()
                    if column != search_str:
                        match = False
                        break
                except AttributeError:
                    match = False

            if match:
                if not return_index:
                    results.append(item)
                else:
                    results.append(
                        IndexItem(index=self.offset + index, item=item)
                    )

        return results

    def __getitem__(self, i):
        return self._items[i]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        for item in self._items:
            yield item


class FileSystemEntry:
    """Represents a file or directory accessable by the media player."""

    def __init__(self, entry, separator):
        self.separator = separator
        """The character used to seperate directories in the path."""
        self.name = entry["name"]
        """The file or directory name."""
        self.path = entry["path"]
        """The full path of the file or directory."""
        self._is_file = entry["type"] == "F"
        self.size = entry["size"]
        """The file size in bytes. 0 for directories."""
        self.timestamp = entry["timestamp"]
        """The timestamp of the file or directory."""

    def is_file(self) -> bool:
        """:returns: True if the item is a file, False if directory."""
        return self._is_file

    def is_directory(self) -> bool:
        """:returns: True if the item is a directory, False if file."""
        return not self._is_file

    def __repr__(self):
        return (
            f'FileSystemEntry {"File" if self._is_file else "Directory"}:'
            f' "{self.path}"'
        )

    def __str__(self):
        return self.__repr__()


class BrowserEntry:
    """
    Represents files or directories accessable by the media player.

    Iterable and subscriptable.
    """

    def __init__(self, data):

        self.path_separator = data["pathSeparator"]
        """The character used to seperate directories in the path."""
        entries = data["entries"] if "entries" in data else data["roots"]
        self._entries = [
            FileSystemEntry(entry, self.path_separator) for entry in entries
        ]

    def __repr__(self):
        return str(self._entries)

    def __str__(self):
        return str(self._entries)

    def __getitem__(self, i):
        return self._entries[i]

    def __iter__(self):
        for entry in self._entries:
            yield entry
