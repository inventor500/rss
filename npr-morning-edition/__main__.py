#! /usr/bin/python3

"""
NPR does not put the URL of the audio in the RSS feed.

Usage:
python npr_podcast_downloader.py [--proxy <proxy>] [url]

Requirements:
Depends on the requests and beautiful soup 4 libraries.
Depends on lxml (for use by beautiful soup).
Requires a UNIX-like system due to use of Python's syslog library.
Due to the use of the "walrus operator" (:=), this requires at least Python 3.8.
Code has only been tested on Python 3.13 (as of Feb. 2025).
"""

from sys import argv, stderr, exit
from traceback import extract_tb
import syslog

from requests import Session

from .config import Config, parse_args
from .feeds import process_feeds

def main(args: list[str]) -> None:
    """The main function."""
    syslog.openlog(ident="NprPodcastDownloader", facility=syslog.LOG_NEWS)
    try:
        with Session() as session:
            conf: Config = parse_args(args)
            # Set the default headers
            session.headers.update({
                "User-Agent": conf.user_agent,
                "Referer": "https://www.npr.org",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-GPC": "1",
            })
            # Set the proxy
            if conf.proxy is not None:
                session.proxies.update({
                    "http": conf.proxy,
                    "https": conf.proxy,
                })
            # Download and convert the feed
            feed = process_feeds(conf.urls, session)
            print(feed.toprettyxml())
    except BaseException as err:
        print(f"Unable to download: {err}", file=stderr)
        syslog.syslog(
            syslog.LOG_ERR,
            f"Unable to download: {err}\n{'\n'.join(extract_tb(err.__traceback__).format())}",
        )
        exit(1)

## Start the main function
main(argv)
