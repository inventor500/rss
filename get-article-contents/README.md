# Get Article Contents

The `get-article-contents` program attempts to enrich an RSS/ATOM feed by downloading the contents of the article and inserting them into the feed.
This will *always* generate an ATOM feed, even if the original was an RSS feed.

## Feed

Usage: `get-article-contents [options] <url>`

| *Options*     | *Parameter*                | *Meaning*                                                                    |
|----------------|----------------------------|------------------------------------------------------------------------------|
| `--url`        | An HTTP(s) URL             | Where to fetch the feed from.                                                |
| `--selector`   | A CSS selector             | Used to select part of the article on the website for inclusion in the feed. |
| `--timeout`    | A length of time, e.g. 10s | Allowed timeout before fetch is assumed to have failed.                      |
| `--user-agent` | A user agent string        | Which user agent to use.                                                                             |

**Notes**:
* If `--url` is provided, the final `<url>` parameter is optional and will be ignored if provided.
* `--selector` is used to select a portion of a page. For example, if set to `article` (the default), then elements of the `article` type will be included in the RSS feed.
