import asyncio
from lib.async_client import AsyncClient


async def tester():
    beefweb = AsyncClient("localhost", 6980, "test", "test")

    status = await beefweb.get_player_state(
        column_map={
            "%artist%": "artist",
            "%title%": "title",
            "%_foobar2000_version%": "fbver",
        }
    )
    print("\n\n", status.active_item)
    if status.active_item.columns is not None:
        print(
            f"{status.active_item.columns.artist} - "
            f"{status.active_item.columns.title} - "
            f"{status.active_item.columns.fbver}"
        )
    status = await beefweb.get_player_state(
        column_map={
            "%artist%": "artist",
            "%title%": "title",
            "%_foobar2000_version%": "fbver",
        }
    )


asyncio.run(tester())
