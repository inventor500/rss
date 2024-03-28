package main

import (
	"os"
	"regexp"

	rss "github.com/inventor500/rss/podcast-feed-regex"
)

const Url = "https://feeds.simplecast.com/WCb5SgYj"

func main() {
	os.Exit(rss.MainFunction(Url, makeRegex()))
}

func makeRegex() []rss.Replacement {
	regex := make([]rss.Replacement, 2)
	regex[0] = rss.Replacement{
		Regex:       regexp.MustCompile(`dts\.podtrac\.com/.*/injector\.simplecastaudio\.com`),
		Replacement: "injector.simplecastaudio.com",
	}
	regex[1] = rss.Replacement{
		Regex:       regexp.MustCompile(`\?aid=rss_feed.*"`),
		Replacement: "\"",
	}
	return regex
}
