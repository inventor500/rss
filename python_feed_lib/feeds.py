#! /usr/bin/python3

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from os import getenv
from typing import Callable
from xml.dom.minidom import Document, Element, parseString
import logging

from bs4 import Tag, Comment
from requests import Session

## Globals

Logger = logging.getLogger(__name__)

## Networking

DEFAULT_USER_AGENT: str = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"

@contextmanager
def with_session(referer: str|None = None, user_agent: str|None = None, proxy: str|None = None):
    """Create a session.
    Creates a requests.Session with specified settings.
    """
    try:
        with Session() as sess:
            # Set the default headers to send
            sess.headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-GPC": "1", # Enable GPC
                "User-Agent": user_agent if user_agent is not None else DEFAULT_USER_AGENT
            })
            # Set the referer string
            if referer is not None:
                sess.headers.update({
                    "Referer": referer,
                })
            # Set the default proxy settings
            if proxy is not None:
                sess.proxies.update({
                    "http": proxy,
                    "https": proxy,
                })
            yield sess
    finally:
        pass

def enrich_articles[T](
        feed: Document|Element,
        getter: Callable[[Element, Session], tuple[Element, T]|Element],
        setter: Callable[[Element, T, Document], None],
        sess: Session,
        doc: Document|None = None,
        *,
        max_workers: int = 3,
        logger: logging.Logger = Logger,
):
    """Get the article body and (if possible) media URL for each element.
    
    Calls getter to fetch the article. If getter returns only the element, then it is assumed to have
    failed, and the article will be removed from the feed.
    Otherwise, setter is called to update the element in-place.

    logger: The logger to use. This allows for a different logger to be used than this module's default.
    """
    if doc is None:
        if isinstance(feed, Element) and isinstance(feed.ownerDocument, Document):
            doc = feed.ownerDocument
        elif isinstance(feed, Document):
            doc = feed
        else:
            raise RuntimeError("Unable to infer feed document! An actual XML document must somehow be previded to this function!")
    assert isinstance(doc, Document)
    with ThreadPoolExecutor(max_workers = max_workers) as pool:
        futures = [pool.submit(getter, entry, sess) for entry in feed.getElementsByTagName("entry")]
    for future in futures:
        result = future.result()
        if isinstance(result, Element): # The article was not able to be downloaded
            logger.info("Removing entry from feed")
            result.parentNode.removeChild(result)
            continue
        entry, res = result
        # The Python documentation does not mention minidom being thread-safe,
        # so update this in serial
        setter(entry, res, doc)

def get_user_agent() -> str:
    """Get the default user agent."""
    if (user_agent:= getenv("RSS_USER_AGENT")) is not None:
        return user_agent
    if (user_agent := getenv("USER_AGENT")) is not None:
        return user_agent
    return DEFAULT_USER_AGENT


## Conversion

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

def sort_elements(feed: Document) -> None:
    """Sort the <entry> elements by date/time.
    Modification is done in-place.
    """
    def get_date(e: Element) -> str:
        updated: list[Element] = e.getElementsByTagName("updated")
        if len(updated) != 1:
            raise RuntimeError("Invalid number of updated tags")
        return " ".join(node.nodeValue for node in updated[0].childNodes if node.nodeType == node.TEXT_NODE)
    elements: list[Element] = feed.documentElement.getElementsByTagName("entry")
    for element in elements:
        feed.documentElement.removeChild(element)
    for element in sorted(elements, key=get_date):
        feed.documentElement.appendChild(element)

def cleanup_html(content: Tag) -> None:
    """Cleanup HTML content in-place.
    This entails removing scripts, comments, etc.
    """
    for script in content.find_all("script"):
        if script is not None:
            script.decompose()
    for comment in content.find_all(lambda x: isinstance(x, Comment)):
        assert isinstance(comment, Comment)
        if comment.parent is not None:
            comment.parent.decompose()

## Getters

def get_single_element(tag: str, node: Element|Document) -> Element|None:
    """Get a single element of type <tag> from the children of node."""
    nodes = node.getElementsByTagName(tag)
    return None if len(nodes) == 0 else nodes[0]

def get_string(e: Element) -> str:
    """Get an element's contents."""
    return " ".join(_e.nodeValue for _e in e.childNodes if _e.nodeType == e.TEXT_NODE)

def get_entry_link(e: Element) -> str:
    """Get the Atom feed's link."""
    if (link_node := get_single_element("link", e)) is None:
        raise RuntimeError("Unable to find a link for the entry: No <link> element was found.")
    if not (link := link_node.getAttribute("href")):
        raise RuntimeError("The link does not contain an href attribute")
    return link

## Element Creation

def create_text_node(tag: str, val: str, doc: Document, attr: dict[str, str]|None = None) -> Element:
    """Create a text element."""
    element = doc.createElement(tag)
    element.appendChild(doc.createTextNode(val))
    if attr is not None:
        for key, val in attr.items():
            element.setAttribute(key, val)
    return element
