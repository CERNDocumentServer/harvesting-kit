from cgi import escape
from urllib import urlencode

from invenio.webinterface_handler_config import HTTP_BAD_REQUEST, SERVER_RETURN
from invenio.webpage import pagefooteronly, pageheaderonly, page
from invenio.search_engine import perform_request_search
from invenio.search_engine import get_coll_i18nname, get_record
from invenio.bibrecord import record_get_field_value


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

CFG_JOURNALS = ['Acta',
                'Advances in High Energy Physics',
                'Chinese Physics C',
                'European Physical Journal C',
                'Journal of Cosmology and Astroparticle Physics',
                'Journal of High Energy Physics',
                'New Journal of Physics',
                'Nuclear Physics B',
                'Physics Letters B',
                'Progress of Theoretical and Experimental Physics']

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
    for i, nation_tuple in enumerate(_CFG_NATION_MAP):
        query = _build_query(nation_tuple)
        results = perform_request_search(p=query, of='intbitset')
        req.write("""<tr><td>%s</td><td><a href="/search?%s&sc=1">%s</a></td><td><a href="/nations.py/articles?i=%s" target="_blank">Articles</td><tr>\n""" % (
                escape(nation_tuple[0]), escape(urlencode([("p", query)]), True), len(results), i
            ))
        req.flush()
    req.write("</table>\n")
    req.write(pagefooteronly(req=req))
    return ""

def articles(req, i):
    try:
        i = int(i)
        assert 0 <= i < len(_CFG_NATION_MAP)
    except:
        raise SERVER_RETURN(HTTP_BAD_REQUEST)
    nation_tuple = _CFG_NATION_MAP[i]
    ret = []
    page_title = "SCOAP3 Articles by authors from %s" % nation_tuple[0]
    query = _build_query(nation_tuple)
    for journal in CFG_JOURNALS:
        results = perform_request_search(p=query, cc=journal, of='intbitset')
        if not results:
            #ret.append("<p>No articles yet</p>")
            continue
        ret.append("<h2>%s (%s)</h2" % (escape(get_coll_i18nname(journal)), len(results)))
        ret.append("<p><ul>")
        for recid in results:
            record = get_record(recid)
            title = record_get_field_value(record, '245', code='a')
            doi = record_get_field_value(record, '024', '7', code='a')
            ret.append('<li><a href="http://dx.doi.org/%s" target="_blank">%s</a>: %s</li>' % (escape(doi, True), escape(doi), title))
        ret.append("</ul></p>")
    body = '\n'.join(ret)
    return page(req=req, title=page_title, body=body)

def csv(req):
    req.content_type = 'text/csv; charset=utf-8'
    req.headers_out['content-disposition'] = 'attachment; filename=scoap3.csv'
    header = ','.join(['Nation'] + [get_coll_i18nname(journal) for journal in CFG_JOURNALS])
    print >> req, header
    for nation_tuple in _CFG_NATION_MAP:
        query = _build_query(nation_tuple)
        line = ','.join([nation_tuple[0]] + [str(len(perform_request_search(p=query, cc=journal, of='intbitset'))) for journal in CFG_JOURNALS])
        print >> req, line
