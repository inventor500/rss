# Podcast Feed Regex

This is a library used other places in this repository. Call into it's `MainFunction`.

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

## `Replacement`

This `struct` contains a `*regexp.Regexp` (`Regex`) and a string (`Replacement`). The intention is to replace anything that matches `Regex` with `Replacement`.
