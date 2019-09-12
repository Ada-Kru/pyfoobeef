#!/usr/bin/python3
import asynctest
from asyncio import sleep
from uuid import uuid1
from pathlib import Path
from pyfoobeef import AsyncClient, EventListener
from pyfoobeef.exceptions import RequestError
from pyfoobeef.models import PlayerState, Playlists, PlaylistItems


DEFAULT_TIME_DELAY = 0.5


class Helper:
    def __init__(self):
        self.attribute = None

    def set_attribute(self, new_attribute):
        self.attribute = new_attribute


class ClientTest(asynctest.TestCase):
    async def setUp(self):
        self.beefweb = AsyncClient("localhost", 6980)
        self.plist_title = str(uuid1())
        module_dir = Path(__file__).absolute().parent.parent
        self.media_path = str((module_dir / "test_media").resolve())

        await self.beefweb.add_playlist(title=self.plist_title)
        playlist_id = (await self.beefweb.find_playlist(self.plist_title)).id
        await self.beefweb.set_current_playlist(playlist_id)
        await self.beefweb.add_playlist_items(playlist_id, [self.media_path])
        await self.beefweb.sort_playlist_items(playlist_id, "%tracknumber%")
        await self.beefweb.stop()
        await sleep(DEFAULT_TIME_DELAY)

        self.listener = EventListener(
            base_url="localhost",
            port=6980,
            active_item_column_map={
                "%artist%": "artist",
                "%title%": "title",
                "%length%": "length",
            },
            no_active_item_ignore_time=0,
            playlist_ref=playlist_id,
            playlist_items_column_map={
                "%artist%": "artist",
                "%title%": "title",
                "%length%": "length",
            },
            offset=1,
            count=3,
            username="test",
            password="test",
        )

    async def test_connection(self):
        await self.listener.connect(reconnect_time=1)
        await sleep(DEFAULT_TIME_DELAY)
        self.assertTrue(self.listener.is_connected())
        await self.listener.disconnect()
        await sleep(DEFAULT_TIME_DELAY)
        self.assertFalse(self.listener.is_connected())

    async def test_callbacks(self):
        state_helper = Helper()
        items_helper = Helper()
        playlists_helper = Helper()

        await self.beefweb.stop()
        await sleep(DEFAULT_TIME_DELAY)

        self.listener.add_callback(
            info_type="player_state", callback_func=state_helper.set_attribute
        )
        self.listener.add_callback(
            info_type="playlist_items",
            callback_func=items_helper.set_attribute,
        )
        self.listener.add_callback(
            info_type="playlists", callback_func=playlists_helper.set_attribute
        )

        await self.listener.connect(reconnect_time=1)
        await sleep(DEFAULT_TIME_DELAY)
        self.assertTrue(type(state_helper.attribute) == PlayerState)
        self.assertTrue(type(items_helper.attribute) == PlaylistItems)
        self.assertTrue(len(items_helper.attribute) == 2)
        self.assertTrue(len(items_helper.attribute[0]) == 3)
        self.assertTrue(type(playlists_helper.attribute) == Playlists)

        self.listener.remove_callback(
            "player_state", state_helper.set_attribute
        )
        state_helper.set_attribute(None)
        await self.beefweb.play()
        await sleep(DEFAULT_TIME_DELAY)
        self.assertTrue(state_helper.attribute is None)
        self.assertTrue(type(items_helper.attribute) == PlaylistItems)

        await self.beefweb.stop()
        await sleep(DEFAULT_TIME_DELAY)
        self.listener.remove_all_callbacks()
        items_helper.set_attribute(None)
        await self.beefweb.play()
        await sleep(DEFAULT_TIME_DELAY)
        self.assertTrue(items_helper.attribute is None)

    async def tearDown(self):
        await self.listener.disconnect()
        await self.beefweb.stop()
        try:
            plist = await self.beefweb.find_playlist(self.plist_title)
            if plist is not None:
                await self.beefweb.remove_playlist(plist.id)
        except RequestError:
            pass


if __name__ == "__main__":
    asynctest.main()
