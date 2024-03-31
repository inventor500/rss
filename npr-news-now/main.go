package main

import (
	"os"
	"regexp"

	rss "github.com/inventor500/rss/podcast-feed-regex"
)

const Url = "https://feeds.npr.org/500005/podcast.xml"

func main() {
	os.Exit(rss.MainFunction(Url, makeRegex()))
}

func makeRegex() []rss.Replacement {
	regex := make([]rss.Replacement, 3)
	regex[0] = rss.Replacement{
		Regex:       regexp.MustCompile(`chrt\.fm/.*ondemand\.npr\.org`),
		Replacement: "onedemand.npr.org",
	}
	regex[1] = rss.Replacement{
		Regex:       regexp.MustCompile(`chrt\.fm/.*/traffic\.megaphone\.fm`),
		Replacement: "traffic.megaphone.fm",
	}
	regex[2] = rss.Replacement{
		Regex:       regexp.MustCompile(`\?p=.*"`),
		Replacement: "\"",
	}
	return regex
}
