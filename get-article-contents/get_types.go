package article_getter

import (
	"compress/gzip"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/beevik/etree"
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
	Proxy       string
}

func GetFeed(conf *Config, client *http.Client) (*feed.Feed, error) {
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

func feedWorker(in chan struct {
	string
	int
}, out chan *result, conf *Config, client *http.Client) {
	for url := range in {
		out <- getPage(url.int, url.string, conf.CssSelector, conf.UserAgent, client)
	}
}

func EnrichFeed(feed *feed.Feed, conf *Config, client *http.Client) error {
	var fetchedMap artMap = make(artMap)
	urls := getUrls(feed, conf.RemoteUrl)
	in := make(chan struct {
		string
		int
	})
	out := make(chan *result, len(urls))
	// Initialize the workgroup
	for range 3 {
		go feedWorker(in, out, conf, client)
	}
	// Run
	for id, url := range urls {
		in <- struct {
			string
			int
		}{url, id}
	}
	for range len(urls) {
		r := <-out
		if r.Err == nil {
			fetchedMap[r.Id] = r.Content
		} else {
			log.Printf("Received error when downloading article: %s", r.Err)
		}
	}
	for id, doc := range fetchedMap {
		if doc == nil { // Nothing was found
			continue
		}
		h, err := doc.Html()
		if err == nil && h != "" {
			feed.Items[id].Content = h
		} else if err != nil {
			log.Printf("Failed to produce article Html: %s", err)
		} else {
			// Link could theoretically be empty here, but likely won't be
			log.Printf("Received no viable Html for %s", feed.Items[id].Link)
		}
	}
	return nil
}

// Convert the gofeed object into an ATOM feed
func MakeFeed(feed *feed.Feed) string {
	if feed == nil {
		return ""
	}
	doc := etree.NewDocument()
	root := doc.CreateElement("feed")
	doc.SetRoot(root)
	// Make this an ATOM feed
	root.CreateAttr("xmlns", "http://www.w3.org/2005/Atom")
	// Title is mandatory
	root.AddChild(createTextElement("title", feed.Title, doc))
	// Id is mandatory
	// TODO: How to get this? It is not included in the parsed feed.
	root.AddChild(createTextElement("id", "", doc))
	if feed.Link != "" {
		root.AddChild(createLink(feed.Link, doc))
	} else {
		for _, link := range feed.Links {
			root.AddChild(createLink(link, doc))
		}
	}
	// Updated is mandatory
	if feed.Updated != "" {
		root.AddChild(createTextElement("updated", feed.Updated, doc))
	} else {
		root.AddChild(createTextElement("updated", currentTime(), doc))
	}
	if feed.Copyright != "" {
		root.AddChild(createTextElement("copyright", feed.Copyright, doc))
	}
	// If at least one author is not specified, then every article must have an author
	if len(feed.Authors) > 0 {
		for _, author := range feed.Authors {
			root.AddChild(createAuthor(author, doc))
		}
	}
	// Program used to create the feed
	if feed.Generator != "" {
		root.AddChild(createTextElement("generator", feed.Generator, doc))
	}
	if feed.Image != nil && feed.Image.URL != "" {
		// TODO: Check if this should be a logo instead?
		// Logos should be twice as tall as they are wide,
		// but icons should be square
		root.AddChild(createTextElement("icon", feed.Image.URL, doc))
	}
	// This is pointless without these
	for _, item := range feed.Items {
		root.AddChild(createItem(item, doc))
	}
	str, _ := doc.WriteToString()
	return str
}

func createItem(item *feed.Item, doc *etree.Document) *etree.Element {
	root := doc.CreateElement("entry")
	// Title, ID, and Updated are all mandatory
	root.AddChild(createTextElement("title", item.Title, doc))
	root.AddChild(createTextElement("id", item.GUID, doc))
	if item.Updated != "" {
		root.AddChild(createTextElement("updated", item.Updated, doc))
		if item.Published != "" {
			root.AddChild(createTextElement("published", item.Published, doc))
		}
	} else {
		// Since this is mandatory, used published date to fill in
		root.AddChild(createTextElement("updated", item.Published, doc))
	}
	// Technically optional
	for _, author := range item.Authors {
		root.AddChild(createAuthor(author, doc))
	}
	if item.Description != "" {
		// TODO: Does this escape the HTML/XML?
		if content, err := parseXML(item.Description); err == nil && content != nil {
			// Only create if able to parse
			summary := doc.CreateElement("summary")
			summary.AddChild(content)
			root.AddChild(summary)
		}
	}
	// Add links
	if item.Link != "" {
		root.AddChild(createLink(item.Link, doc))
	} else {
		for _, link := range item.Links {
			root.AddChild(createLink(link, doc))
		}
	}
	// This one is why this whole program exists
	if item.Content != "" {
		root.AddChild(makeContent(item.Content, doc))
	} else {
		// Link could be empty here, but probably won't be
		log.Printf("Article '%s' has no content", item.Link)
	}
	if len(item.Categories) > 0 {
		for _, category := range item.Categories {
			cat := doc.CreateElement("category")
			cat.CreateAttr("term", category)
			root.AddChild(cat)
		}
	}
	// TODO: Add other elements?
	return root
}

func makeContent(html string, doc *etree.Document) *etree.Element {
	if xmlString, err := convertToXML(html); err == nil {
		if xml, err := parseXML(xmlString); err == nil {
			element := doc.CreateElement("content")
			element.CreateAttr("type", "xhtml")
			element.AddChild(xml)
			return element
		} else {
			log.Printf("Failed to convert string to XML, using HTML instead: %s", err)
		}
	} else {
		log.Printf("Failed to convert to XML, using HTML instead: %s", err)
	}
	element := createTextElement("content", html, doc)
	element.CreateAttr("type", "html")
	return element
}

func parseXML(xml string) (*etree.Element, error) {
	doc := etree.NewDocument()
	if err := doc.ReadFromString(xml); err != nil {
		return nil, err
	}
	return doc.Root(), nil
}

func createAuthor(author *feed.Person, doc *etree.Document) *etree.Element {
	root := doc.CreateElement("author")
	if author.Name != "" {
		root.AddChild(createTextElement("name", author.Name, doc))
	}
	if author.Email != "" {
		root.AddChild(createTextElement("email", author.Email, doc))
	}
	return root
}

func createLink(href string, doc *etree.Document) *etree.Element {
	link := doc.CreateElement("link")
	link.CreateAttr("href", href)
	return link
}

// Make an ISO-formatted datetime string
func currentTime() string {
	format := "1970-01-01T15:04:05Z"
	return time.Now().Format(format)
}

func createTextElement(tag, text string, doc *etree.Document) *etree.Element {
	element := doc.CreateElement(tag)
	t := doc.CreateText(text)
	element.AddChild(t)
	return element
}

// Map article URLs to their contents
type artMap map[int]*goquery.Selection

type result struct {
	Id      int // Track which item this belongs to
	Content *goquery.Selection
	Err     error
}

func getPage(id int, url, selector, userAgent string, client *http.Client) *result {
	res := result{Id: id}
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		res.Err = err
		return &res
	}
	addHeaders(url, userAgent, req)
	r, err := client.Do(req)
	if err != nil {
		res.Err = err
		return &res
	}
	defer r.Body.Close()
	if r.StatusCode != 200 {
		res.Err = fmt.Errorf("received error code %d", r.StatusCode)
		return &res
	}
	// gzip was requested in the added headers
	var reader io.ReadCloser = r.Body
	if r.Header.Get("content-encoding") == "gzip" {
		reader, err = gzip.NewReader(r.Body)
		if err != nil {
			res.Err = err
			return &res
		}
		defer reader.Close()
	}
	doc, err := goquery.NewDocumentFromReader(reader)
	if err != nil {
		res.Err = err
		return &res
	}
	doc.Find("script").Remove()
	selection := doc.Find(selector)
	if selection.Size() > 0 {
		res.Content = selection
		return &res
	} else {
		res.Err = ErrNoMatches
		return &res
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
