# Fox 6 Milwaukee Feed Downloader

This script will download and enhance the feed for Fox 6 Milwaukee.

* For news articles where the article body is available, it downloads and adds it to the feed.
* For posts containing a web video, the link is added as though it were a podcast.  
Note that the podcast links are not guaranteed to be stable, i.e. an old link may become invalid.

## Usage

```sh
python3 fox_6_milwaukee.py [--proxy <proxy-url>] [--user-agent "<user-agent>"]
```

* `proxy-url`: The URL of a proxy server to use, e.g. `socks5h://localhost:1148`  
Use of a proxy is *highly* recommended. [Wireproxy](https://github.com/whyvl/wireproxy) is an example.
* `user-agent`: The user agent string to send with HTTP requests.  
If not specified, this will be read from the `RSS_USER_AGENT` environment variable.  
If that is not specified, the user agent will be read from the `USER_AGENT` variable.  
If that is not specified, then a sensible default will be used instead.
