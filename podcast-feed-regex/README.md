# Podcast Feed Regex

This is a library used other places in this repository. Call into it's `MainFunction`.

Scripts using this library will use the user agent specified by the `RSS_USER_AGENT` environment variable when sending HTTPS requests.

Example:

```go
func main() {
	os.Exit(rss.MainFunction(Url, makeRegex()))
}
```

Where `makeRegex()` returns an array of `Replacement` objects.


## `MainFunction`

This function takes a URL (string) and list of replacements (`[]Replacement`). `MainFunction` downloads the RSS/Atom feed and uses the `Replacement` objects to do find/replace on the feed, before printing it to standard out.

Returns 0 if successful, 1 otherwise.

## `MakeRegex`

This fuction takes a slice of slices of strings. Each of the interior slices is expected to be two elements long, where the first element is a string representation of a regular expression, and the second is the intended replacement of the regular expression.

## `Replacement`

This `struct` contains a `*regexp.Regexp` (`Regex`) and a string (`Replacement`). The intention is to replace anything that matches `Regex` with `Replacement`.
