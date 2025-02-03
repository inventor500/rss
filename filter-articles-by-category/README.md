This is a script to filter articles with an unwanted category out of the feed. Unfortunately, not all feed readers support filtering by feed-assigned category.

Note that this script is for post-processing, not downloading a feed.

This script relies on the feed's report of article categories. If the feed does not specify categories, or reports them inaccurately, then this script will not help you!

# Usage

`filter-articles-by-category.py {<filename>|-} {<category1> ... <categoryn>}`

If `-` is given in place of a filename, the script will read from standard in.  
Categories will be matched in a case-insensitive manner with categories specified by news article.  
If the category specified by the news article contains any of the categories specified at the command line, the article will be removed from the feed.  
Articles that do not specify a category will not be removed.  
The feed, without the filtered articles, is printed to standard out.


## Example usage

Remove sports-related articles from `feed.xml`, printing the new feed to standard out:
```sh
python3 filter-articles-by-category.py feed.xml "Sports" "Baseball" "Basketball"
```

Remove business and opinion articles:
```sh
cat feed.xml | python filter-articles-by-category.py - "Business" "Commentary" "Opinion"
```
