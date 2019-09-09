#!/usr/bin/python3
import unittest
from time import sleep
from uuid import uuid1
from pathlib import Path
from sys import path as sys_path

sys_path.insert(0, "..")

from lib.client import Client, RequestError
from lib.models import PlayerState


DEFAULT_TIME_DELAY = 0.5


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.beefweb = Client("localhost", 6980)
        self.plist1_title = str(uuid1())
        self.plist2_title = str(uuid1())
        self.plist3_title = str(uuid1())
        module_dir = Path(__file__).absolute().parent.parent
        self.media_path = str(module_dir / "test_media")

    def test_get_player_state(self):
        state = self.beefweb.get_player_state()
        self.assertTrue(type(state) is PlayerState)
        state = self.beefweb.get_player_state(
            column_map={
                "%artist%": "artist",
                "%title%": "title",
                "%length%": "length",
            }
        )
        self.assertTrue(type(state) is PlayerState)

    def test_set_player_state(self):
        state = self.beefweb.get_player_state()
        vol = state.volume.min // 4
        self.beefweb.set_player_state(
            volume=vol,
            mute=False,
            position=0,
            relative_position=0,
            playback_mode=3,
        )
        state = self.beefweb.get_player_state()
        self.assertEqual(state.playback_mode.number, 3)
        self.assertEqual(state.volume.value, vol)

    def test_play_states(self):
        self.beefweb.add_playlist(title=self.plist1_title)
        playlist_id = self.beefweb.find_playlist(self.plist1_title).id
        self.beefweb.set_current_playlist(playlist_id)
        self.beefweb.add_playlist_items(playlist_id, [self.media_path])
        self.beefweb.sort_playlist_items(playlist_id, "%tracknumber%")

        self.beefweb.play()
        sleep(DEFAULT_TIME_DELAY)
        state = self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "playing")
        self.beefweb.pause()
        sleep(DEFAULT_TIME_DELAY)
        state = self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "paused")
        self.beefweb.pause_toggle()
        sleep(DEFAULT_TIME_DELAY)
        state = self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "playing")
        self.beefweb.stop()
        sleep(DEFAULT_TIME_DELAY)
        state = self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "stopped")

        self.beefweb.play_specific(playlist_id, 0)
        sleep(DEFAULT_TIME_DELAY)
        state = self.beefweb.get_player_state()
        self.assertEqual(state.active_item.index, 0)
        self.assertEqual(state.playback_state, "playing")
        self.beefweb.play_next(by="%tracknumber%")
        sleep(DEFAULT_TIME_DELAY)
        state = self.beefweb.get_player_state()
        self.assertEqual(state.active_item.index, 1)
        self.assertEqual(state.playback_state, "playing")
        self.beefweb.play_previous(by="%tracknumber%")
        sleep(DEFAULT_TIME_DELAY)
        state = self.beefweb.get_player_state()
        self.assertEqual(state.active_item.index, 0)
        self.assertEqual(state.playback_state, "playing")
        self.beefweb.stop()
        self.beefweb.play_random()
        sleep(DEFAULT_TIME_DELAY)
        state = self.beefweb.get_player_state()
        self.assertEqual(state.playback_state, "playing")

        self.beefweb.remove_playlist(playlist_id)

    def test_find_playlist(self):
        self.beefweb.add_playlist(title=self.plist1_title)
        playlist = self.beefweb.find_playlist(title=self.plist1_title)
        self.assertEqual(playlist.title, self.plist1_title)

        playlist = self.beefweb.find_playlist(search_id=playlist.id)
        self.assertEqual(playlist.title, self.plist1_title)

        self.beefweb.remove_playlist(playlist.id)

    def test_get_playlist_items(self):
        self.beefweb.add_playlist(title=self.plist1_title)
        playlist_id = self.beefweb.find_playlist(self.plist1_title).id
        self.beefweb.set_current_playlist(playlist_id)
        self.beefweb.add_playlist_items(playlist_id, [self.media_path])
        self.beefweb.sort_playlist_items(playlist_id, "%tracknumber%")

        colmap = {"%title%": "title"}
        items = self.beefweb.get_playlist_items(
            playlist_id, offset=1, count=2, column_map=colmap
        )
        self.assertEqual(len(items), 2)
        self.assertEqual(len(items[0]), 1)
        self.assertEqual(items[0].title, "This is test track 2")
        self.assertEqual(items[1].title, "This is test track 3")

        self.beefweb.remove_playlist(playlist_id)

    def test_set_current_playlist(self):
        self.beefweb.add_playlist(title=self.plist1_title)
        self.beefweb.add_playlist(title=self.plist2_title)
        playlist1 = self.beefweb.find_playlist(self.plist1_title)
        playlist2 = self.beefweb.find_playlist(self.plist2_title)

        self.beefweb.set_current_playlist(playlist1.id)
        playlist = self.beefweb.find_playlist(playlist1.title)
        self.assertTrue(playlist.is_current)

        self.beefweb.set_current_playlist(playlist2.index)
        playlist = self.beefweb.find_playlist(playlist2.title)
        self.assertTrue(playlist.is_current)

        self.beefweb.remove_playlist(playlist1.id)
        self.beefweb.remove_playlist(playlist2.id)

    def test_playlist_item_manipulation(self):
        self.beefweb.add_playlist(title=self.plist1_title)
        self.beefweb.add_playlist(title=self.plist2_title)
        self.beefweb.add_playlist(title=self.plist3_title)
        playlist1 = self.beefweb.find_playlist(self.plist1_title)
        playlist2 = self.beefweb.find_playlist(self.plist2_title)
        playlist3 = self.beefweb.find_playlist(self.plist3_title)
        self.beefweb.set_current_playlist(playlist1.id)
        self.beefweb.add_playlist_items(playlist1.id, [self.media_path])
        self.beefweb.sort_playlist_items(playlist1.id, "%tracknumber%")

        self.beefweb.copy_playlist_items(
            playlist_ref=playlist1.id, item_indices=(1, 2), dest_index=1
        )
        items = self.beefweb.get_playlist_items(playlist1.id)
        self.assertEqual(len(items), 5)
        self.assertEqual(items[3].title, "This is test track 2")
        self.assertEqual(items[4].title, "This is test track 3")

        self.beefweb.move_playlist_items(
            playlist_ref=playlist1.id, item_indices=(0, 3), dest_index=4
        )
        items = self.beefweb.get_playlist_items(playlist1.id)
        self.assertEqual(len(items), 5)
        self.assertEqual(items[2].title, "This is test track 1")
        self.assertEqual(items[3].title, "This is test track 2")

        self.beefweb.copy_between_playlists(
            source_playlist=playlist1.id,
            dest_playlist=playlist2.id,
            item_indices=[0, 1],
        )
        self.beefweb.copy_between_playlists(
            source_playlist=playlist1.id,
            dest_playlist=playlist2.id,
            item_indices=[2],
            dest_index=1,
        )
        items = self.beefweb.get_playlist_items(playlist2.id)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].title, "This is test track 2")
        self.assertEqual(items[1].title, "This is test track 1")
        self.assertEqual(items[2].title, "This is test track 3")

        self.beefweb.move_between_playlists(
            source_playlist=playlist2.id,
            dest_playlist=playlist3.id,
            item_indices=(1, 2),
        )
        items = self.beefweb.get_playlist_items(playlist3.id)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "This is test track 1")
        self.assertEqual(items[1].title, "This is test track 3")
        self.beefweb.move_between_playlists(
            source_playlist=playlist2.id,
            dest_playlist=playlist3.id,
            item_indices=(0,),
            dest_index=0,
        )
        items = self.beefweb.get_playlist_items(playlist3.id)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].title, "This is test track 2")

        self.beefweb.sort_playlist_items(
            playlist_ref=playlist3.id, by="%track number%", desc=True
        )
        items = self.beefweb.get_playlist_items(playlist3.id)
        self.assertEqual(items[0].title, "This is test track 3")
        self.assertEqual(items[1].title, "This is test track 2")
        self.assertEqual(items[2].title, "This is test track 1")

        self.beefweb.remove_playlist_items(
            playlist_ref=playlist3.id, item_indices=(0, 2)
        )
        items = self.beefweb.get_playlist_items(playlist3.id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "This is test track 2")

        self.beefweb.remove_playlist(playlist1.id)
        self.beefweb.remove_playlist(playlist2.id)
        self.beefweb.remove_playlist(playlist3.id)

    def test_get_browser(self):
        roots = self.beefweb.get_browser_roots()
        self.assertTrue(any("test_media" in x.path for x in roots))

        entries = self.beefweb.get_browser_entries(self.media_path)
        self.assertTrue(any("test1.ogg" in x.path for x in entries))

    def tearDown(self):
        self.beefweb.stop()
        for name in (self.plist1_title, self.plist2_title, self.plist3_title):
            try:
                plist = self.beefweb.find_playlist(name)
                if plist is not None:
                    self.beefweb.remove_playlist(plist.id)
            except RequestError:
                pass


if __name__ == "__main__":
    unittest.main()
