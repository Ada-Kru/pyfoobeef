.. pyfoobeef documentation master file, created by
   sphinx-quickstart on Wed Sep 11 10:55:14 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=========
pyfoobeef
=========

Allows control of the Foobar2000 and DeaDBeeF media players through the `beefweb <https://github.com/hyperblast/beefweb>`_ plugin API.

* Both asynchronous and synchronous clients
* An asynchronous event listener with callbacks
* For Python 3.6 and up
* MIT License


Classes
-------
.. toctree::
   :maxdepth: 4

   source/pyfoobeef

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

    # Add items to the playlist.  Note that paths including drive letters
    # are case sensitive even on Windows due to limitations of the beefweb
    # plugin (so r"c:\Music" would not work here).
    player.add_playlist_items(new_playlist, items=[r"C:\Music"])

    player.play()
    # Give the media player a bit of time to actually start playing.
    sleep(0.5)

    # Column maps represent the media data fields to retrieve and the names
    # to assign the returned data to.
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


The asynchronous client follows a very similar format:

.. code-block:: python

    import pyfoobeef
    import asyncio


    async def example():
        player = pyfoobeef.AsyncClient("localhost", 8880)

        # Add a new playlist.
        new_playlist = await player.add_playlist(title="My New Playlist")
        await player.set_current_playlist(new_playlist)

        # Add items to the playlist.  Note that paths including drive letters
        # are case sensitive even on Windows due to limitations of the beefweb
        # plugin (so r"c:\Music" would not work here).
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


The asynchronous event listener can automatically execute callbacks when certain events are received or the media players state can be determined from the EventListener object's attributes:

.. code-block:: python

    import pyfoobeef
    import asyncio


    def print_active_item(state):
        print("From player state callback.  Active item is:")
        print(state.active_item)


    def print_playlists(playlists):
        print("From playlists callback.  Current playlists:")
        for playlist in playlists:
            print(playlist)


    async def example():
        listener = pyfoobeef.EventListener(
            base_url="localhost",
            port=8880,
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

        await asyncio.sleep(10)

        # The last received information about the player state and playlists
        # can be accessed from the listener object itself.
        print("From the last player state object saved to listener."
              "  Active item is:")
        print(listener.player_state.active_item)
        print("Estimated playback position: ",
              listener.player_state.estimated_position_mmss())
        for playlist in listener.playlists:
            print(playlist)

        await asyncio.sleep(10)

        # The listener should always be disconnected when done.
        await listener.disconnect()


    asyncio.run(example())
