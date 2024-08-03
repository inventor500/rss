#! /bin/sh
# data-saferedirecturl is used by gmail, and for some reason is reason is present in these feeds sometimes
# Removing it should get rid of some of the ads
simulate-browser -regex '(?i)<p>.*?<a href=".*?data-saferedirecturl=".*?".*?</a>(?:\n|.)*?</p>' '' https://www.dailywire.com/feeds/rss.xml

