from cgi import escape
from urllib import urlencode

from invenio.webpage import pagefooteronly, pageheaderonly
from invenio.search_engine import perform_request_search

_CFG_NATION_MAP = [
("Algeria", ),
("Argentina", ),
("Armenia", ),
("Australia", ),
("Austria", ),
("Azerbaijan", ),
("Belarus", ),
("Belgium", ),
("Bangladesh", ),
("Brazil", ),
("Bulgaria", ),
("Canada", ),
("CERN", ),
("Chile", ),
("China (PRC)", "PR China", "China"),
("Colombia", ),
("Costa Rica", ),
("Croatia", ),
("Cuba", ),
("Cyprus", ),
("Czech Republic", ),
("Denmark", ),
("Egypt", ),
("Estonia", ),
("Finland", ),
("France", ),
("Georgia", ),
("Germany", ),
("Greece", ),
("Hong-Kong", "Hong Kong"),
("Hungary", ),
("Iceland", ),
("India", ),
("Indonesia", ),
("Iran", ),
("Ireland", ),
("Israel", ),
("Italy", "Italia"),
("Japan", ),
("Korea", "Republic of Korea", "South Korea"),
("Lebanon", ),
("Lithuania", ),
("Mexico", ),
("Montenegro", ),
("Morocco", ),
("Netherlands", "The Netherlands"),
("New Zealand", ),
("Norway", ),
("Pakistan", ),
("Poland", ),
("Portugal", ),
("Romania", ),
("Russia", ),
("Saudi Arabia", ),
("Serbia", ),
("Singapore", ),
("Slovak Republic", "Slovakia"),
("Slovenia", ),
("South Africa", ),
("Spain", ),
("Sweden", ),
("Switzerland", ),
("Taiwan", ),
("Thailand", ),
("Tunisia", ),
("Turkey", ),
("Ukraine", ),
("United Kingdom", "UK", "U.K"),
("United States", "USA", "U.S.A"),
("Uruguay", ),
("Uzbekistan", ),
("Venezuela", ),
("Vietnam", ),
]

def _build_query(nation_tuple):
    out = []
    for value in nation_tuple:
        out.append('affiliation:"*%s" OR affiliation:"*%s."' % (value, value))
    return " OR ".join(out)

def index(req):
    req.content_type = "text/html"
    req.write(pageheaderonly("Nation numbers", req=req))
    req.write("<h1>Nation numbers</h1>")
    req.flush()
    req.write("<table>\n")
    for nation_tuple in _CFG_NATION_MAP:
        query = _build_query(nation_tuple)
        results = perform_request_search(p=query, of='intbitset')
        req.write("""<tr><td>%s</td><td><a href="/search?%s">%s</a></td><tr>\n""" % (
                escape(nation_tuple[0]), escape(urlencode([("p", query)]), True), len(results)
            ))
        req.flush()
    req.write("</table>\n")
    req.write(pagefooteronly(req=req))
    return ""
