# Daily Wire Feed Getter

The Daily Wire provides an rss feed. However, the URL for this feed will first return 403. The error page attempts to use JavaScript to reload the page, but feed readers don't use JavaScript when fetching feeds.

Fortunately, setting a few headers will cause the actual feed to load. This is a short Go program which sends a request with those headers.

To compile, run `go build` in the `dailywire.com` directory (in which this file is located).

This may be included in your Newsboat URLs file with the following line (assuming that the executable is in your `PATH`):

```shell
exec:dailywire.com "~The Daily Wire"
```

## Limitations

* This *will not* follow Newsboat's proxy settings.
* The user agent is currently hard-coded.
