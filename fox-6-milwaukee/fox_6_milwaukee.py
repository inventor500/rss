#! /usr/bin/env python3

"""
Downloads and enriches the news feed for Fox6 Milwaukee.
This feed contains local news for Milwaukee, WI.
"""

from dataclasses import dataclass
from html import escape
from sys import argv, exit
from xml.dom.minidom import parseString, Document, Element
from xml.parsers.expat import ExpatError
import argparse
import json
import logging

from bs4 import BeautifulSoup, Tag
from bs4.formatter import XMLFormatter
from requests import Session
from requests.exceptions import HTTPError

from python_feed_lib import with_session, convert_feed, get_user_agent, setup_logging, enrich_articles, get_entry_link, cleanup_html

# URL of the feed to download from
# TODO: Expand this to include other things?
FEED_URL: str = "https://www.fox6now.com/rss/category/news"
Logger: logging.Logger

def main(args: list[str]) -> None:
    """The main function."""
    global Logger
    conf = parse_args(args)
    Logger = setup_logging("Fox6Downloader")
    with with_session("https://www.fox6now.com", conf.user_agent, conf.proxy) as sess:
        try:
            feed: Document = get_feed(FEED_URL, sess)
            enrich_articles(feed, get_article, update_article, sess)
            print(feed.toxml())
        except HTTPError as err:
            Logger.fatal("Unable to download base feed: %s", err)
            exit(1)
        except RuntimeError as err:
            Logger.fatal("Error processing feed: %s", err)
            exit(1)


@dataclass
class Config:
    user_agent: str
    proxy: str|None

def parse_args(argv: list[str]) -> Config:
    """Parse arguments."""
    assert len(argv) >= 1
    parser = argparse.ArgumentParser(prog=argv[0])
    parser.add_argument("-p", "--proxy", type=str, default=None, help="Proxy URL to use", required=False, dest="proxy")
    parser.add_argument("-u", "--user-agent", type=str, default=None, help="User agent to use for HTTP(s) requests", dest="user_agent")
    parsed = parser.parse_args(argv[1:])
    if "user_agent" in vars(parsed) and parsed.user_agent is not None:
        user_agent = parsed.user_agent
    else:
        user_agent = get_user_agent()
    if "proxy" in vars(parsed) and parsed.proxy is not None:
        proxy = parsed.proxy
    else:
        proxy = None
    return Config(
        user_agent = user_agent,
        proxy = proxy,
    )

def get_feed(url: str, sess: Session) -> Document:
    """Download the base feed."""
    res = sess.get(url)
    res.raise_for_status()
    parsed: Document = parseString(res.text)
    if parsed.documentElement.tagName.lower() == "rss":
        return convert_feed(parsed)
    return parsed

def remove_signup_links(article: Tag) -> None:
    """Remove the newsletter links from an article.
    Changes are done in-place.
    """
    for ad in article.find_all("a", attrs={"href": "https://www.fox6now.com/newsletters"}):
        if ad is not None and ad.parent is not None:
            ad.parent.decompose()

def get_article(
        entry: Element,
        sess: Session
) -> tuple[Element, tuple[Tag|None, str|None]]|Element:
    """Get the article contents. Returns (received_entry, (article_body, video_url))|received_entry.
    Intended to be called by enrich_articles in concert with update_article.
    """
    try:
        link = get_entry_link(entry)
        res = sess.get(link)
        res.raise_for_status()
        article = BeautifulSoup(res.text, "lxml")
        content = article.find(class_="article-content")
        if content is not None: # Article has content
            assert isinstance(content, Tag)
            cleanup_html(content)
            remove_signup_links(content)
            return entry, (content, None)
        else: # Video?
            video = article.find(class_="script", attrs={"type": "application/ld+json"})
            if video is None: # No video
                return entry
            assert isinstance(content, Tag)
            js: dict[str, str|dict] = json.parse(video.get_text())
            if "contentUrl" not in js or not isinstance(js["contentUrl"], str):
                Logger.info("Could not extract video URL from metadata element")
                return entry
            url = js["contentUrl"]
            # TODO: Do any of these have article contents?
            # If not, then the touple return type is useless
            return entry, (None, url)
    except BaseException as err:
        Logger.error("Unable to fetch article: %s", err)
        return entry

def update_article(entry: Element, contents: tuple[Tag|None, str|None], doc: Document) -> None:
    """Update the article with the received contents.
    Intended to be called by enrich_articles in concert with get_article.
    """
    content, video = contents
    if content is not None:
        cont_str = content.decode(formatter=XMLFormatter.REGISTRY["minimal"]) # Make sure this is XML
        try:
            parsed: Document = parseString(cont_str) # Probably not the most efficient way
        except ExpatError as err:
            Logger.error(
                "Unable to parse XML produced by this script: %s\nThis article will be skipped.",
                err,
            )
            return
        cont = parsed.documentElement
        container = doc.createElement("content")
        container.appendChild(cont)
        entry.appendChild(container)
    if video is not None:
        vid_element: Element = doc.createElement("link")
        vid_element.setAttribute("rel", "enclosure")
        vid_element.setAttribute("type", "application/x-mpegURL") # TODO: Is it ever anything other than this?
        vid_element.setAttribute("title", "Video")
        vid_element.setAttribute("href", escape(video))
        entry.appendChild(vid_element)


if __name__=="__main__":
    main(argv)
