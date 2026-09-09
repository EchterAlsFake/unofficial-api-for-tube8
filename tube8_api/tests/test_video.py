import pytest
from base_api import DownloadConfigHLS

from tube8_api import Client


@pytest.mark.asyncio
async def test_all():
    client = Client()
    video = await client.get_video("https://www.tube8.com/porn-video/81330021/")

    assert isinstance(video.title, str) and len(video.title) > 0
    assert isinstance(video.video_id, str) and len(video.video_id) > 0
    assert isinstance(video.media_definitions, list) and len(video.media_definitions) > 0
    assert isinstance(video.duration, int) and len(str(video.duration)) > 0
    assert isinstance(video.thumbnail, str) and len(video.thumbnail) > 0
    assert isinstance(video.author_name, str) and len(video.author_name) > 0

    config = DownloadConfigHLS(quality="worst", return_report=True)
    stuff = await video.download(config)
    assert stuff.status == "completed"


def test_extract_html_snippet():
    from base_api import BaseCore
    from tube8_api.api import Video

    html_sample = '''<div id="pageWrapper" class="site-wrapper">
<header class="site-header"></header>
<div class="main_content tm_main_content" id="mainContent">
    <div id="watch-container" class="container tm_container " data-video-id="266869831">
        <div class="watch-contentWrapper">
            <div id="videoContainer" data-testid="video_player_container" class="mgp_desktop">
                <script id="tm_pc_player_setup">
                    page_params.video_player_setup = {
                        playervars: {"disable_sharebar":1,"htmlPauseRoll":"true","htmlPostRoll":"false","embedCode":"<iframe src=\\"/embed/266869831/\\" frameborder=\\"0\\" width=\\"560\\" height=\\"340\\" scrolling=\\"no\\" allowfullscreen></iframe>","autoplay":true,"autoreplay":"false","hidePostPauseRoll":"false","video_unavailable":"false","pauseroll_url":"","postroll_url":"","video_duration":"20","actionTags":"","link_url":"https://www.tube8.com/porn-video/266869831/","related_url":"https://www.tube8.com/video/player_related_datas?id=266869831","image_url":"https://pix-cdn77.t8cdn.com/c6371/videos/202609/03/61178365/original_61178365.mov/plain/ex:1:no/bg:0:0:0/rs:fit:1280:720/vts:15?hash=-P7Ioz9JKo7fBVJuQ66FU4mDt5k=&validto=1788948769","video_title":"Teasing curves and gaming thrills await you! \\ud83c\\udf51\\ud83c\\udfae\\u2728","defaultQuality":[720,480,240,1080],"vcServerUrl":"/svvt/add?stype=svv&svalue=266869831&snonce=a0qsqnr5dysy192b&skey=f82cb0bc25d918bc7e46f92dc525e43fe5aa2c8ef6e16a0f4efa41992a23ccd8&stime=1788945169","mediaDefinitions":[{"format":"hls","videoUrl":"https://www.tube8.com/media/hls/?s=eyJ2a2V5IjoyNjY4Njk4MzEsInMiOiJhYTYyOTU1YTI3NzBjNzNmNGFhYjU2MTE0NmVjYTliOTcyYmEzNmYyNGIxZWRjODI2YmU0ZDJjMTJmMGQ3ZjRiIiwiZ3QiOjE3ODg5NDUxNjksImUiOmZhbHNlfQ","remote":true,"segmentFormats":{"video":"fmp4","audio":"aac"}},{"format":"mp4","videoUrl":"https://www.tube8.com/media/mp4/?s=eyJ2a2V5IjoyNjY4Njk4MzEsInMiOiJhYTYyOTU1YTI3NzBjNzNmNGFhYjU2MTE0NmVjYTliOTcyYmEzNmYyNGIxZWRjODI2YmU0ZDJjMTJmMGQ3ZjRiIiwiZ3QiOjE3ODg5NDUxNjksImUiOmZhbHNlfQ","remote":true,"segmentFormats":{"video":"mp4","audio":"aac"}}]}
                    };
                </script>
            </div>
            <div class="watch-metadata">
                <h1 class="videoTitle tm_videoTitle">Teasing curves and gaming thrills await you! 🍑🎮✨</h1>
                <div class="video-actionsWrapper">
                    <div class="feature-action feature-actionViews"><span class="infoValue tm_infoValue">37</span></div>
                </div>
                <div class="video-uploaderInfoWrapper">
                    <div class="submitByLink">
                        <a href="/amateur/174f847/">little sinful angel</a>
                    </div>
                    <span class="publishedDate">Published on September 7, 2026</span>
                </div>
            </div>
        </div>
    </div>
</div>
</div>'''

    video = Video(url="https://www.tube8.com/porn-video/266869831/", core=BaseCore())
    data = video._extract_html(html_sample)

    assert data["video_id"] == "266869831"
    assert data["title"] == "Teasing curves and gaming thrills await you! 🍑🎮✨"
    assert data["duration"] == 20
    assert data["thumbnail"] == "https://pix-cdn77.t8cdn.com/c6371/videos/202609/03/61178365/original_61178365.mov/plain/ex:1:no/bg:0:0:0/rs:fit:1280:720/vts:15?hash=-P7Ioz9JKo7fBVJuQ66FU4mDt5k=&validto=1788948769"
    assert data["author_name"] == "little sinful angel"
    assert data["views"] == "37"
    assert data["publish_date"] == "Published on September 7, 2026"
    assert data["embed_url"] == "https://www.tube8.com/embed/266869831/"
    assert len(data["media_definitions"]) == 2
    assert data["m3u8_url"].startswith("https://www.tube8.com/media/hls/")