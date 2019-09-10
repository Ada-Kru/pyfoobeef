=========
pyfoobeef
=========
Allows control of the Foobar2000 and DeaDBeeF media players through the `beefweb <https://github.com/hyperblast/beefweb>`_ plugin API.

* Both asynchronous and synchronous clients
* An asynchronous event listener with callbacks
* For Python 3.6 and up
* MIT License


Installation
------------
1. Install and configure the `beefweb <https://github.com/hyperblast/beefweb>`_ plugin for your media player.

2. Run::

    pip install pyfoobeef


Examples
--------
Synchronous client:

.. code-block:: python

    import pyfoobeef
    from time import sleep


    player = pyfoobeef.Client("localhost", 8880)

    # Add a new playlist.
    new_playlist = player.add_playlist(title="My New Playlist")
    player.set_current_playlist(new_playlist)

    # Add items to the playlist.
    player.add_playlist_items(new_playlist, items=[r"C:\Music"])

    player.play()
    # Give the media player a bit of time to actually start playing.
    sleep(0.5)

    # Columns (media data fields) to retrieve and the names to map them to.
    column_map = {
        "%artist%": "artist",
        "%title%": "title",
        "%album% - %track number% - %title%": "my_custom_column",
    }
    status = player.get_player_state(column_map)

    if status.active_item.has_columns():
        # Returned columns may be addressed by subscripting or as attributes.
        print(status.active_item.columns["artist"])
        print(status.active_item.columns.title)
        print(status.active_item.columns.my_custom_column)

    # Display the playback state (ex. "playing")
    print(status.playback_state)

    # Display information about the volume level (current, min, max, etc.)
    print(status.volume)


Asynchronous client:

.. code-block:: python

    import pyfoobeef
    import asyncio


    async def example():
        player = pyfoobeef.AsyncClient("localhost", 8880)

        # Add a new playlist.
        new_playlist = await player.add_playlist(title="My New Playlist")
        await player.set_current_playlist(new_playlist)

        # Add items to the playlist.
        await player.add_playlist_items(new_playlist, items=[r"C:\Music"])

        # sort items by length
        await player.sort_playlist_items(new_playlist, by="%length_seconds%")

        # Get information about the first 10 items in a playlist.
        items = await player.get_playlist_items(
            new_playlist,
            column_map=["%artist%", "%title%", "%length%"],
            offset=0,
            count=10,
        )
        for item in items:
            print(item)

        # Play a specific item.
        await player.play_specific(new_playlist, 4)


    asyncio.run(example())


Event listener:

.. code-block:: python

    import pyfoobeef
    import asyncio


    def print_active_item(state):
        print("Active Item:")
        print(state.active_item)


    def print_playlists(playlists):
        print("Current Playlists:")
        for playlist in playlists:
            print(playlist)


    async def example():
        listener = pyfoobeef.EventListener(
            base_url="localhost",
            port=6980,
            active_item_column_map={
                "%artist%": "artist",
                "%title%": "title",
                "%length%": "length",
            },
        )

        # Add callbacks for player events.
        listener.add_callback("player_state", print_active_item)
        listener.add_callback("playlists", print_playlists)

        # Start listening for events from the player.
        await listener.connect(reconnect_time=1)

        await asyncio.sleep(20)

        await listener.disconnect()


    asyncio.run(example())
