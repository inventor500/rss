#! /usr/bin/python3

from enum import Enum, auto
from typing import Iterable
from xml.etree import ElementTree
import sys
from os import path

def main(args: list[str]) -> None:
    """The main function."""
    if len(args) <= 2:
        print(f"Usage: {args[0]} "
              "{<filename>|-]} {<category1> ... <categoryn>}\n\"-\" "
              "will read from standard in", file=sys.stderr)
        sys.exit(1)
    feed: ElementTree.ElementTree
    if args[1] == "-": # Read from stdin
        feed = ElementTree.parse(sys.stdin)
    else: # Read from file
        with open(path.expandvars(path.expanduser(args[1]))) as opened:
            feed = ElementTree.parse(opened)
    categories = args[2:]
    remove_matching_articles(categories, feed)
    feed.write(sys.stdout, encoding="unicode")

class ArticleType(Enum):
    """Supported feed types."""
    RSS0 = auto()
    RSS2 = auto()
    ATOM = auto()

def get_article_categories(article: ElementTree.Element, a_type: ArticleType) -> list[str]:
    """Get the categories of an article."""
    categories = article.findall("category") # Atom and RSS both use the <category> tag
    if a_type == ArticleType.ATOM: # Atom feed
        # Contained in the term attribute
        return [c.attrib["term"] for c in categories if "term" in c.attrib] 
    else: # RSS feed
        # Contained in the text element
        return [c.text for c in categories if c.text is not None and c.text != ""]

def get_feed_type(feed: ElementTree.ElementTree) -> ArticleType:
    """Get the type of the feed."""
    root = feed.getroot()
    if root.tag.lower() == "feed":
        return ArticleType.ATOM
    elif "version" in root.attrib and root.attrib["version"] == "2.0":
        return ArticleType.RSS2
    return ArticleType.RSS0


def get_articles(root: ElementTree.Element, feed_type: ArticleType) -> Iterable[ElementTree.Element]:
    """Get the articles from a feed."""
    # <entry> for Atom, <item> for RSS
    if feed_type == ArticleType.ATOM:
        return root.findall("entry")
    return root.findall("item")


def get_root(feed: ElementTree.ElementTree, feed_type: ArticleType) -> ElementTree.Element|None:
    """Get the root element."""
    if feed_type == ArticleType.ATOM:
        return feed.getroot()
    # Articles in RSS are inside of the "channel" element
    root = feed.getroot()
    return root.find("channel")


def article_matches_p(article: ElementTree.Element, categories: list[str], a_type: ArticleType) -> bool:
    """Test if the article matches any of the categories."""
    a_cat = get_article_categories(article, a_type)
    for category in categories:
        for cat in a_cat:
            if category.lower() in cat.lower():
                return True
    return False

def remove_matching_articles(categories: list[str], feed: ElementTree.ElementTree):
    """Remove articles with a matching category."""
    feed_type = get_feed_type(feed)
    root = get_root(feed, feed_type)
    if root is None: # No articles
        return
    to_remove: list[ElementTree.Element] = [
        a for a in get_articles(root, feed_type) if article_matches_p(a, categories, feed_type)
    ]
    for article in to_remove:
        root.remove(article)


if __name__=="__main__":
    main(sys.argv)
