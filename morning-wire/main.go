package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
)

func main() {
	os.Exit(mainFunction())
}

const Url = "https://feeds.simplecast.com/WCb5SgYj"
const UserAgent = "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Thunderbird/102.14.0"

// This could probably become one regex, but the feed is not long enough for multiple iterations to be a concern
var urlFixRegex = regexp.MustCompile(`dts\.podtrac\.com/.*/injector\.simplecastaudio\.com`)
var trackingRegex = regexp.MustCompile(`\?aid=rss_feed.*"`)

func mainFunction() int {
	feed, err := downloadFeed()
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err)
		return 1
	}
	// It is unnecessary to actually parse the feed to make such a small change
	feed = urlFixRegex.ReplaceAllString(feed, "injector.simplecastaudio.com")
	feed = trackingRegex.ReplaceAllString(feed, "\"")
	fmt.Print(feed)
	return 0
}

func downloadFeed() (string, error) {
	client := http.Client{}
	req, _ := http.NewRequest("GET", Url, nil)
	addHeaders(req)
	res, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to retrieve feed")
	}
	defer res.Body.Close()
	if res.StatusCode != 200 {
		return "", fmt.Errorf("received status code %d", res.StatusCode)
	}
	if b, err := io.ReadAll(res.Body); err == nil {
		return string(b), nil
	} else {
		return "", err
	}
}

func addHeaders(req *http.Request) {
	req.Header.Set("User-Agent", UserAgent)
	req.Header.Set("DNT", "1")
	req.Header.Set("Sec-GPC", "1")
	req.Header.Set("Pragma", "no-cache")
	req.Header.Set("Cache-Control", "no-cache")
}
