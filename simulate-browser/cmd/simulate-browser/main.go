package main

import (
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"regexp"

	sim "github.com/inventor500/rss/simulate-browser"
)

// This user agent is used if the RSS_USER_AGENT environment variable is not set.
const DefaultUserAgent = "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"

type arguments struct {
	Timeout      int
	Replacements []sim.FindReplace
	Url          string
	Verbose      bool
}

// The main function. Returns 0 if successful, 1 otherwise.
func MainFunc() int {
	args, err := parseArguments()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Usage: %s [args] url\n", os.Args[0])
		flag.PrintDefaults()
		return 1
	}
	if args.Verbose {
		initializeLogger()
	}
	userAgent := os.Getenv("RSS_USER_AGENT")
	if userAgent == "" {
		userAgent = DefaultUserAgent
	}
	result, err := sim.DownloadFile(args.Url, args.Timeout, userAgent, args.Verbose)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to download: %s\n", err)
		return 1
	}
	if args.Replacements != nil {
		fmt.Println(sim.ApplyRegex(args.Replacements, result, args.Verbose))
	} else {
		fmt.Println(result)
	}
	return 0
}

func initializeLogger() {
	log.SetPrefix("")
}

func parseArguments() (*arguments, error) {
	timeout := flag.Int("timeout", 10, "Timeout in seconds for requests")
	useRegex := flag.Bool("regex", false, "Enable use of regular expressions for post-processing")
	verbose := flag.Bool("v", false, "Verbose mode")
	if len(os.Args) < 2 {
		return nil, errors.New("no arguments provided")
	}
	flag.Parse()
	if *useRegex {
		// The last argument should be the url
		args := flag.Args()
		if len(args)%2 != 1 {
			return nil, errors.New("invalid number of find/replace values - # find must match # replace")
		} else {
			findList := make([]sim.FindReplace, (len(args)-1)/2)
			// Iterate two at a time, skip the url
			for i := 0; i < (len(args)-1)/2; i++ {
				findList[i] = sim.FindReplace{
					Find:    regexp.MustCompile(args[i*2]),
					Replace: args[i*2+1],
				}
			}
			return &arguments{
				Timeout:      *timeout,
				Url:          flag.Arg(len(args) - 1),
				Replacements: findList,
				Verbose:      *verbose,
			}, nil
		}
	} else {
		return &arguments{
			Timeout: *timeout,
			Url:     flag.Arg(0),
			Verbose: *verbose,
		}, nil
	}
}

// The actual main function. Just calls os.Exit on the results of MainFunc.
func main() {
	os.Exit(MainFunc())
}
