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

from .config import Config, parse_args
from .feeds import process_feeds

from python_feed_lib import with_session

def main(args: list[str]) -> None:
    """The main function."""
    syslog.openlog(ident="NprPodcastDownloader", facility=syslog.LOG_NEWS)
    try:
        conf: Config = parse_args(args)
        with with_session(
                referer="https://www.npr.org",
                user_agent=conf.user_agent,
                proxy=conf.proxy,
        ) as session:
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
