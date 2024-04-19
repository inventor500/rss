package main

import (
	"compress/gzip"
	"fmt"
	"io"
	"net/http"
	"os"
)

// This user agent is used if the RSS_USER_AGENT environment variable is not set.
const DefaultUserAgent = "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"

// The main function. Returns 0 if successful, 1 otherwise.
func MainFunc() int {
	if len(os.Args) != 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <url>\n", os.Args[0])
		return 1
	}
	url := os.Args[1]
	userAgent := os.Getenv("RSS_USER_AGENT")
	if userAgent == "" {
		userAgent = DefaultUserAgent
	}
	result, err := DownloadFile(url, userAgent, AddHeaders)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to download: %s", err)
		return 1
	} else {
		fmt.Println(result)
		return 0
	}
}

// Add headers to the request.
// url: Used for the Referer header
// userAgent: The user agent string
func AddHeaders(url, userAgent string, req *http.Request) {
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept", "text/html,application/xhtml+xmlapplication/xml;q=0.9,image/avif,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	req.Header.Set("Accept-Encoding", "gzip")
	req.Header.Set("Referer", url)
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Upgrade-Insecure-Requests", "1")
	req.Header.Set("Sec-Fetch-Dest", "document")
	req.Header.Set("Sec-Fetch-Mode", "navigate")
	req.Header.Set("Sec-Fetch-Site", "same-origin")
	req.Header.Set("Sec-Fetch-User", "?1")
	req.Header.Set("DNT", "1")
	req.Header.Set("Sec-GPC", "1")
	req.Header.Set("TE", "Trailers")
}

// Download the file.
// addHeaders: Allows using a custom function to add readers
func DownloadFile(url, userAgent string, addHeaders func(string, string, *http.Request)) (string, error) {
	client := http.Client{}
	req, _ := http.NewRequest("GET", url, nil)
	addHeaders(url, userAgent, req)
	res, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer res.Body.Close()
	if res.StatusCode != 200 && res.StatusCode != 304 {
		return "", fmt.Errorf("received status code %d", res.StatusCode)
	}
	if res.Header.Get("Content-Encoding") == "gzip" {
		return decompress(res.Body)
	} else {
		b, err := io.ReadAll(res.Body)
		if err != nil {
			return "", err
		}
		return string(b), nil
	}

}

// Decompress the downloaded file.
func decompress(reader io.Reader) (string, error) {
	r, err := gzip.NewReader(reader)
	if err != nil {
		return "", err
	}
	defer r.Close()
	b, err := io.ReadAll(r)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

// The actual main function. Just calls os.Exit on the results of MainFunc.
func main() {
	os.Exit(MainFunc())
}
