package simulate_browser

import (
	"compress/gzip"
	"fmt"
	"io"
	"net/http"
	"time"
)

/** Download the file.
 * addHeaders: The function invoked to add headers to the request
 */
func DownloadFile(url string, timeout int, userAgent string) (string, error) {
	client := http.Client{
		Timeout: time.Duration(timeout) * time.Second,
	}
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

/** Add headers to the request.
 * url: Used for the Referer header
 * userAgent: The user agent string
 */
func addHeaders(url, userAgent string, req *http.Request) {
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
