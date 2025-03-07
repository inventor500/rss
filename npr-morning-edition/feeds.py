#! /usr/bin/python3

"""
Work with feeds.
"""

from typing import Iterable
from xml.dom.minidom import Document, Element,  parseString
import re
import syslog

import bs4
from requests import Session, HTTPError

from python_feed_lib import (
    cleanup_html,
    convert_element,
    convert_feed,
    enrich_articles,
    get_single_element,
    sort_elements,
)


def process_feeds(urls: list[str], sess: Session) -> Document:
    """Download and combine the feeds."""
    main: Document = convert_feed(get_feed(urls[0], sess))
    if len(urls) == 1: # No need to combine
        enrich_articles(main, get_article, enrich_article, sess)
        return main
    # This is done in serial
    feeds: Iterable[Document] = (get_feed(url, sess) for url in urls[1:])
    for feed in feeds:
        join_feeds(main, feed)
    sort_elements(main)
    enrich_articles(main, get_article, enrich_article, sess)
    return main

def join_feeds(main: Document, new: Document) -> None:
    """Join the feeds together. Modified the main feed in-place."""
    # Atom uses "<feed>", RSS uses "<rss>"
    is_atom: bool = new.documentElement.tagName == "feed"
    main_doc = main.documentElement
    for article in new.documentElement.getElementsByTagName("entry" if is_atom else "item"):
        a = article if is_atom else convert_element(article, new) # Make sure this is Atom
        main.importNode(a, deep=True)
        main_doc.appendChild(a)

def get_feed(url: str, sess: Session) -> Document:
    """Download and parse the feed."""
    try:
        res = sess.get(url)
        res.raise_for_status()
        return parseString(res.text)
    except HTTPError as err:
        raise RuntimeError(f"Unable to download feed: {err}") from err
    except BaseException as err:
        raise RuntimeError(f"Unable to parse feed: {err}") from err

def get_article(
        entry: Element,
        sess: Session,
) -> tuple[Element, tuple[bs4.Tag|None, str|None]]|Element:
    """Download the article and extract the media and text content.
    Returns the associated element for easier processing later.
    If only the element is returned, then the fetch failed and the element may be discarded.
    """
    try:
        if (link_node := get_single_element("link", entry)) is None:
            syslog.syslog(syslog.LOG_INFO, "Unable to find a link for the entry")
            return entry
        if not (link := link_node.getAttribute("href")):
            syslog.syslog(syslog.LOG_INFO, "The link does not contain an href attribute")
            return entry
        res = sess.get(link)
        res.raise_for_status()
        body = bs4.BeautifulSoup(res.text, "lxml")
        url_node = body.find(lambda x: x.has_attr("href"), class_="audio-module-listen")
        if not isinstance(url_node, bs4.Tag) or not isinstance(url := url_node.attrs.get("href"), str):
            syslog.syslog(syslog.LOG_INFO, f"Unable to extract media url from article at {link}")
            return entry
        cleanup_html(body)
        url = re.sub(r"\?.*?$", "", url)
        return entry, (body, url)
    except BaseException as err:
        syslog.syslog(syslog.LOG_ERR, f"Error while fetching entry media: {err}")
        return entry

def enrich_article(entry: Element, contents: tuple[bs4.Tag|None, str|None], doc: Document) -> None:
    """Enrich the article contents."""
    body, media = contents
    if media is not None:
        enclosure = doc.createElement("link")
        for key, val in {
                "rel": "enclosure",
                "href": media,
        }.items():
            enclosure.setAttribute(key, val)
        # RSS Guard seems to assume that untyped links are jpegs
        if media.endswith(".mp3"):
            enclosure.setAttribute("type", "audio/mpeg")
        else:
            syslog.syslog(syslog.LOG_DEBUG, f"The media link is not an mp3: {media}")
        entry.appendChild(enclosure)
    # TODO: Append the text?
