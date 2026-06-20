"""
Copyright (C) 2026 Johannes Habel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations
import os
import re
import json
import logging
import asyncio

from typing import AsyncGenerator
from functools import cached_property
from curl_cffi import Response, AsyncSession
from base_api.modules.type_hints import DownloadReport
from base_api.base import BaseCore, setup_logger, Helper
from base_api.modules.errors import InvalidProxy, UnknownError, NetworkingError, BotProtectionDetected, ResourceGone
try:
    import lxml
    parser = "lxml" # Faster speeds, but more dependencies

except (ModuleNotFoundError, ImportError):
    parser = "html.parser" # Fallback to classic HTML parser (will work fine)

try:
    from modules.consts import *
    from modules.errors import *
    from modules.type_hints import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *
    from .modules.errors import *
    from .modules.type_hints import *


async def on_error(url: str, error: Exception, attempt: int) -> bool:
    print(f"URL: {url}, ERROR: {error}, Attempt: {attempt}")

    if isinstance(error, ResourceGone):
        return False

    return True


async def get_html_content(core: BaseCore, url: str) -> str | None | dict:
    try:
        content = await core.fetch(url)
        if isinstance(content, str):
            return content

        if isinstance(content, Response):
            if content.status_code == 404:
                raise NotFound(f"Server returned 404 for: {url}")

    except NetworkingError as e:
        raise NetworkError(str(e)) from e

    except InvalidProxy as e:
        raise ProxyError(str(e)) from e

    except BotProtectionDetected as e:
        raise BotDetection(str(e)) from e

    except UnknownError as e:
        raise UnknownNetworkError(str(e)) from e

class Video:
    def __init__(self, url: str, core: BaseCore, html_content: str | None = None):
        self.core = core
        self.url = url
        self.html_content = html_content
        self._soup = None
        self.script = None
        self.logger = setup_logger(name="Thumbzilla API - [Video]", level=logging.ERROR)

    def enable_logging(self, log_file: str | None = None, level: int | None =None, log_ip: str | None = None, log_port: int | None = None):
        if not level:
            level = logging.DEBUG

        self.logger = setup_logger(name="Thumbzilla API - [Client]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)

    @property
    def soup(self) -> BeautifulSoup:
        if not self._soup:
            raise ValueError("You probably forgot to call init")

        return self._soup

    async def init(self):
        if not self.html_content:
            self.html_content = await get_html_content(core=self.core, url=self.url)

        assert isinstance(self.html_content, str)
        self._soup = BeautifulSoup(self.html_content, parser)
        self.script = self.parse_script()
        return self

    def parse_script(self):
        """
        Extracts the JSON script
        :return:
        """
        stuff = self.soup.find("script", attrs={"type": "application/ld+json"}).text
        return json.loads(stuff).get("@graph")

    @cached_property
    def video_id(self) -> str:
        """Extracts the unique video ID."""
        return re.search(r'-video/(\d+)', self.url).group(1)

    @cached_property
    def duration(self) -> int:
        """Returns the video duration in seconds."""
        return int(re.search(r'PT(\d+)S', self.script[1].get("duration")).group(1))

    @cached_property
    def thumbnail(self) -> str:
        """Returns the main preview image/poster URL."""
        return self.script[1].get("thumbnailUrl")

    @cached_property
    def embed_url(self) -> str:
        return self.script[1].get("embedUrl")

    @cached_property
    def views(self) -> str:
        return self.script[1].get("interactionCount")

    @cached_property
    def publish_date(self) -> str:
        return self.script[1].get("uploadDate")
    @cached_property
    def publish_date_thumbnail(self) -> str:
        return self.script[0].get("datePublished")

    @cached_property
    def description(self) -> str:
        return self.script[0].get("description")

    @cached_property
    def title(self) -> str:
        return self.script[0].get("name")

    @cached_property
    def author_name(self) -> str:
        return self.script[0].get("author")


    # --- Video Streams & Formats ---

    @cached_property
    def media_definitions(self) -> dict:
        """Returns the raw list of dictionaries containing video streams (HLS, MP4)."""
        assert isinstance(self.html_content, str)
        return json.loads(re.search(r'"mediaDefinitions"\s*:\s*(\[.*?])', self.html_content).group(1))

    async def m3u8_base_url(self) -> str | None:
        """Convenience property to quickly get the main HLS adaptive stream path."""
        url = None
        for media in self.media_definitions:
            if media.get('format') == 'hls':
                url = media.get('videoUrl')

        if not url:
            raise ValueError("Could not extract the HLS URL, please report this!")

        assert isinstance(url, str)
        stuff = await get_html_content(core=self.core, url=url)
        assert isinstance(stuff, str)
        data = json.loads(stuff)

        m3u8_lines = ["#EXTM3U", "#EXT-X-VERSION:3"]

        for stream in data:
            quality = stream.get("quality", "unknown")
            width = stream.get("width", 720)
            height = stream.get("height", 404)
            url = stream.get("videoUrl", "")

            if not url:
                continue

            # Rough bandwidth estimation based on standard stream naming conventions
            # (e.g., 4000K = 4,000,000 bps, 2000K = 2,000,000 bps)
            # If '1080P_4000K' is in the URL, we use 4000000. Default to a sensible fallback.
            bandwidth = 4000000
            if "4000K" in url:
                bandwidth = 4000000
            elif "2000K" in url:
                bandwidth = 2000000
            elif "1000K" in url:
                bandwidth = 1000000

            # Adjust dimensions safely if height changes per quality
            # Your JSON snippet showed height 404 for all, but typically:
            stream_height = int(quality) if quality.isdigit() else height
            # Rough 16:9 aspect ratio calculation for width if it's dynamic
            stream_width = int(stream_height * (16 / 9)) if quality.isdigit() else width

            # Append the stream info tag with attributes
            m3u8_lines.append(
                f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},'
                f'RESOLUTION={stream_width}x{stream_height},'
                f'NAME="{quality}p"'
            )
            # The line immediately following the tag must be the URI
            m3u8_lines.append(url)

        return "\n".join(m3u8_lines)


    async def download(self, quality, path="./", callback: callback_hint=None, no_title=False, remux: bool = False,
                 callback_remux: callback_hint=None, start_segment: int = 0, stop_event: asyncio.Event | None = None,
                 segment_state_path: str | None = None, segment_dir: str | None = None,
                 return_report: bool = False, cleanup_on_stop: bool = True, keep_segment_dir: bool = False
                 ) -> bool | DownloadReport:
        """
        :param callback:
        :param quality:
        :param path:
        :param no_title:
        :param remux:
        :param callback_remux:
        :param start_segment:
        :param stop_event:
        :param segment_state_path:
        :param segment_dir:
        :param return_report:
        :param cleanup_on_stop:
        :param keep_segment_dir:
        :return:
        """
        if not no_title:
            path = os.path.join(path, f"{self.title}.mp4")

        return await self.core.download(video=self, quality=quality, path=path, callback=callback, remux=remux,
                                         callback_remux=callback_remux, start_segment=start_segment,
                                         stop_event=stop_event,
                                         segment_state_path=segment_state_path, segment_dir=segment_dir,
                                         return_report=return_report,
                                         cleanup_on_stop=cleanup_on_stop, keep_segment_dir=keep_segment_dir)


class UserHelper(Helper):
    def __init__(self, url: str, core: BaseCore):
        super().__init__(core=core, video_constructor=Video, alternative_constructor=None)
        self.url = url
        self.core = core
        self.html_content = None
        self.logger = setup_logger(name="Tube8 API - [Amateur]", log_file=None, level=logging.ERROR)

    def enable_logging(self, log_file: str | None = None, level: int | None = None, log_ip: str | None = None,
                       log_port: int | None = None):
        if not level:
            level = logging.DEBUG

        self.logger = setup_logger(name="Tube8 API - [Amateur]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)

    @property
    def soup(self) -> BeautifulSoup:
        if not self._soup:
            raise ValueError("You probably forgot to call init")

        return self._soup

    async def init(self):
        self.html_content = await get_html_content(core=self.core, url=self.url)

        assert isinstance(self.html_content, str)
        self._soup = BeautifulSoup(self.html_content, parser)
        return self

    @cached_property
    def name(self) -> str:
        try:
            return self.soup.find("h1", class_="name-title").text

        except AttributeError:
            return re.findall(r'username: "(.*?)"', self.html_content)[1]

    @cached_property
    def rank(self) -> str:
        return self.soup.find_all("p", class_="info-stat-data")[0].text

    @cached_property
    def subscribers_count(self) -> str:
        return self.soup.find_all("p", class_="info-stat-data")[2].text

    @cached_property
    def views(self) -> str:
        return self.soup.find_all("p", class_="info-stat-data")[1].text


    async def get_videos(self, pages: int = 2,
                         videos_concurrency: int | None = None,
                         pages_concurrency: int | None = None,
                         on_video_error: on_error_hint = on_error,
                         on_page_error: on_error_hint = None
                         ) -> AsyncGenerator[Video, None]:

        page_urls = [f"{self.url}?page={page}" for page in range(1, pages + 1)]
        videos_concurrency = videos_concurrency or self.core.configuration.videos_concurrency
        pages_concurrency = pages_concurrency or self.core.configuration.pages_concurrency

        assert videos_concurrency and pages_concurrency
        async for video in self.iterator(target_page_urls=page_urls, max_video_concurrency=videos_concurrency,
                                         max_page_concurrency=pages_concurrency, video_link_extractor=extractor_html,
                                         on_video_error=on_video_error,
                                         on_page_error=on_page_error):
            yield video


class Pornstar(UserHelper):
    @cached_property
    def pornstar_information(self) -> dict:
        thing = {}
        keys = self.soup.find_all("p", class_="info-stat-label")
        values = self.soup.find_all("p", class_="info-stat-data")

        for key, value in zip(keys, values):
            thing.update({key.text: value.text})

        return thing


class Amateur(UserHelper):
    pass


class Channel(UserHelper):
    def __init__(self, url: str, core: BaseCore):
        super().__init__(core=core, url=url)
        self.core = core
        self.url = url
        self._soup = None
        self.html_content = None
        self.logger = setup_logger(name="Tube8 API - [Channel]", log_file=None, level=logging.ERROR)

    def enable_logging(self, log_file: str | None = None, level: int | None = None, log_ip: str | None = None,
                       log_port: int | None = None):
        if not level:
            level = logging.DEBUG

        self.logger = setup_logger(name="Tube8 API - [Channel]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)

    @property
    def soup(self) -> BeautifulSoup:
        if not self._soup:
            raise ValueError("You probably forgot to call init")

        return self._soup


    async def init(self):
        if not self.html_content:
            self.html_content = await get_html_content(core=self.core, url=self.url)

        assert isinstance(self.html_content, str)
        self._soup = BeautifulSoup(self.html_content, parser)
        return self


    async def get_videos(self, pages: int = 2,
                     videos_concurrency: int | None = None,
                     pages_concurrency: int | None = None,
                     on_video_error: on_error_hint = on_error,
                     on_page_error: on_error_hint = None
                     ) -> AsyncGenerator[Video, None]:

        page_urls = [f"{self.url}?page={page}" for page in range(1, pages + 1)]
        videos_concurrency = videos_concurrency or self.core.configuration.videos_concurrency
        pages_concurrency = pages_concurrency or self.core.configuration.pages_concurrency
        assert videos_concurrency and pages_concurrency
        async for video in self.iterator(target_page_urls=page_urls, max_video_concurrency=videos_concurrency,
                                         max_page_concurrency=pages_concurrency, video_link_extractor=extractor_html,
                                         on_video_error=on_video_error,
                                         on_page_error=on_page_error):
            yield video


class Client(Helper):
    def __init__(self, core: BaseCore = BaseCore()):
        super().__init__(core=core, video_constructor=Video)
        self.core = core or BaseCore()
        self.core.initialize_session()
        assert isinstance(self.core.session, AsyncSession)
        self.core.session.headers.update(HEADERS)
        self.core.session.cookies.update(COOKIES)
        self.logger = setup_logger(name="Tube8 API - [Client]", log_file=None, level=logging.ERROR)


    def enable_logging(self, log_file: str | None = None, level: int | None =None, log_ip: str | None = None, log_port: int | None = None):
        if not level:
            level = logging.DEBUG

        self.logger = setup_logger(name="Tube8 API - [Client]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)


    async def get_video(self, url: str) -> Video:
        video = Video(core=self.core, url=url)
        return await video.init()

    async def get_pornstar(self, url: str) -> Pornstar:
        pornstar = Pornstar(core=self.core, url=url)
        return await pornstar.init()

    async def get_channel(self, url: str) -> Channel:
        channel = Channel(core=self.core, url=url)
        return await channel.init()

    async def get_amateur(self, url: str) -> Amateur:
        amateur = Amateur(core=self.core, url=url)
        return await amateur.init()

    async def search(self, query: str, pages: int = 2,
                     videos_concurrency: int | None = None,
                     pages_concurrency: int | None = None,
                     on_video_error: on_error_hint = on_error,
                     on_page_error: on_error_hint = None
                     ) -> AsyncGenerator[Video, None]:
        # I am too lazy to implement search filters
        page_urls = [f"https://tube8.com/searches.html/?q={query}&page={page}" for page in range(1, pages + 1)]
        videos_concurrency = videos_concurrency or self.core.configuration.videos_concurrency
        pages_concurrency = pages_concurrency or self.core.configuration.pages_concurrency
        assert videos_concurrency and pages_concurrency

        async for video in self.iterator(target_page_urls=page_urls, max_video_concurrency=videos_concurrency,
                                         max_page_concurrency=pages_concurrency, video_link_extractor=extractor_search,
                                         on_video_error=on_video_error,
                                         on_page_error=on_page_error):
            yield video
