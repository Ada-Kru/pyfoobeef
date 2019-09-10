from lib.client import Client
from pprint import pprint
import time


beefweb = Client('localhost', 6980, 'test', 'test')

status = beefweb.get_player_state(column_map={'%artist%': 'artist',
                                              '%title%': 'title',
                                              '%_foobar2000_version%': 'fbver'})
print('\n\n', status.active_item)
if status.active_item.columns is not None:
    pprint(f'{status.active_item.columns.artist} - {status.active_item.columns.title} - {status.active_item.columns.fbver}')
print(status.active_item.duration_mss())

# plists = beefweb.get_playlists()
# pprint(plists.find_playlist(search_id='p5', find_last=True))

# beefweb.play_specific(playlist_ref='p5', index=90)

# playlists = beefweb.get_playlists()
# print(playlists.playlists)
# print(playlists.find_playlist('Movies').item_count)

# items = beefweb.get_playlist_items(playlist_ref='p3', range=(200, 1000000))
# print(items.find_item(album_artist='Yello', return_index=True))

# beefweb.set_current_playlist('p1')

# beefweb.add_playlist(title='test_playlist')
# playlists = beefweb.get_playlists()
# test_playlist_id = playlists.find_playlist('test_playlist').id
# time.sleep(1)
# beefweb.set_playlist_title(playlist_ref=test_playlist_id, title="Changed Title")
# time.sleep(1)
# beefweb.move_playlist(playlist_ref=test_playlist_id, new_index=0)
# time.sleep(1)
# beefweb.clear_playlist(playlist_ref=test_playlist_id)
# beefweb.remove_playlist(playlist_ref=test_playlist_id)

# roots = beefweb.get_browser_roots()
# pprint(roots.entries)
# root_path = roots.entries[0].path
# entries = beefweb.get_browser_entries(path=root_path)
# pprint(entries.entries)

# playlists = beefweb.get_playlists()
# test_playlist = playlists.find_playlist('test_playlist')
# if test_playlist is not None:
#     beefweb.remove_playlist(playlist_ref=test_playlist.id)
# test_playlist2 = playlists.find_playlist('test_playlist2')
# if test_playlist2 is not None:
#     beefweb.remove_playlist(playlist_ref=test_playlist2.id)
#
# beefweb.add_playlist(title='test_playlist')
# playlists = beefweb.get_playlists()
# test_playlist_id = playlists.find_playlist('test_playlist').id
# beefweb.set_current_playlist(test_playlist_id)
# beefweb.add_playlist_items(test_playlist_id, items=[r'C:\Adamu\temp'])

# beefweb.add_playlist(title='test_playlist2')
# playlists = beefweb.get_playlists()
# test_playlist2_id = playlists.find_playlist('test_playlist2').id

# beefweb.sort_playlist_items(test_playlist_id, by='%length_seconds%', desc=True)
# playlist_items = beefweb.get_playlist_items(test_playlist_id)
# pprint(playlist_items.playlist_items)
# results = playlist_items.find_playlist_item(title="Craig Safan - Ending On Fire")
# print(results)
# beefweb.remove_playlist_items(test_playlist_id, item_indices=[3])
# playlist_items = beefweb.get_playlist_items(test_playlist_id)
# pprint(playlist_items.playlist_items)
# beefweb.move_playlist_items(test_playlist_id, item_indices=[3, 4], target_index=1)

# beefweb.copy_playlist_items(test_playlist_id, item_indices=[2, 3], target_index=0)
# beefweb.copy_between_playlists(test_playlist_id, test_playlist2_id, item_indices=[2, 3], target_index=0)

# beefweb.move_between_playlists(test_playlist_id, test_playlist2_id, item_indices=[2, 3], target_index=0)
# beefweb.get_artwork(test_playlist_id, index=0)
