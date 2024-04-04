package main

import (
	"os"

	rss "github.com/inventor500/rss/podcast-feed-regex"
)

const Url = "https://feeds.npr.org/500005/podcast.xml"

func main() {
	os.Exit(rss.MainFunction(Url, rss.MakeRegex(
		[][]string{
			{`chrt\.fm/.*ondemand\.npr\.org`, "onedemand.npr.org"},
			{`chrt\.fm/.*/traffic\.megaphone\.fm`, "traffic.megaphone.fm"},
			{`\?p=.*"`, "\""},
		},
	)))
}
