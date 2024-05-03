package simulate_browser

import (
	"log"
	"regexp"
)

// The Find/Replace values for post-processing the downloaded item.
type FindReplace struct {
	Find    *regexp.Regexp
	Replace string
}

// Apply the regular expressions in the list to the string.
func ApplyRegex(regexList []FindReplace, text string, verbose bool) string {
	logs := log.Default()
	for i := 0; i < len(regexList); i++ {
		if verbose {
			logs.Printf("Replacing '%s' with '%s'...\n", regexList[i].Find, regexList[i].Replace)
		}
		text = regexList[i].Find.ReplaceAllString(text, regexList[i].Replace)
	}
	return text
}
