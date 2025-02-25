#! /usr/bin/python3

"""
Work with feeds.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Iterable
from xml.dom.minidom import Document, Element,  parseString
import re
import syslog

import bs4
import requests


def process_feeds(urls: list[str], sess: requests.Session) -> Document:
    """Download and combine the feeds."""
    main: Document = convert_feed(get_feed(urls[0], sess))
    if len(urls) == 1: # No need to combine
        enrich_articles(main, sess, main)
        return main
    # This is done in serial
    feeds: Iterable[Document] = (get_feed(url, sess) for url in urls[1:])
    for feed in feeds:
        join_feeds(main, feed)
    sort_elements(main)
    enrich_articles(main, sess, main)
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

def get_feed(url: str, sess: requests.Session) -> Document:
    """Download and parse the feed."""
    try:
        res = sess.get(url)
        res.raise_for_status()
        return parseString(res.text)
    except requests.HTTPError as err:
        raise RuntimeError(f"Unable to download feed: {err}") from err
    except BaseException as err:
        raise RuntimeError(f"Unable to parse feed: {err}") from err


def convert_feed(feed: Document) -> Document:
    """Convert the feed from an RSS feed to an Atom feed."""
    doc: Document = parseString("""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"/>""")
    root: Element = doc.documentElement
    if (channel := get_single_element("channel", feed)) is None:
        raise RuntimeError("Unable to get channel information from RSS feed")
    # Get the feed attributes
    if (title := get_single_element("title", channel)) is not None:
        root.appendChild(title)
    # for link in channel.getElementsByTagName("link"):
    #     _l = doc.createElement("link")
    #     _l.setAttribute("href", get_string(link))
    #     root.appendChild(_l)
    if (copy_right := get_single_element("copyright", channel)) is not None:
        root.appendChild(create_text_node("rights", get_string(copy_right), doc))
    if (desc := get_single_element("description", channel)) is not None:
        root.appendChild(create_text_node("subtitle", get_string(desc), doc))
    if (generator := get_single_element("generator", channel)) is not None:
        root.appendChild(generator)
    root.appendChild(create_text_node(
        "updated",
        get_string(last_build_date) if (last_build_date := get_single_element("lastBuildDate", channel)) \
        is not None else datetime.now().isoformat(),
        doc,
    ))
    if (image := get_single_element("image", channel)) is not None \
       and (image := get_single_element("url", image)) is not None:
        root.appendChild(create_text_node("logo", get_string(image), doc))
    # Get the articles
    for element in feed.getElementsByTagName("item"):
        root.appendChild(convert_element(element, doc))
    return doc

def sort_elements(feed: Document) -> None:
    """Sort the <entry> elements by date/time.
    Modification is done in-place.
    """
    def get_date(e: Element) -> datetime:
        updated: list[Element] = e.getElementsByTagName("updated")
        if len(updated) != 1:
            raise RuntimeError("Invalid number of updated tags")
        return " ".join(node.nodeValue for node in updated[0].childNodes if node.nodeType == node.TEXT_NODE)
    elements: list[Element] = feed.documentElement.getElementsByTagName("entry")
    for element in elements:
        feed.documentElement.removeChild(element)
    for element in sorted(elements, key=get_date):
        feed.documentElement.appendChild(element)

def convert_element(original: Element, doc: Document) -> Element:
    """Convert an RSS item from RSS to an Atom entry."""
    new = doc.createElement("entry")
    if (title := get_single_element("title", original)) is not None:
        new.appendChild(title)
    else:
        raise RuntimeError("The element has no title")
    if (guid := get_single_element("guid", original)) is not None:
        new.appendChild(create_text_node("id", get_string(guid), doc))
    else:
        raise RuntimeError("The element is missing its guid")
    if (pubdate := get_single_element("pubDate", original)) is not None:
        new.appendChild(create_text_node("updated", get_string(pubdate), doc))
    else:
        raise RuntimeError("While pubDate is optional in RSS, updated is mandatory in Atom")
    if (link := get_single_element("link", original)) is not None:
        _l = doc.createElement("link")
        _l.setAttribute("href", get_string(link))
        new.appendChild(_l)
    if (desc := get_single_element("description", original)) is not None:
        desc.tagName = "summary"
        new.appendChild(desc)
    return new

def get_string(e: Element) -> str:
    """Get an element's contents."""
    return " ".join(_e.nodeValue for _e in e.childNodes if _e.nodeType == e.TEXT_NODE)

def create_text_node(tag: str, val: str, doc: Document, attr: dict[str, str]|None = None) -> Element:
    """Create a text element."""
    element = doc.createElement(tag)
    element.appendChild(doc.createTextNode(val))
    if attr is not None:
        for key, val in attr.items():
            element.setAttribute(key, val)
    return element

def get_single_element(tag: str, node: Element|Document) -> Element|None:
    """Get a single element of type <tag> from the children of node."""
    nodes = node.getElementsByTagName(tag)
    return None if len(nodes) == 0 else nodes[0]

def get_article(
        element: Element,
        session: requests.Session
) -> tuple[str, bs4.BeautifulSoup, Element]|Element:
    """Download the article and extract the media URL and text content.
    Returns the associated element for easier processing later.
    If only the element is returned, then the fetch failed, and the element may be discarded.
    """
    try:
        if (link_node := get_single_element("link", element)) is None:
            syslog.syslog(syslog.LOG_INFO, "Unable to find a link for the entry")
            return element
        if not (link := link_node.getAttribute("href")):
            syslog.syslog(syslog.LOG_INFO, "The link does not contain an href attribute")
            return element
        res = session.get(link)
        res.raise_for_status()
        body = bs4.BeautifulSoup(res.text, "lxml")
        url_node = body.find(lambda x: x.has_attr("href"), class_="audio-module-listen")
        if not isinstance(url_node, bs4.Tag) or not isinstance(url := url_node.attrs.get("href"), str):
            syslog.syslog(syslog.LOG_INFO, f"Unable to extract media url from article at {link}")
            return element
        url = re.sub(r"\?.*?$", "", url)
        # TODO: This removal of script tags is in case this is ever included in the <content> of the entry
        # As of now, it doesn't do anything useful
        # for script in body.find_all("script"): # Remove script tags
        #     script.destroy()
        return (url, body, element)
    except BaseException as err:
        syslog.syslog(syslog.LOG_ERR, f"Error while fetching entry media: {err}")
        return element

def enrich_article(article: Element, media: str|None, body: bs4.BeautifulSoup, doc: Document):
    """Enrich the article contents."""
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
            syslog.syslog(syslog.LOG_DEBUG, f"The media link is not to an mp3: {media}")
        article.appendChild(enclosure)
    # TODO: Append the text somehow?

def enrich_articles(feed: Document|Element, sess: requests.Session, doc: Document, max_workers: int = 3):
    """Get the article body and (if possible) media URL for each element.
    The body and media URL will be added to the element in-place.
    """
    with ThreadPoolExecutor(max_workers = max_workers) as pool:
        futures = [pool.submit(get_article, entry, sess) for entry in feed.getElementsByTagName("entry")]
    for future in futures:
        result = future.result()
        if isinstance(result, Element):
            syslog.syslog(syslog.LOG_INFO, "Removing entry from feed")
            result.parentNode.removeChild(result)
            continue
        media_url, body, entry = result
        # The Python documentation does not mention minidom being thread-safe,
        # so update this in serial
        enrich_article(entry, media_url, body, doc)
