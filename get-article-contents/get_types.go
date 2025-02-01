package article_getter

import (
	"compress/gzip"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
	feed "github.com/mmcdole/gofeed"
)

var ErrTimeoutReached = errors.New("operation timed out")
var ErrNoMatches = errors.New("nothing matched the selector")

// The config for operations
type Config struct {
	RemoteUrl   string
	CssSelector string
	UserAgent   string
	Timeout     time.Duration
}

func GetFeed(conf *Config) (*feed.Feed, error) {
	trans := http.Transport{IdleConnTimeout: 10 * time.Second}
	client := http.Client{Transport: &trans}
	req, err := http.NewRequest("GET", conf.RemoteUrl, nil)
	if err != nil {
		return nil, err
	}
	addHeaders(conf.RemoteUrl, conf.UserAgent, req)
	res, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()
	var reader io.ReadCloser = res.Body
	if res.Header.Get("content-encoding") == "gzip" {
		r, err := gzip.NewReader(res.Body)
		if err != nil {
			return nil, err
		}
		defer r.Close()
		reader = r
	}
	parser := feed.NewParser()
	return parser.Parse(reader)
}

func EnrichFeed(feed *feed.Feed, conf *Config) error {
	var fetchedMap artMap = make(artMap)
	// How long to wait between requests
	const sendDelay = 200 * time.Millisecond
	// Content should go in the <description> tag if this is RSS, or in <content> for atom
	urls := getUrls(feed, conf.RemoteUrl)
	ch := make(chan *result, len(urls))
	for id, url := range urls {
		go getPage(id, url, conf.CssSelector, conf.UserAgent, ch)
		// Try and avoid being flagged as a bot
		time.Sleep(sendDelay)
	}
	for i := 0; i < len(urls); i++ {
		r := <-ch
		if r.Err == nil {
			fetchedMap[r.Id] = r.Content
		} else {
			// TODO: Log this somewhere
			fetchedMap[r.Id] = nil
		}
	}
	for id, doc := range fetchedMap {
		if doc == nil {
			continue
		}
		h, err := doc.Html()
		if err == nil {
			feed.Items[id].Content = h
		}
	}
	return nil
}

// Map article URLs to their contents
type artMap map[int]*goquery.Selection

type result struct {
	Id      int // Track which item this belongs to
	Content *goquery.Selection
	Err     error
}

func getPage(id int, url, selector, userAgent string, ch chan *result) {
	res := result{Id: id}
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		res.Err = err
		ch <- &res
		return
	}
	trans := http.Transport{IdleConnTimeout: 10 * time.Second}
	client := &http.Client{Transport: &trans}
	addHeaders(url, userAgent, req)
	r, err := client.Do(req)
	if err != nil {
		res.Err = err
		ch <- &res
		return
	}
	defer r.Body.Close()
	if r.StatusCode != 200 {
		res.Err = fmt.Errorf("received error code %d", r.StatusCode)
		ch <- &res
		return
	}
	// gzip was requested in the added headers
	var reader io.ReadCloser = r.Body
	if r.Header.Get("content-encoding") == "gzip" {
		reader, err = gzip.NewReader(r.Body)
		if err != nil {
			res.Err = err
			ch <- &res
			return
		}
		defer reader.Close()
	}
	doc, err := goquery.NewDocumentFromReader(reader)
	if err != nil {
		res.Err = err
		ch <- &res
		return
	}
	selection := doc.Find(selector)
	if selection.Size() > 0 {
		res.Content = selection
		ch <- &res
		return
	} else {
		res.Err = ErrNoMatches
		ch <- &res
		return
	}
}

func addHeaders(url, userAgent string, req *http.Request) {
	req.Header.Add("Referer", url)            // Firefox can send the url of the page as its own referer
	req.Header.Add("User-Agent", userAgent)   // Override Go's default
	req.Header.Add("Sec-GPC", "1")            // Global Privacy Control
	req.Header.Add("Accept-Encoding", "gzip") // Try to use compression
	req.Header.Add("Sec-Fetch-Dest", "document")
	req.Header.Add("Sec-Fetch-Mode", "navigate")
	req.Header.Add("Sec-Fetch-Site", "same-origin")
	req.Header.Add("Sec-Fetch-User", "?1")
}

func getUrls(f *feed.Feed, remote string) []string {
	urls := make([]string, len(f.Items))
	for c, i := range f.Items {
		if len(i.Link) > 0 && i.Link[0] == '/' {
			urls[c] = fixUrl(i.Link, remote)
		} else {
			urls[c] = i.Link
		}
	}
	return urls
}

// Some feeds may specify the URL relative to the root,
// instead of with the full protocol+domain.
func fixUrl(u, base string) string {
	// If URL was invalid, would have failed earlier in the program
	loc := strings.Index(base[8:], "/")
	if loc > 0 {
		return base[:8+loc] + u
	} else { // No "/" at end, and no path, e.g. "https://example.org"
		return base + u
	}
}
