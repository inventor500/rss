package simulate_browser_test

import (
	"regexp"
	"testing"

	sim "github.com/inventor500/rss/simulate-browser"
)

func TestApplyRegex(t *testing.T) {
	const startString = "<html><body>Hello world!</body></html>"
	t.Run("Single replacement", func(t *testing.T) {
		const replacedString = "<lmth><body>Hello world!</body></lmth>"
		regex := []sim.FindReplace{{
			Find:    regexp.MustCompile("html"),
			Replace: "lmth",
		}}
		if result := sim.ApplyRegex(regex, startString); result != replacedString {
			t.Errorf("Expected %s, received %s", replacedString, result)
		}
	})
	t.Run("Double replacement", func(t *testing.T) {
		regex := []sim.FindReplace{
			{
				Find:    regexp.MustCompile("html"),
				Replace: "lmth",
			},
			{
				Find:    regexp.MustCompile("lmth"),
				Replace: "html",
			},
		}
		if result := sim.ApplyRegex(regex, startString); result != startString {
			t.Errorf("Expected %s, received %s", startString, result)
		}
	})
}
