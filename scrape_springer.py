#!/usr/bin/env python
from cgi import escape
from bs4 import BeautifulSoup
from urllib import urlopen

## DOIs da includere in first articles.

URL = "http://link.springer.com/journal/10052/74/1/page/1"

soup = BeautifulSoup(urlopen(URL).read())
articles = soup.findAll('h3', {'class': 'title'})
print "<p><ul>"
for article in articles:
    article = article.find('a')
    href = article.get('href')
    doi = href.replace("/article/", "").encode('utf8')
    title = article.getText(' ', True).strip().encode('utf8')
    print '<li><a href="http://dx.doi.org/%s" target="_blank">%s</a>: %s</li>' % (escape(doi, True), escape(doi), title)
print "</ul></p>"
