# Simulate Browser

This is a utility that simulates a request from the Firefox web browser. This helps to download feeds from websites that try to ensure that only "real people" download feeds. This is accomplished by setting (almost) all headers to match what Firefox ESR.

This script also automatically decompresses `gzip`ed output.

The same thing could easily be accomplished by writing a wrapper script over cURL and `gzip`, but this is more portable.

## Usage

Environment variables:
- `RSS_USER_AGENT`: The user agent. Defaults to a user agent string taken from Firefox ESR.

Parameters:
- The URL to download.

Example usage:
`./simulate-browser <url>`


## Limitations

- Currently does not accept the `br` or `deflate` encodings, which Firefox does.
