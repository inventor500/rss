# Simulate Browser

This is a utility that simulates a request from the Firefox web browser. This helps to download feeds from websites that try to ensure that only "real people" download feeds. This is accomplished by setting (almost) all headers to match what Firefox.


## Usage

Environment variables:
- `RSS_USER_AGENT`: The user agent.
- `USER_AGENT`: If `RSS_USER_AGENT` is unspecified, then this variable is read.

Parameters:
- `--verbose`: Prints what it is doing to stderr. `-v` is also accepted.
- `--socks5-hostname`: Uses SOCKS 5 to make connections.
- `--timeout`: The time to wait for a response (in seconds). Defaults to 10 seconds. `-t` is also accepted.
- `--regex`: Enables the use of find/replace functionality. If this flag is enabled, regular expressions should alternate with their replacements before the URL, e.g. `expression1 replacement1 expression2 replacement2 https://example.com`. `-r` is also accepted.
- The URL to download.

Example usage:
`./simulate-browser <url>`


## Compilation

Requirements:
- A C++ compiler supporting C++20
- CMake
- cURL development headers

```shell
$ cmake -b build
$ cmake --build build
```
