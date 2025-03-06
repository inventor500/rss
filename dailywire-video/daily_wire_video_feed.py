#! /usr/bin/python3

"""
Download a show from the Daily Wire and convert it into an Atom podcast feed.
This will only work with releases that do not require a payed subscription.
This script can be put in any feed reader that supports calling an external
script, e.g. Newsboat or RSS Guard.

The feed name is derived from the URL, e.g.
"www.dailywire.com/show/the-ben-shapiro-show" -> "The Ben Shapiro Show"
Names have spaces replaced with "-" and are downcased during processing,
so "the-ben-shapiro-show" and "The Ben Shapiro Show" are equivalent.

Example usage:
daily_wire_video_feed.py "The Ben Shapiro Show"

Requirements:
Depends on the "requests" library.
Due to the use of Python's "syslog" library, this will only work on UNIX-like
systems, e.g. Mac OS and Linux.
Due to the use of the "walrus operator" (:=), this requires at least Python 3.8.
Code has only been tested on Python 3.13 (as of Feb. 2025).
"""

## Imports

from atexit import register as atexit
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import escape
from os import path
from sys import argv, stderr, exit as sysexit
from traceback import extract_tb
from typing import Any
from urllib import parse as urlparse
from xml.dom.minidom import Document, Element, parseString as parseXML
import json
import os
import re
import syslog

import requests as req


## Main function

def main(args: list[str]) -> None:
    """The main function."""
    if len(args) != 2 or args[1] == "--help" or args[1] == "-h":
        print(
            f"Usage: {argv[0]} "
            "{name}\nExample: "
            f"{argv[0]} 'Ben After Dark'",
            file=stderr)
        sysexit(1)
    syslog.openlog(ident="DailyWireVideo", facility=syslog.LOG_NEWS)
    atexit(syslog.closelog)
    try:
        videos = get_videos(args[1])
        feed = create_feed(args[1], videos)
        print(feed.toxml())
    except RuntimeError as err:
        syslog.syslog(f"Unable to download: {err}\n{'\n'.join(extract_tb(err.__traceback__).format())}")
        print(f"Unable to download: {err}", file=stderr)
        exit(1)


## XML/Feed Functions

class VideoElement:
    """A video in the main feed."""
    icon_url: str|None
    article_url: str
    title: str
    published: str
    description: str|None
    slug: str|None
    video_url: str|None = None
    _id: str|None = None
    # TODO: Add author?

    def __init__(
            self,
            icon_url: str|None,
            article_url: str,
            title: str,
            published: str,
            description: str|None,
            slug: str|None,
            _id: str|None = None,
    ):
        self.icon_url = icon_url
        self.article_url = article_url
        self.title = title
        self.published = published
        self.description = description
        self.slug = slug
        self._id = _id

    def to_xml(self, doc: Document) -> Element:
        """Create an XML element."""
        entry = doc.createElement("entry")
        entry.appendChild(create_text_element("title", escape(self.title), doc))
        entry.appendChild(create_link_element("link", self.article_url, doc))
        _id = self._id if self._id is not None else self.article_url
        entry.appendChild(create_text_element("id", escape(_id), doc))
        entry.appendChild(create_text_element("updated", self.published, doc))
        if self.description is not None:
            entry.appendChild(create_text_element("summary", escape(self.description), doc))
        if self.video_url is not None:
            download_link = create_link_element("link", escape(self.video_url), doc)
            download_link.setAttribute("rel", "enclosure")
            download_link.setAttribute("type", "application/x-mpegURL")
            download_link.setAttribute("title", "Video")
            entry.appendChild(download_link)
        return entry

    def __str__(self):
        return f"VideoElement: ['{self.title}': hasVideo: {self.video_url is not None}]"

    __repr__ = __str__

def create_feed(title: str, videos: list[VideoElement]) -> Document:
    """Create a feed."""
    doc: Document = parseXML("""<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"></feed>""")
    root = doc.documentElement
    root.appendChild(create_text_element("title", title, doc))
    root.appendChild(create_text_element("id", root_url(title), doc))
    root.appendChild(create_text_element(
        "updated",
        datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        doc,
    ))
    root.appendChild(create_text_element("generator", argv[0], doc))
    root.appendChild(
        create_text_element("icon", "https://www.dailywire.com/favicons/apple-touch-icon-57x57.png", doc)
    )
    for video in videos:
        root.appendChild(video.to_xml(doc))
    return doc

def create_text_element(tag: str, contents: str, doc: Document) -> Element:
    """Create a text element."""
    element = doc.createElement(tag)
    element.appendChild(doc.createTextNode(contents))
    return element

def create_link_element(tag: str, href: str, doc: Document, text: str|None = None) -> Element:
    """Create a link.
    If text is not provided, then no text element will be created.
    """
    element = doc.createElement(tag) if text is None else create_text_element(tag, text, doc)
    element.setAttribute("href", href)
    return element

