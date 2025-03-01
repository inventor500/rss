package main

import (
	"flag"
	"fmt"
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
	conf, err := parseArgs()
	if err != nil {
		return err
	}
	// TODO: Maybe support reading from stdin for post-processing only?
	feed, err := getter.GetFeed(conf)
	if err != nil {
		return err
	}
	err = getter.EnrichFeed(feed, conf)
	if err != nil {
		return err
	}
	fmt.Println(getter.MakeFeed(feed))
	return nil
}

// Parse arguments
func parseArgs() (*getter.Config, error) {
	// TODO: Proxy support
	var conf getter.Config
	flag.StringVar(&conf.RemoteUrl, "url", "", "The url to fetch the feed from. Will also attempt to read from the final command line argument received.")
	flag.StringVar(&conf.CssSelector, "selector", "article", "The CSS selector to use when extractoring articles")
	flag.DurationVar(&conf.Timeout, "timeout", 10*time.Second, "Duration for which to wait for each individual feed.")
	flag.StringVar(&conf.UserAgent, "user-agent", "", fmt.Sprintf("User agent. If not specified, will read from, in order, the RSS_USER_AGENT and USER_AGENT environment variables. If neither of those is specified, will use the default user agent (%s).", DefaultUserAgent))
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
	if conf.UserAgent == "" {
		conf.UserAgent = os.Getenv("RSS_USER_AGENT")
	}
	if conf.UserAgent == "" {
		conf.UserAgent = os.Getenv("USER_AGENT")
	}
	if conf.UserAgent == "" {
		conf.UserAgent = DefaultUserAgent
	}
	return &conf, nil
}
