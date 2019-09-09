#!/usr/bin/python3
import asynctest
from asyncio import sleep
from uuid import uuid1
from pathlib import Path
from sys import path as sys_path

sys_path.insert(0, "..")

from lib.async_client import AsyncClient, RequestError
from lib.models import PlayerState


DEFAULT_TIME_DELAY = 0.5


class ClientTest(asynctest.TestCase):
    async def setUp(self):
        self.beefweb = AsyncClient("localhost", 6980)
        self.plist1_title = str(uuid1())
        self.plist2_title = str(uuid1())
        self.plist3_title = str(uuid1())
        module_dir = Path(__file__).absolute().parent.parent
        self.media_path = str(module_dir / "test_media")

    async def test_get_player_state(self):
        state = await self.beefweb.get_player_state()
        self.assertTrue(type(state) is PlayerState)
        state = await self.beefweb.get_player_state(
            column_map={
                "%artist%": "artist",
                "%title%": "title",
                "%length%": "length",
            }
        )
        self.assertTrue(type(state) is PlayerState)

    async def test_set_player_state(self):
        state = await self.beefweb.get_player_state()
        vol = state.volume.min // 4
        await self.beefweb.set_player_state(
            volume=vol,
            mute=False,
            position=0,
            relative_position=0,
            playback_mode=3,
        )
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.playback_mode.number, 3)
        self.assertEqual(state.volume.value, vol)

    async def test_play_states(self):
        await self.beefweb.add_playlist(title=self.plist1_title)
        playlist_id = (await self.beefweb.find_playlist(self.plist1_title)).id
        await self.beefweb.set_current_playlist(playlist_id)
        await self.beefweb.add_playlist_items(playlist_id, [self.media_path])
        await self.beefweb.sort_playlist_items(playlist_id, "%tracknumber%")

        await self.beefweb.play()
        await sleep(DEFAULT_TIME_DELAY)
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "playing")
        await self.beefweb.pause()
        await sleep(DEFAULT_TIME_DELAY)
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "paused")
        await self.beefweb.pause_toggle()
        await sleep(DEFAULT_TIME_DELAY)
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "playing")
        await self.beefweb.stop()
        await sleep(DEFAULT_TIME_DELAY)
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "stopped")

        await self.beefweb.play_specific(playlist_id, 0)
        await sleep(DEFAULT_TIME_DELAY)
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.active_item.index, 0)
        self.assertEqual(state.playback_state, "playing")
        await self.beefweb.play_next(by="%tracknumber%")
        await sleep(DEFAULT_TIME_DELAY)
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.active_item.index, 1)
        self.assertEqual(state.playback_state, "playing")
        await self.beefweb.play_previous(by="%tracknumber%")
        await sleep(DEFAULT_TIME_DELAY)
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.active_item.index, 0)
        self.assertEqual(state.playback_state, "playing")
        await self.beefweb.stop()
        await self.beefweb.play_random()
        await sleep(DEFAULT_TIME_DELAY)
        state = await self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "playing")

        await self.beefweb.remove_playlist(playlist_id)

    async def test_find_playlist(self):
        await self.beefweb.add_playlist(title=self.plist1_title)
        playlist = await self.beefweb.find_playlist(title=self.plist1_title)
        self.assertEqual(playlist.title, self.plist1_title)

        playlist = await self.beefweb.find_playlist(search_id=playlist.id)
        self.assertEqual(playlist.title, self.plist1_title)

        await self.beefweb.remove_playlist(playlist.id)

    async def test_get_playlist_items(self):
        await self.beefweb.add_playlist(title=self.plist1_title)
        playlist_id = (await self.beefweb.find_playlist(self.plist1_title)).id
        await self.beefweb.set_current_playlist(playlist_id)
        await self.beefweb.add_playlist_items(playlist_id, [self.media_path])
        await self.beefweb.sort_playlist_items(playlist_id, "%tracknumber%")

        colmap = {"%title%": "title"}
        items = await self.beefweb.get_playlist_items(
            playlist_id, offset=1, count=2, column_map=colmap
        )
        self.assertEqual(len(items), 2)
        self.assertEqual(len(items[0]), 1)
        self.assertEqual(items[0].title, "This is test track 2")
        self.assertEqual(items[1].title, "This is test track 3")

        await self.beefweb.remove_playlist(playlist_id)

    async def test_set_current_playlist(self):
        await self.beefweb.add_playlist(title=self.plist1_title)
        await self.beefweb.add_playlist(title=self.plist2_title)
        playlist1 = await self.beefweb.find_playlist(self.plist1_title)
        playlist2 = await self.beefweb.find_playlist(self.plist2_title)

        await self.beefweb.set_current_playlist(playlist1.id)
        playlist = await self.beefweb.find_playlist(playlist1.title)
        self.assertTrue(playlist.is_current)

        await self.beefweb.set_current_playlist(playlist2.index)
        playlist = await self.beefweb.find_playlist(playlist2.title)
        self.assertTrue(playlist.is_current)

        await self.beefweb.remove_playlist(playlist1.id)
        await self.beefweb.remove_playlist(playlist2.id)

    async def test_playlist_item_manipulation(self):
        await self.beefweb.add_playlist(title=self.plist1_title)
        await self.beefweb.add_playlist(title=self.plist2_title)
        await self.beefweb.add_playlist(title=self.plist3_title)
        playlist1 = await self.beefweb.find_playlist(self.plist1_title)
        playlist2 = await self.beefweb.find_playlist(self.plist2_title)
        playlist3 = await self.beefweb.find_playlist(self.plist3_title)
        await self.beefweb.set_current_playlist(playlist1.id)
        await self.beefweb.add_playlist_items(playlist1.id, [self.media_path])
        await self.beefweb.sort_playlist_items(playlist1.id, "%tracknumber%")

        await self.beefweb.copy_playlist_items(
            playlist_ref=playlist1.id, item_indices=(1, 2), dest_index=1
        )
        items = await self.beefweb.get_playlist_items(playlist1.id)
        self.assertEqual(len(items), 5)
        self.assertEqual(items[3].title, "This is test track 2")
        self.assertEqual(items[4].title, "This is test track 3")

        await self.beefweb.move_playlist_items(
            playlist_ref=playlist1.id, item_indices=(0, 3), dest_index=4
        )
        items = await self.beefweb.get_playlist_items(playlist1.id)
        self.assertEqual(len(items), 5)
        self.assertEqual(items[2].title, "This is test track 1")
        self.assertEqual(items[3].title, "This is test track 2")

        await self.beefweb.copy_between_playlists(
            source_playlist=playlist1.id,
            dest_playlist=playlist2.id,
            item_indices=[0, 1],
        )
        await self.beefweb.copy_between_playlists(
            source_playlist=playlist1.id,
            dest_playlist=playlist2.id,
            item_indices=[2],
            dest_index=1,
        )
        items = await self.beefweb.get_playlist_items(playlist2.id)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].title, "This is test track 2")
        self.assertEqual(items[1].title, "This is test track 1")
        self.assertEqual(items[2].title, "This is test track 3")

        await self.beefweb.move_between_playlists(
            source_playlist=playlist2.id,
            dest_playlist=playlist3.id,
            item_indices=(1, 2),
        )
        items = await self.beefweb.get_playlist_items(playlist3.id)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "This is test track 1")
        self.assertEqual(items[1].title, "This is test track 3")
        await self.beefweb.move_between_playlists(
            source_playlist=playlist2.id,
            dest_playlist=playlist3.id,
            item_indices=(0,),
            dest_index=0,
        )
        items = await self.beefweb.get_playlist_items(playlist3.id)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].title, "This is test track 2")

        await self.beefweb.sort_playlist_items(
            playlist_ref=playlist3.id, by="%track number%", desc=True
        )
        items = await self.beefweb.get_playlist_items(playlist3.id)
        self.assertEqual(items[0].title, "This is test track 3")
        self.assertEqual(items[1].title, "This is test track 2")
        self.assertEqual(items[2].title, "This is test track 1")

        await self.beefweb.remove_playlist_items(
            playlist_ref=playlist3.id, item_indices=(0, 2)
        )
        items = await self.beefweb.get_playlist_items(playlist3.id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "This is test track 2")

        await self.beefweb.remove_playlist(playlist1.id)
        await self.beefweb.remove_playlist(playlist2.id)
        await self.beefweb.remove_playlist(playlist3.id)

    async def test_get_browser(self):
        roots = await self.beefweb.get_browser_roots()
        self.assertTrue(any("test_media" in x.path for x in roots))

        entries = await self.beefweb.get_browser_entries(self.media_path)
        self.assertTrue(any("test1.ogg" in x.path for x in entries))

    async def tearDown(self):
        await self.beefweb.stop()
        for name in (self.plist1_title, self.plist2_title, self.plist3_title):
            try:
                plist = await self.beefweb.find_playlist(name)
                if plist is not None:
                    await self.beefweb.remove_playlist(plist.id)
            except RequestError:
                pass


if __name__ == "__main__":
    asynctest.main()
