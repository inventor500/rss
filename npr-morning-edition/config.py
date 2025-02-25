#! /usr/bin/python3

"""
Parse arguments.
"""

from argparse import ArgumentParser
from dataclasses import dataclass
from os import getenv

# Default values
USER_AGENT: str = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"

def get_user_agent() -> str:
    """Get the user agent to use."""
    if (env := getenv("RSS_USER_AGENT")) is not None:
        return env
    if (env := getenv("USER_AGENT")) is not None:
        return env
    return USER_AGENT

@dataclass
class Config:
    urls: list[str]
    proxy: str|None = None
    user_agent: str = get_user_agent()

def parse_args(args: list[str]) -> Config:
    """Parse arguments."""
    parser = ArgumentParser(prog="npr_podcast_downloader", description="Downloads NPR podcasts.")
    parser.add_argument("-p", "--proxy", type=str, default=None, help="Proxy URL", required=False, dest="proxy")
    parser.add_argument("-u", "--user-agent", type=str, default=None, help="User agent to use", required=False, dest="user_agent")
    parser.add_argument("urls", type=str, nargs="*", help="Podcast URL")
    parsed = parser.parse_args(args[1:])
    if len(parsed.urls) < 1:
        parser.print_usage()
        raise RuntimeError("At least one URL must be specified!")
    return Config(
        proxy=parsed.proxy,
        # TODO: Change this after coding for combining feeds
        urls=parsed.urls,
        user_agent=parsed.user_agent if parsed.user_agent is not None else get_user_agent()
    )
