from cgi import escape

from invenio.htmlutils import remove_html_markup
from invenio.search_engine import get_collection_reclist, get_coll_i18nname, get_record
from invenio.bibrecord import record_get_field_value

CFG_JOURNALS = ['Physics Letters B',
                   'Nuclear Physics B',
                   'Advances in High Energy Physics',
                   'Chinese Physics C',
                   'Journal of Cosmology and Astroparticle Physics',
                   'New Journal of Physics',
                   'Acta',
                   'Progress of Theoretical and Experimental Physics',
                   'European Physical Journal C',
                   'Journal of High Energy Physics']

def main():
    for journal in CFG_JOURNALS:
        name = get_coll_i18nname(journal)
        reclist = get_collection_reclist(journal)
        print "<h2>%s</h2>" % escape(name)
        if not reclist:
            print "<p>None yet.</p>"
            continue
        print "<p><ul>"
        for recid in reclist:
            record = get_record(recid)
            title = remove_html_markup(record_get_field_value(record, '245', code='a'), remove_escaped_chars_p=False).strip()
            doi = record_get_field_value(record, '024', '7', code='a')
            print '<li><a href="http://dx.doi.org/%s" target="_blank">%s</a>: %s</li>' % (escape(doi, True), escape(doi), title)
        print "</ul></p>"

if __name__ == "__main__":
    main()
