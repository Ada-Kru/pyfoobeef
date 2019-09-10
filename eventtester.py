#!/usr/bin/python3
import asyncio
from lib.event_listener import EventListener

# from pprint import pprint


def print_state(state):
    print(state.active_item)


def print_items(items):
    print('items:')
    for item in items:
        print(item)


async def tester():
    listener = EventListener(
        base_url="localhost",
        port=6980,
        active_item_column_map={
            "%artist%": "artist",
            "%title%": "title",
            "%length%": "length",
        },
        no_active_item_ignore_time=0,
        playlist_ref='p5',
        playlist_items_column_map={
            "%artist%": "artist",
            "%title%": "title",
            "%length%": "length",
        },
        offset=0,
        count=3,
        username="test",
        password="test",
    )
    listener.add_callback("player_state", print_state)
    listener.add_callback("playlist_items", print_items)
    await listener.connect(reconnect_time=1)
    for i in range(1):
        await asyncio.sleep(1)
        print(i, listener.is_connected())
        if listener.player_state is not None:
            print(listener.player_state.estimated_position_mmss())
        # print(
        #     "state: ",
        #     listener._connection.ready_state if listener._connection else None,
        # )
        # print(
        #     "state: ",
        #     listener._connection._response.status
        #     if listener._connection._response
        #     else None,
        # )
    # await asyncio.sleep(2)
    # print('disconnecting...')
    # await listener.disconnect()
    # await asyncio.sleep(2)
    # print('done')
    #
    # await listener.connect(reconnect_time=1)
    # await asyncio.sleep(2)
    # print('disconnecting...')
    # await listener.disconnect()
    # await asyncio.sleep(2)
    # print('done')

    await listener.disconnect()


asyncio.run(tester())
