package main

import (
	"os"

	rss "github.com/inventor500/rss/podcast-feed-regex"
)

const Url = "https://feeds.simplecast.com/WCb5SgYj"

func main() {
	os.Exit(rss.MainFunction(Url, rss.MakeRegex(
		[][]string{
			{`dts\.podtrac\.com/.*/injector\.simplecastaudio\.com`, "injector.simplecastaudio.com"},
			{`\?aid=rss_feed.*"`, "\""},
		},
	),
	))
}
