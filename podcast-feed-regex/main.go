package podcast

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
)

const UserAgent = "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"

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
	req.Header.Set("User-Agent", UserAgent)
	req.Header.Set("DNT", "1")
	req.Header.Set("Sec-GPC", "1")
	req.Header.Set("Pragma", "no-cache")
	req.Header.Set("Cache-Control", "no-cache")
}
