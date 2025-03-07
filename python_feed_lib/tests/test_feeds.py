#! /usr/bin/python3

from os import environ
import unittest

import requests

from .. import feeds


## Networking

class TestWithSession(unittest.TestCase):
    """Test the with_session context manager."""
    def test_referer(self) -> None:
        """Test creating a session with a referer."""
        sess: requests.Session
        # Test with a referer
        with feeds.with_session(referer="https://example.org") as sess:
            self.assertIsInstance(sess, requests.Session)
            self.assertTrue("Referer" in sess.headers)
            self.assertEqual(sess.headers["Referer"], "https://example.org")
        # Test without a referer
        with feeds.with_session() as sess:
            self.assertIsInstance(sess, requests.Session)
            if "Referer" in sess.headers:
                self.assertNotEqual(sess.headers["Referer"], "https://example.org")

    def test_user_agent(self) -> None:
        """Test creating a session with a user agent."""
        sess: requests.Session
        # Test with a user agent
        user_agent = "Test Program 1.0"
        with feeds.with_session(user_agent=user_agent) as sess:
            self.assertIsInstance(sess, requests.Session)
            self.assertTrue("User-Agent" in sess.headers)
            self.assertEqual(sess.headers["User-Agent"], user_agent)
        # Test without a user agent
        with feeds.with_session() as sess:
            self.assertTrue("User-Agent" in sess.headers)
            self.assertEqual(sess.headers["User-Agent"], feeds.DEFAULT_USER_AGENT)

    def test_proxy(self) -> None:
        """Test creating a session with a proxy."""
        sess: requests.Session
        proxy = "https://example.org"
        # Test with a proxy
        with feeds.with_session(proxy=proxy) as sess:
            self.assertIsInstance(sess, requests.Session)
            self.assertTrue("http" in sess.proxies)
            self.assertEqual(sess.proxies["http"], proxy)
            self.assertTrue("https" in sess.proxies)
            self.assertEqual(sess.proxies["https"], proxy)
        # Test without a user agent
        with feeds.with_session() as sess:
            if "http" in sess.proxies:
                self.assertNotEqual(sess.proxies["http"], proxy)
            if "https" in sess.proxies:
                self.assertNotEqual(sess.proxies["https"], proxy)

class TestGetUserAgent(unittest.TestCase):
    """Test the get_user_agent function."""
    env: dict[str, str] = {}
    rss_user_agent: str = "User Agent from RSS_USER_AGENT"
    user_agent: str = "User Agent from USER_AGENT"
    def setUp(self):
        # Back up settings
        self.env = environ

    def tearDown(self):
        global environ
        # Restore settings
        for setting in ("USER_AGENT", "RSS_USER_AGENT"):
            if setting in self.env:
                environ[setting] = self.env[setting]
            elif setting not in self.env and setting in environ:
                del environ[setting]

    def test_rss_user_agent(self) -> None:
        """Test getting value from RSS_USER_AGENT environment variable."""
        # Ensure RSS_USER_AGENT has greatest priority
        environ["RSS_USER_AGENT"] = self.rss_user_agent
        environ["USER_AGENT"] = self.user_agent
        self.assertEqual(feeds.get_user_agent(), self.rss_user_agent)
        # Ensure still fetchable when USER_AGENT is not set
        del environ["USER_AGENT"]
        self.assertEqual(feeds.get_user_agent(), self.rss_user_agent)

    def test_user_agent(self) -> None:
        """Test getting value from the USER_AGENT environment variable."""
        if "RSS_USER_AGENT" in environ:
            del environ["RSS_USER_AGENT"]
        environ["USER_AGENT"] = self.user_agent
        self.assertEqual(feeds.get_user_agent(), self.user_agent)

    def test_default_value(self) -> None:
        """Test getting a value when neither RSS_USER_AGENT not USER_AGENT is set."""
        if "RSS_USER_AGENT" in environ:
            del environ["RSS_USER_AGENT"]
        if "USER_AGENT" in environ:
            del environ["USER_AGENT"]
        self.assertEqual(feeds.get_user_agent(), feeds.DEFAULT_USER_AGENT)
