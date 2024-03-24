package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
)

// These are here to make them easier to change later on
const Url = "https://www.dailywire.com/feeds/rss.xml"
const UserAgent = "Mozilla/5.0 (Windows NT 10.0; rv:123.0) Gecko/20100101 Firefox/123.0"

func main() {
	os.Exit(mainFunction())
}

func mainFunction() int {
	client := http.Client{}
	req, _ := http.NewRequest("GET", Url, nil)
	addHeaders(req)
	res, err := client.Do(req)
	if err != nil {
		fmt.Fprintln(os.Stderr, "Failed to retrieve feed")
		return 1
	}
	defer res.Body.Close()
	if res.StatusCode != 200 {
		fmt.Fprint(os.Stderr, "Received status code %i\n", res.StatusCode)
		return 1
	}
	if b, err := io.ReadAll(res.Body); err == nil {
		fmt.Printf("%s", b)
	} else {
		fmt.Fprintf(os.Stderr, "Failed to read body")
		return 1
	}
	return 0
}

func addHeaders(req *http.Request) {
	req.Header.Set("User-Agent", UserAgent)
	req.Header.Set("DNT", "1")
	req.Header.Set("Sec-GPC", "1")
	req.Header.Set("Sec-Fetch-Dest", "document")
	req.Header.Set("Sec-Fetch-Mode", "navigate")
	req.Header.Set("Sec-Fetch-Site", "same-site")
	req.Header.Set("Sec-Fetch-User", "?1")
	req.Header.Set("Pragma", "no-cache")
	req.Header.Set("Cache-Control", "no-cache")
}
