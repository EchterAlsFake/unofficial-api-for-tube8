import pytest
from tube8_api import Client

@pytest.mark.asyncio
async def test_all():
    client = Client()
    channel = await client.get_channel("https://www.tube8.com/pornstar/nancy-a/")

    assert isinstance(channel.name, str) and len(channel.name) > 0
    assert isinstance(channel.views, str) and len(channel.views) > 0
    assert isinstance(channel.rank, str) and len(channel.rank) > 0
    assert isinstance(channel.videos_count, str) and len(channel.videos_count) > 0

    idx = 0
    async for video in channel.get_videos():
        idx += 1
        item = video.unwrap()
        assert isinstance(item.title, str) and len(item.title) > 0

        if idx >= 3:
            break


def test_extract_html_snippet():
    from base_api import BaseCore
    from tube8_api.api import Channel

    # Channel page snippet
    html_channel = '''<div id="pageWrapper" class="site-wrapper">
<div class="main-information">
    <div class="name-wrapper">
        <h1 class="name-title">Team Skeet</h1>
    </div>
    <div class="stats-bar-wrapper">
        <div class="main-stats-bar">
            <ul class="main-stats-wrapper">
                <li class="info-stat">
                    <p class="info-stat-label">Rank</p>
                    <p class="info-stat-data">9</p>
                </li>
                <li class="info-stat">
                    <p class="info-stat-label">Views</p>
                    <p class="info-stat-data">39.2M</p>
                </li>
                <li class="info-stat">
                    <p class="info-stat-label">Subscribers</p>
                    <p class="info-stat-data">483</p>
                </li>
                <li class="info-stat">
                    <p class="info-stat-label">Videos</p>
                    <p class="info-stat-data">1.8K</p>
                </li>
            </ul>
        </div>
    </div>
</div>
</div>'''

    channel = Channel(url="https://www.tube8.com/channel/teamskeet/", core=BaseCore())
    data = channel._extract_html(html_channel)
    assert data["name"] == "Team Skeet"
    assert data["rank"] == "9"
    assert data["views"] == "39.2M"
    assert data["videos_count"] == "1.8K"

