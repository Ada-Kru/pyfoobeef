#!/usr/bin/python3
import unittest
from time import sleep
from uuid import uuid1
from pathlib import Path
from pyfoobeef import Client
from pyfoobeef.exceptions import RequestError
from pyfoobeef.models import PlayerState


DEFAULT_TIME_DELAY = 0.5


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.beefweb = Client("localhost", 6980)
        self.plist1_title = str(uuid1())
        self.plist2_title = str(uuid1())
        self.plist3_title = str(uuid1())
        module_dir = Path(__file__).absolute().parent.parent
        self.media_path = str((module_dir / "test_media").resolve())

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
        playlist = self.beefweb.add_playlist(title=self.plist1_title)
        self.beefweb.set_current_playlist(playlist)
        self.beefweb.add_playlist_items(playlist, [self.media_path])
        self.beefweb.sort_playlist_items(playlist, "%tracknumber%")

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

        self.beefweb.play_specific(playlist, 0)
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

    def test_add_and_find_playlist(self):
        self.beefweb.add_playlist(title=self.plist1_title)
        playlist = self.beefweb.find_playlist(title=self.plist1_title)
        self.assertEqual(playlist.title, self.plist1_title)

        playlist = self.beefweb.find_playlist(search_id=playlist.id)
        self.assertEqual(playlist.title, self.plist1_title)

        self.beefweb.remove_playlist(playlist)

        playlist = self.beefweb.add_playlist(title=self.plist1_title)
        self.assertEqual(playlist.title, self.plist1_title)
        playlist2 = self.beefweb.add_playlist(title=self.plist2_title)
        self.assertEqual(playlist2.title, self.plist2_title)

        # insert 3rd playlist between other two
        num_playlists = len(self.beefweb.get_playlists())
        playlist3 = self.beefweb.add_playlist(
            title=self.plist3_title, index=num_playlists - 1
        )
        self.assertEqual(playlist3.title, self.plist3_title)

        self.beefweb.remove_playlist(playlist)
        self.beefweb.remove_playlist(playlist2)
        playlist = self.beefweb.add_playlist(
            title=self.plist1_title, return_playlist=False
        )
        self.assertIsNone(playlist)
        playlist = self.beefweb.add_playlist(
            title=self.plist2_title, index=-1, return_playlist=False
        )
        self.assertIsNone(playlist)

    def test_get_playlist_items(self):
        playlist = self.beefweb.add_playlist(title=self.plist1_title)
        self.beefweb.set_current_playlist(playlist)
        self.beefweb.add_playlist_items(playlist, [self.media_path])
        self.beefweb.sort_playlist_items(playlist, "%tracknumber%")

        colmap = {"%title%": "title"}
        items = self.beefweb.get_playlist_items(
            playlist, offset=1, count=2, column_map=colmap
        )
        self.assertEqual(len(items), 2)
        self.assertEqual(len(items[0]), 1)
        self.assertEqual(items[0].title, "This is test track 2")
        self.assertEqual(items[1].title, "This is test track 3")

    def test_set_current_playlist(self):
        playlist1 = self.beefweb.add_playlist(title=self.plist1_title)
        playlist2 = self.beefweb.add_playlist(title=self.plist2_title)

        self.beefweb.set_current_playlist(playlist1)
        playlist = self.beefweb.find_playlist(playlist1.title)
        self.assertTrue(playlist.is_current)

        self.beefweb.set_current_playlist(playlist2)
        playlist = self.beefweb.find_playlist(playlist2.title)
        self.assertTrue(playlist.is_current)

    def test_playlist_item_manipulation(self):
        playlist1 = self.beefweb.add_playlist(title=self.plist1_title)
        playlist2 = self.beefweb.add_playlist(title=self.plist2_title)
        playlist3 = self.beefweb.add_playlist(title=self.plist3_title)
        self.beefweb.set_current_playlist(playlist1)
        self.beefweb.add_playlist_items(playlist1, [self.media_path])
        self.beefweb.sort_playlist_items(playlist1, "%tracknumber%")

        self.beefweb.copy_playlist_items(
            playlist_ref=playlist1, item_indices=(1, 2), dest_index=1
        )
        items = self.beefweb.get_playlist_items(playlist1)
        self.assertEqual(len(items), 5)
        self.assertEqual(items[3].title, "This is test track 2")
        self.assertEqual(items[4].title, "This is test track 3")

        self.beefweb.move_playlist_items(
            playlist_ref=playlist1, item_indices=(0, 3), dest_index=4
        )
        items = self.beefweb.get_playlist_items(playlist1)
        self.assertEqual(len(items), 5)
        self.assertEqual(items[2].title, "This is test track 1")
        self.assertEqual(items[3].title, "This is test track 2")

        self.beefweb.copy_between_playlists(
            source_playlist=playlist1,
            dest_playlist=playlist2,
            item_indices=[0, 1],
        )
        self.beefweb.copy_between_playlists(
            source_playlist=playlist1,
            dest_playlist=playlist2,
            item_indices=[2],
            dest_index=1,
        )
        items = self.beefweb.get_playlist_items(playlist2)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].title, "This is test track 2")
        self.assertEqual(items[1].title, "This is test track 1")
        self.assertEqual(items[2].title, "This is test track 3")

        self.beefweb.move_between_playlists(
            source_playlist=playlist2,
            dest_playlist=playlist3,
            item_indices=(1, 2),
        )
        items = self.beefweb.get_playlist_items(playlist3)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "This is test track 1")
        self.assertEqual(items[1].title, "This is test track 3")
        self.beefweb.move_between_playlists(
            source_playlist=playlist2,
            dest_playlist=playlist3,
            item_indices=(0,),
            dest_index=0,
        )
        items = self.beefweb.get_playlist_items(playlist3)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].title, "This is test track 2")

        self.beefweb.sort_playlist_items(
            playlist_ref=playlist3, by="%track number%", desc=True
        )
        items = self.beefweb.get_playlist_items(playlist3)
        self.assertEqual(items[0].title, "This is test track 3")
        self.assertEqual(items[1].title, "This is test track 2")
        self.assertEqual(items[2].title, "This is test track 1")

        self.beefweb.remove_playlist_items(
            playlist_ref=playlist3, item_indices=(0, 2)
        )
        items = self.beefweb.get_playlist_items(playlist3)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "This is test track 2")

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
