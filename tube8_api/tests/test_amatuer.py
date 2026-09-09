import pytest
from tube8_api import Client


@pytest.mark.asyncio
async def test_all():
    client = Client()
    amateur = await client.get_amateur("https://www.tube8.com/amateur/e6cd031-ph/")

    assert isinstance(amateur.name, str) and len(amateur.name) > 0

    idx = 0
    async for video in amateur.get_videos():
        idx += 1

        assert isinstance(video.unwrap().title, str)

        if idx >= 3:
            break


def test_extract_html_snippet():
    from base_api import BaseCore
    from tube8_api.api import Amateur, User

    html_sample = '''<div id="pageWrapper" class="site-wrapper">
<div class="main-information">
    <div class="name-wrapper">
        <h1 class="name-title">
            MidnightMuseX
        </h1>
    </div>
</div>
</div>'''

    amateur = Amateur(url="https://www.tube8.com/amateur/e6cd031-ph/", core=BaseCore())
    data = amateur._extract_html(html_sample)
    assert data["name"] == "MidnightMuseX"

    user = User(url="https://www.tube8.com/user/midnightmusex/", core=BaseCore())
    data_user = user._extract_html(html_sample)
    assert data_user["name"] == "MidnightMuseX"

