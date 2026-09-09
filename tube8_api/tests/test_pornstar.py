import pytest
from tube8_api import Client


@pytest.mark.asyncio
async def test_all():
    client = Client()
    pornstar = await client.get_pornstar("https://www.tube8.com/pornstar/nancy-a/")

    assert isinstance(pornstar.name, str) and len(pornstar.name) > 0
    assert isinstance(pornstar.pornstar_information, dict) and len(pornstar.pornstar_information) > 0

    idx = 0
    async for video in pornstar.get_videos():
        idx += 1

        item = video.unwrap()
        assert isinstance(item.title, str) and len(item.title) > 0

        if idx >= 3:
            break


def test_extract_html_snippet():
    from base_api import BaseCore
    from tube8_api.api import Pornstar

    html_sample = '''<div id="pageWrapper" class="site-wrapper">
<div id="profileInfo">
    <div class="main-information">
        <div class="name-wrapper">
            <h1 class="name-title">Alina Angel</h1>
        </div>
        <div class="stats-bar-wrapper">
            <div class="main-stats-bar">
                <ul class="main-stats-wrapper">
                    <li class="info-stat">
                        <p class="info-stat-label">Model Rank</p>
                        <p class="info-stat-data">1</p>
                    </li>
                    <li class="info-stat">
                        <p class="info-stat-label">Views</p>
                        <p class="info-stat-data">699K</p>
                    </li>
                    <li class="info-stat">
                        <p class="info-stat-label">Subscribers</p>
                        <p class="info-stat-data">3.9K</p>
                    </li>
                </ul>
            </div>
        </div>
    </div>
    <div id="DrawerProfileInfo">
        <ul class="profile-info">
            <li class="info-stat">
                <p class="info-stat-label">Astrology</p>
                <p class="info-stat-data">Capricorn</p>
            </li>
            <li class="info-stat">
                <p class="info-stat-label">Years Active</p>
                <p class="info-stat-data">2021 to Present (Started around 51 years old)</p>
            </li>
            <li class="info-stat">
                <p class="info-stat-label">Measurements</p>
                <p class="info-stat-data">34D--</p>
            </li>
        </ul>
        <div class="known-for-wrapper">
            <span class="known-for-title">Best Known For:</span>
            <ul class="known-for-tags-wrapper">
                <li class="known-for-tag">
                    <a class="known-for-text" href="/cat/hd/">HD</a>
                </li>
            </ul>
        </div>
        <div class="known-for-wrapper">
            <span class="known-for-title">Featured in:</span>
            <ul class="known-for-tags-wrapper">
                <li class="known-for-tag">
                    <a class="known-for-text" href="/channel/teamskeet/">Team Skeet</a>
                </li>
            </ul>
        </div>
    </div>
</div>
</div>'''

    ps = Pornstar(url="https://www.tube8.com/pornstar/alina-angel/", core=BaseCore())
    data = ps._extract_html(html_sample)
    assert data["name"] == "Alina Angel"
    assert data["pornstar_information"]["Model Rank"] == "1"
    assert data["pornstar_information"]["Views"] == "699K"
    assert data["pornstar_information"]["Subscribers"] == "3.9K"
    assert data["pornstar_information"]["Astrology"] == "Capricorn"
    assert data["pornstar_information"]["Best Known For"] == ["HD"]
    assert data["pornstar_information"]["Featured in"] == ["Team Skeet"]

