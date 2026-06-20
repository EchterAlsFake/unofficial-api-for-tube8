import pytest
from tube8_api import Client

@pytest.mark.asyncio
async def test_all():
    client = Client()
    channel = await client.get_channel("https://www.tube8.com/pornstar/nancy-a/")

    assert isinstance(channel.name, str) and len(channel.name) > 0
    assert isinstance(channel.views, str) and len(channel.views) > 0
    assert isinstance(channel.rank, str) and len(channel.rank) > 0
    assert isinstance(channel.subscribers_count, str) and len(channel.subscribers_count) > 0

    idx = 0
    async for video in channel.get_videos():
        idx += 1
        assert isinstance(video.title, str) and len(video.title) > 0

        if idx >= 3:
            break

