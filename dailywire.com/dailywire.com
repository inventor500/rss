#! /bin/sh
# data-saferedirecturl is used by gmail, and for some reason is reason is present in these feeds sometimes
# Removing it should get rid of some of the ads
simulate-browser --regex '<(?:[hH][0-9]|p)>.*?<a href=".*?data-saferedirecturl=".*?".*?</a>(?:\n|.)*?</(?:[hH][0-9]|p)>' '' '(<(?:h[0-9]|p)>(?:<[aA].*?>)?<(?:strong|b)>.*?(?:WATCH|RELATED|[0-9]{1,2}[%\$] OFF).*?</(?:strong|b)>(?:</[aA]>)?</(?:h[0-9]|p)>)' '' '<[pP]>.*?CHECK OUT THE DAILY WIRE HOLIDAY GIFT GUIDE.*?</[pP]>' '' https://www.dailywire.com/feeds/rss.xml

# vim:set filetype=sh et:

