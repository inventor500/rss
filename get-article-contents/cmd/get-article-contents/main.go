package main

import (
	"flag"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"time"

	getter "github.com/inventor500/rss/get-article-contents"
)

const DefaultUserAgent = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"

func main() {
	err := mainFunc()
	if err != nil {
		fmt.Fprintf(os.Stderr, "An error has occured: %s\n", err)
		os.Exit(1)
	}
}

func mainFunc() error {
	conf := parseArgs()
	if err := setHttpDefaults(conf.Proxy, conf.Timeout); err != nil {
		return err
	}
	if err := initLog(); err != nil {
		return err
	}
	client := http.Client{}
	// TODO: Maybe support reading from stdin for post-processing only?
	feed, err := getter.GetFeed(conf, &client)
	if err != nil {
		return err
	}
	// Remove old items from the feed
	if conf.MaxDaysBack != 0 {
		getter.TruncateFeed(feed, conf.MaxDaysBack)
	}
	err = getter.EnrichFeed(feed, conf, &client)
	if err != nil {
		return err
	}
	fmt.Println(getter.MakeFeed(feed))
	return nil
}

// Parse arguments
func parseArgs() *getter.Config {
	var conf getter.Config
	flag.StringVar(&conf.RemoteUrl, "url", "", "The url to fetch the feed from. Will also attempt to read from the final command line argument received.")
	flag.StringVar(&conf.CssSelector, "selector", "article", "The CSS selector to use when extractoring articles")
	flag.DurationVar(&conf.Timeout, "timeout", 10*time.Second, "Duration for which to wait for each individual feed.")
	flag.StringVar(&conf.UserAgent, "user-agent", "", fmt.Sprintf("User agent. If not specified, will read from, in order, the RSS_USER_AGENT and USER_AGENT environment variables. If neither of those is specified, will use the default user agent (%s).", DefaultUserAgent))
	flag.StringVar(&conf.Proxy, "proxy", "", "Proxy URL to use for HTTP requests, e.g. socks5h://localhost:8090")
	flag.IntVar(&conf.MaxDaysBack, "max-days-back", 15, "How far in the past an article can be before it is ignored, in days. 0 disables this functionality.")
	flag.Parse()
	if conf.RemoteUrl == "" {
		if len(flag.Args()) == 1 {
			conf.RemoteUrl = flag.Args()[0]
		} else {
			fmt.Fprintf(os.Stderr, "URL was not specified.\n")
			flag.Usage()
			os.Exit(1)
		}
	}
	if conf.MaxDaysBack < 0 {
		fmt.Fprintf(os.Stderr, "Days must be a positive integer, or 0")
		flag.Usage()
		os.Exit(1)
	}
	if conf.UserAgent == "" {
		conf.UserAgent = os.Getenv("RSS_USER_AGENT")
	}
	if conf.UserAgent == "" {
		conf.UserAgent = os.Getenv("USER_AGENT")
	}
	if conf.UserAgent == "" {
		conf.UserAgent = DefaultUserAgent
	}
	return &conf
}

func setHttpDefaults(proxyUrl string, timeout time.Duration) error {
	var proxy = http.ProxyFromEnvironment
	if proxyUrl != "" {
		u, err := url.Parse(proxyUrl)
		if err != nil {
			return err
		}
		proxy = http.ProxyURL(u)
	}
	http.DefaultTransport = &http.Transport{Proxy: proxy, IdleConnTimeout: timeout}
	return nil
}
