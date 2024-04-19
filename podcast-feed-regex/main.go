package podcast

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
)

// Can be overriden by setting the RSS_USER_AGENT environment variable
const DefaultUserAgent = "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"

type Replacement struct {
	Regex       *regexp.Regexp
	Replacement string
}

func MainFunction(url string, regex []Replacement) int {
	feed, err := downloadFeed(url)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err)
		return 1
	}
	for i := 0; i < len(regex); i++ {
		feed = regex[i].Regex.ReplaceAllString(feed, regex[i].Replacement)
	}
	fmt.Print(feed)
	return 0
}

func MakeRegex(regexTuples [][]string) []Replacement {
	replacements := make([]Replacement, len(regexTuples))
	for i := 0; i < len(regexTuples); i++ {
		if len(regexTuples[i]) != 2 {
			panic("regex tuples must be exactly two strings each")
		}
		replacements[i] = Replacement{
			Regex:       regexp.MustCompile(regexTuples[i][0]),
			Replacement: regexTuples[i][1],
		}
	}
	return replacements
}

func downloadFeed(url string) (string, error) {
	client := http.Client{}
	req, _ := http.NewRequest("GET", url, nil)
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
	userAgent := os.Getenv("RSS_USER_AGENT")
	if userAgent == "" {
		userAgent = DefaultUserAgent
	}
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("DNT", "1")
	req.Header.Set("Sec-GPC", "1")
	req.Header.Set("Pragma", "no-cache")
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	req.Header.Set("Cache-Control", "no-cache")
	req.Header.Set("Sec-Fetch-User", "?1")
	req.Header.Set("Sec-Fetch-Site", "none")
	req.Header.Set("Sec-Fetch-Mode", "navigate")
	req.Header.Set("Sec-Fetch-Dest", "document")
}
