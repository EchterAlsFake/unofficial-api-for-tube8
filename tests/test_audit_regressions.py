import pytest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from tube8_api import api


def test_search_query_is_one_value():
    client = object.__new__(api.Client)
    client.core = object()
    with patch.object(api, "scrape_stream") as stream:
        client.search("a&b/# 日本", pages=2)
    urls = stream.call_args.kwargs["target_page_urls"]
    assert len(urls) == len(set(urls)) == 2
    for url in urls:
        assert parse_qs(urlsplit(url).query)["q"] == ["a&b/# 日本"]
        assert not urlsplit(url).fragment


def test_subscribers_are_not_video_count():
    html = '<h1>Channel</h1><p class="info-stat-data">1</p><p class="info-stat-data">2</p><p class="info-stat-data">300</p>'
    data = api.Channel(
        url="https://www.tube8.com/channel/test/", core=object()
    )._extract_html(html)
    assert data["videos_count"] is None


@pytest.mark.asyncio
async def test_cli_closes_session_and_reports_false_download(capsys, tmp_path):
    from unittest.mock import AsyncMock, MagicMock
    from base_api import BaseCore
    from base_api.modules.config import RuntimeConfig

    core = BaseCore(RuntimeConfig())
    video = MagicMock(title="Example", length="10", url="https://example.com/video")
    video.load_fields = AsyncMock()
    video.download = AsyncMock(return_value=False)
    client = MagicMock()
    client.get_video = AsyncMock(return_value=video)
    with (
        patch.object(api, "BaseCore", return_value=core),
        patch.object(api, "Client", return_value=client),
    ):
        await api.run_main(
            ["--download", "https://example.com/video", "--output", str(tmp_path)]
        )
    assert core.session is None
    output = capsys.readouterr().out
    assert "Download complete:" not in output
    assert "Done ->" not in output
    assert "Download did not complete" in output


@pytest.mark.asyncio
async def test_empty_user_page_does_not_load_cookie_schema_name():
    from unittest.mock import AsyncMock

    user = api.User(url="https://www.tube8.com/user/missing/", core=object())
    html = '<div id="mainContent"></div><script type="application/ld+json">{"name":"Cookies"}</script>'
    with patch.object(api, "get_html_content", AsyncMock(return_value=html)):
        with pytest.raises(ValueError, match="Profile identity not found"):
            await user._load_html()

def test_french_channel_video_count_does_not_become_subscribers():
    labels=['rang','Vues','Abonnés','Vidéos']
    html=''.join('<li class="info-stat"><p class="info-stat-label">'+label+'</p><p class="info-stat-data">'+str(i)+'</p></li>' for i,label in enumerate(labels,1))
    data=api.Channel(url='https://www.tube8.fr/channel/example/',core=object())._extract_html(html)
    assert data['rank'] == '1' and data['views'] == '2' and data['videos_count'] == '4'

@pytest.mark.asyncio
async def test_unknown_global_session_user_is_not_profile_identity():
    from unittest.mock import AsyncMock
    user=api.User(url='https://www.tube8.com/user/missing/',core=object())
    html='<div id="mainContent"></div><script>var config={username: "Unknown"};</script>'
    with patch.object(api,'get_html_content',AsyncMock(return_value=html)):
        with pytest.raises(ValueError,match='Profile identity not found'):
            await user._load_html()
