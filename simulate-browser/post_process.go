package simulate_browser

import (
	"fmt"
	"regexp"
)

// The Find/Replace values for post-processing the downloaded item.
type FindReplace struct {
	Find    *regexp.Regexp
	Replace string
}

// Apply the regular expressions in the list to the string.
func ApplyRegex(regexList []FindReplace, text string) string {
	for i := 0; i < len(regexList); i++ {
		fmt.Println(regexList[i])
		text = regexList[i].Find.ReplaceAllString(text, regexList[i].Replace)
		fmt.Println(text)
	}
	return text
}