def create_video(element: dict[str, Any]) -> VideoElement|None:
    """Create a video element.
    Returns None if unable to parse.
    """
    if "showEpisode" not in element:
        syslog.syslog(syslog.LOG_INFO, "showEpisode is missing from episode description")
        return None
    episode: dict[str, Any] = element["showEpisode"]
    slug: str|None = None
    if "slug" not in episode:
        syslog.syslog(syslog.LOG_INFO, "id is not provided in episode")
    else:
        slug = episode["slug"]
    description = episode["description"] if "description" in episode else None
    # This is mandatory in ATOM
    published: str = ""
    if "publishedAt" in episode:
        published = episode["publishedAt"]
    elif "scheduledAt" in episode:
        published = episode["scheduledAt"]
    # Title is mandatory in ATOM
    title = episode["title"] if "title" in episode else ""
    # URL (<link>) is mandatory in ATOM
    article_url = episode["sharingURL"] if "sharingURL" in episode else ""
    icon_url = None
    if "images" in episode and "thumbnail" in episode["images"] \
       and "land" in episode["images"]["thumbnail"] \
       and isinstance(episode["images"]["thumbnail"]["land"], str):
        icon_url = episode["images"]["thumbnail"]["land"]
    e_id = episode["id"] if "id" in episode else None
    return VideoElement(
        slug = slug,
        icon_url = icon_url,
        article_url = article_url,
        title = title,
        published = published,
        description = description,
        _id = e_id,
    )


## Download Functions

def get_video_url(article: VideoElement, buildid: str) -> str:
    """Get the URL of the video corresponding to the element.
    Raises a RuntimeError if unable to get the video URL.
    """
    assert article.slug is not None
    url = path.join("https://www.dailywire.com/_next/data/", buildid, f"episode/{article.slug}.json")
    res = req.get(url, headers=Headers)
    if res.status_code != 200:
        raise RuntimeError(f"Unable to download episode data: received status code {res.status_code}")
    js: dict[str, Any] = {}
    try:
        js = res.json()
    except json.JSONDecodeError as err:
        raise RuntimeError(f"Failed to decode episode JSON data: {err}") from err
    if "pageProps" not in js \
       or "v4EpisodeData" not in (cmap := js["pageProps"]) \
       or "videoURL" not in (cmap := cmap["v4EpisodeData"]):
        raise RuntimeError("Unable to extract video url from episode data")
    # TODO: This link is not stable, the token eventually expires
    assert isinstance(cmap["videoURL"], str)
    assert cmap["videoURL"].startswith("http")
    return cmap["videoURL"]

def root_url(series_name: str) -> str:
    """Convert a series name into a url."""
    root: str = "https://www.dailywire.com/show/"
    return path.join(root, urlparse.quote(series_name.replace(' ', '-')))

def get_user_agent() -> str:
    """Get the user agent to use."""
    if (env := os.getenv("RSS_USER_AGENT")) is not None:
        return env
    if (env := os.getenv("USER_AGENT")) is not None:
        return env
    return "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"

Headers: dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "User-Agent": get_user_agent(),
    "Sec-GPC": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Origin": "https://dailywire.com",
}

def get_build_id(show_url: str) -> str:
    """Get the build id."""
    res = req.get(show_url, headers = Headers)
    if res.status_code != 200:
        raise RuntimeError(f"Unable to get the build id: Received status code {res.status_code}")
    getter = re.compile(r'"buildId": ?"(.*?)"')
    _match = getter.search(res.text)
    if _match is None or len(_match.groups()) < 1:
        raise RuntimeError("Unable to find build id in page")
    return _match.groups()[0]

def get_videos(series_name: str) -> list[VideoElement]:
    """Download the main page for the video."""
    params = {
        "slug": series_name.replace(' ', '-').lower(),
        "membershipPlan": None
    }
    res = req.get("https://middleware-prod.dailywire.com/middleware/v4/getShowEpisodesWeb", params=params, headers=Headers)
    if res.status_code != 200:
        raise RuntimeError(f"Unable to download episode list: Received code {res.status_code}")
    try:
        js = res.json()
    except json.JSONDecodeError as err:
        raise RuntimeError("Unable to download: Unable to parse JSON response") from err
    if "componentItems" not in js:
        raise RuntimeError("Invalid episode list: Missing componentItems element")
    if not isinstance(js["componentItems"], list):
        raise RuntimeError("Invalid episode list: componentItems is not a List")
    build_id = get_build_id(f"https://www.dailywire.com/show/{params['slug']}")
    def process_video(item: dict[str, Any]) -> VideoElement|None:
        """Process a video."""
        parsed = create_video(item)
        if parsed is None or parsed.slug is None:
            return None
        try:
            parsed.video_url = get_video_url(parsed, build_id)
            if parsed.video_url.lower() == "access denied":
                return None
        except RuntimeError as err:
            syslog.syslog(syslog.LOG_INFO, str(err))
            return None
        return parsed
    with ThreadPoolExecutor(max_workers=3) as exec:
        results = [exec.submit(process_video, item) for item in js["componentItems"]]
        return [res for res in (_r.result() for _r in results) if res is not None]


## Driver

if __name__ == '__main__':
    main(argv)
