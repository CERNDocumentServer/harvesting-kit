## This file is part of SCOAP3.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
##
## SCOAP3 is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## SCOAP3 is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with SCOAP3; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""
WebSearch templates for SCOAP3
"""

import cgi

from invenio.config import CFG_SITE_LANG, CFG_BASE_URL, CFG_SITE_NAME, CFG_SITE_NAME_INTL, CFG_WEBSEARCH_ADVANCEDSEARCH_PATTERN_BOX_WIDTH, \
    CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES, CFG_WEBSEARCH_LIGHTSEARCH_PATTERN_BOX_WIDTH, CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS, \
    CFG_WEBSEARCH_SIMPLESEARCH_PATTERN_BOX_WIDTH
from invenio.urlutils import drop_default_urlargd, create_html_link
from invenio.messages import gettext_set_language
from invenio.websearch_templates import Template as DefaultTemplate

class Template(DefaultTemplate):
    def tmpl_record_format_htmlbrief_footer(self, ln, display_add_to_basket=True):
        """Returns the footer of the search results list when output
        is html brief. Note that this function is called for each collection
        results when 'split by collection' is enabled.

        See also: tmpl_record_format_htmlbrief_header(..),
                  tmpl_record_format_htmlbrief_body(..)

        Parameters:

          - 'ln' *string* - The language to display
          - 'display_add_to_basket' *bool* - whether to display Add-to-basket button
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """</table>
               <br />
               <input type="hidden" name="colid" value="0" />
               </form>"""

        return out

    def tmpl_record_format_htmlbrief_body(self, ln, recid,
                                          row_number, relevance,
                                          record, relevances_prologue,
                                          relevances_epilogue,
                                          display_add_to_basket=True):
        """Returns the html brief format of one record. Used in the
        search results list for each record.

        See also: tmpl_record_format_htmlbrief_header(..),
                  tmpl_record_format_htmlbrief_footer(..)

        Parameters:

          - 'ln' *string* - The language to display

          - 'row_number' *int* - The position of this record in the list

          - 'recid' *int* - The recID

          - 'relevance' *string* - The relevance of the record

          - 'record' *string* - The formatted record

          - 'relevances_prologue' *string* - HTML code to prepend the relevance indicator

          - 'relevances_epilogue' *string* - HTML code to append to the relevance indicator (used mostly for formatting)

        """

        # load the right message language
        _ = gettext_set_language(ln)

        checkbox_for_baskets = ''
        out = """
                <tr><td valign="top" align="right" style="white-space: nowrap;">
                    %(checkbox_for_baskets)s
                    <abbr class="unapi-id" title="%(recid)s"></abbr>

                %(number)s.
               """ % {'recid': recid,
                      'number': row_number,
                      'checkbox_for_baskets': checkbox_for_baskets}
        if relevance:
            out += """<br /><div class="rankscoreinfo"><a title="rank score">%(prologue)s%(relevance)s%(epilogue)s</a></div>""" % {
                'prologue' : relevances_prologue,
                'epilogue' : relevances_epilogue,
                'relevance' : relevance
                }
        out += """</td><td valign="top">%s</td></tr>""" % record

        return out

    def tmpl_alert_rss_teaser_box_for_query(self, id_query, ln, display_email_alert_part=True):
        """Propose teaser for setting up this query as alert or RSS feed.

        Parameters:
          - 'id_query' *int* - ID of the query we make teaser for
          - 'ln' *string* - The language to display
          - 'display_email_alert_part' *bool* - whether to display email alert part
        """
        return ""

    def tmpl_nbrecs_info(self, number, prolog=None, epilog=None, ln=CFG_SITE_LANG):
        """
        Return information on the number of records.

        Parameters:

        - 'number' *string* - The number of records

        - 'prolog' *string* (optional) - An HTML code to prefix the number (if **None**, will be
        '<small class="nbdoccoll">(')

        - 'epilog' *string* (optional) - An HTML code to append to the number (if **None**, will be
        ')</small>')
        """
        _ = gettext_set_language(ln)

        if number is None:
            number = 0
        if prolog is None:
            prolog = '''&nbsp;<small class="nbdoccoll">('''
        if epilog is None:
            epilog = ''')</small>'''

        if number is 0:
            return prolog + _("none yet") + epilog
        else:
            return prolog + self.tmpl_nice_number(number, ln) + epilog

    def tmpl_search_box(self, ln, aas, cc, cc_intl, ot, sp,
                        action, fieldslist, f1, f2, f3, m1, m2, m3,
                        p1, p2, p3, op1, op2, rm, p, f, coll_selects,
                        d1y, d2y, d1m, d2m, d1d, d2d, dt, sort_fields,
                        sf, so, ranks, sc, rg, formats, of, pl, jrec, ec,
                        show_colls=True, show_title=True):

        """
          Displays the *Nearest search terms* box

        Parameters:

          - 'ln' *string* - The language to display

          - 'aas' *bool* - Should we display an advanced search box? -1 -> 1, from simpler to more advanced

          - 'cc_intl' *string* - the i18nized current collection name, used for display

          - 'cc' *string* - the internal current collection name

          - 'ot', 'sp' *string* - hidden values

          - 'action' *string* - the action demanded by the user

          - 'fieldslist' *list* - the list of all fields available, for use in select within boxes in advanced search

          - 'p, f, f1, f2, f3, m1, m2, m3, p1, p2, p3, op1, op2, op3, rm' *strings* - the search parameters

          - 'coll_selects' *array* - a list of lists, each containing the collections selects to display

          - 'd1y, d2y, d1m, d2m, d1d, d2d' *int* - the search between dates

          - 'dt' *string* - the dates' types (creation dates, modification dates)

          - 'sort_fields' *array* - the select information for the sort fields

          - 'sf' *string* - the currently selected sort field

          - 'so' *string* - the currently selected sort order ("a" or "d")

          - 'ranks' *array* - ranking methods

          - 'rm' *string* - selected ranking method

          - 'sc' *string* - split by collection or not

          - 'rg' *string* - selected results/page

          - 'formats' *array* - available output formats

          - 'of' *string* - the selected output format

          - 'pl' *string* - `limit to' search pattern

          - show_colls *bool* - propose coll selection box?

          - show_title *bool* show cc_intl in page title?
        """

        # load the right message language
        _ = gettext_set_language(ln)


        # These are hidden fields the user does not manipulate
        # directly
        if aas == -1:
            argd = drop_default_urlargd({
                'ln': ln, 'aas': aas,
                'ot': ot, 'sp': sp, 'ec': ec,
                }, self.search_results_default_urlargd)
        else:
            argd = drop_default_urlargd({
                'cc': cc, 'ln': ln, 'aas': aas,
                'ot': ot, 'sp': sp, 'ec': ec,
                }, self.search_results_default_urlargd)

        out = ""
        if show_title:
            # display cc name if asked for
            out += '''
            <h1 class="headline">%(ccname)s</h1>''' % {'ccname' : cgi.escape(cc_intl), }

        out += '''
        <form name="search" action="%(siteurl)s/search" method="get">
        ''' % {'siteurl' : CFG_BASE_URL}

        # Only add non-default hidden values
        for field, value in argd.items():
            out += self.tmpl_input_hidden(field, value)

        leadingtext = _("Search")

        if action == 'browse':
            leadingtext = _("Browse")

        if aas == 1:
            # print Advanced Search form:

            # define search box elements:
            out += '''
            <table class="searchbox advancedsearch">
             <thead>
              <tr>
               <th colspan="3" class="searchboxheader">
                %(leading)s:
               </th>
              </tr>
             </thead>
             <tbody>
              <tr valign="top" style="white-space:nowrap;">
                <td class="searchboxbody">%(matchbox1)s
                  <input type="text" name="p1" size="%(sizepattern)d" value="%(p1)s" class="advancedsearchfield"/>
                </td>
                <td class="searchboxbody">%(searchwithin1)s</td>
                <td class="searchboxbody">%(andornot1)s</td>
              </tr>
              <tr valign="top">
                <td class="searchboxbody">%(matchbox2)s
                  <input type="text" name="p2" size="%(sizepattern)d" value="%(p2)s" class="advancedsearchfield"/>
                </td>
                <td class="searchboxbody">%(searchwithin2)s</td>
                <td class="searchboxbody">%(andornot2)s</td>
              </tr>
              <tr valign="top">
                <td class="searchboxbody">%(matchbox3)s
                  <input type="text" name="p3" size="%(sizepattern)d" value="%(p3)s" class="advancedsearchfield"/>
                </td>
                <td class="searchboxbody">%(searchwithin3)s</td>
                <td class="searchboxbody"  style="white-space:nowrap;">
                  <input class="formbutton" type="submit" name="action_search" value="%(search)s" />
                  <!-- <input class="formbutton" type="submit" name="action_browse" value="%(browse)s" />&nbsp; -->
                </td>
              </tr>
              <tr valign="bottom">
                <td colspan="3" align="right" class="searchboxbody">
                  <small>
                    <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a> ::
                    %(simple_search)s
                  </small>
                </td>
              </tr>
             </tbody>
            </table>
            ''' % {
                'simple_search': create_html_link(self.build_search_url(p=p1, f=f1, rm=rm, cc=cc, ln=ln, jrec=jrec, rg=rg),
                                                  {}, _("Simple Search")),

                'leading' : leadingtext,
                'sizepattern' : CFG_WEBSEARCH_ADVANCEDSEARCH_PATTERN_BOX_WIDTH,
                'matchbox1' : self.tmpl_matchtype_box('m1', m1, ln=ln),
                'p1' : cgi.escape(p1, 1),
                'searchwithin1' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f1',
                                  selected=f1,
                                  values=self._add_mark_to_field(value=f1, fields=fieldslist, ln=ln)
                                ),
              'andornot1' : self.tmpl_andornot_box(
                                  name='op1',
                                  value=op1,
                                  ln=ln
                                ),
              'matchbox2' : self.tmpl_matchtype_box('m2', m2, ln=ln),
              'p2' : cgi.escape(p2, 1),
              'searchwithin2' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f2',
                                  selected=f2,
                                  values=self._add_mark_to_field(value=f2, fields=fieldslist, ln=ln)
                                ),
              'andornot2' : self.tmpl_andornot_box(
                                  name='op2',
                                  value=op2,
                                  ln=ln
                                ),
              'matchbox3' : self.tmpl_matchtype_box('m3', m3, ln=ln),
              'p3' : cgi.escape(p3, 1),
              'searchwithin3' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f3',
                                  selected=f3,
                                  values=self._add_mark_to_field(value=f3, fields=fieldslist, ln=ln)
                                ),
              'search' : _("Search"),
              'browse' : _("Browse"),
              'siteurl' : CFG_BASE_URL,
              'ln' : ln,
              'langlink': '?ln=' + ln,
              'search_tips': _("Search Tips")
            }
        elif aas == 0:
            # print Simple Search form:
            out += '''
            <table class="searchbox simplesearch">
             <thead>
              <tr>
               <th colspan="3" class="searchboxheader">
                %(leading)s:
               </th>
              </tr>
             </thead>
             <tbody>
              <tr valign="top">
                <td class="searchboxbody"><input type="text" name="p" size="%(sizepattern)d" value="%(p)s" class="simplesearchfield"/></td>
                <td class="searchboxbody">%(searchwithin)s</td>
                <td class="searchboxbody">
                  <input class="formbutton" type="submit" name="action_search" value="%(search)s" />
                  <!-- <input class="formbutton" type="submit" name="action_browse" value="%(browse)s" />&nbsp; -->
                </td>
              </tr>
              <tr valign="bottom">
                <td colspan="3" align="right" class="searchboxbody">
                  <small>
                    <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a> ::
                    %(advanced_search)s
                  </small>
                </td>
              </tr>
             </tbody>
            </table>
            ''' % {
              'advanced_search': create_html_link(self.build_search_url(p1=p,
                                                                        f1=f,
                                                                        rm=rm,
                                                                        aas=max(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES),
                                                                        cc=cc,
                                                                        jrec=jrec,
                                                                        ln=ln,
                                                                        rg=rg),
                                                  {}, _("Advanced Search")),

              'leading' : leadingtext,
              'sizepattern' : CFG_WEBSEARCH_SIMPLESEARCH_PATTERN_BOX_WIDTH,
              'p' : cgi.escape(p, 1),
              'searchwithin' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f',
                                  selected=f,
                                  values=self._add_mark_to_field(value=f, fields=fieldslist, ln=ln)
                                ),
              'search' : _("Search"),
              'browse' : _("Browse"),
              'siteurl' : CFG_BASE_URL,
              'ln' : ln,
              'langlink': '?ln=' + ln,
              'search_tips': _("Search Tips")
            }
        else:
            # EXPERIMENTAL
            # print light search form:
            search_in = ''
            if cc_intl != CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME):
                search_in = '''
            <input type="radio" name="cc" value="%(collection_id)s" id="searchCollection" checked="checked"/>
            <label for="searchCollection">%(search_in_collection_name)s</label>
            <input type="radio" name="cc" value="%(root_collection_name)s" id="searchEverywhere" />
            <label for="searchEverywhere">%(search_everywhere)s</label>
            ''' % {'search_in_collection_name': _("Search in %(x_collection_name)s") % \
                  {'x_collection_name': cgi.escape(cc_intl)},
                  'collection_id': cc,
                  'root_collection_name': CFG_SITE_NAME,
                  'search_everywhere': _("Search everywhere")}
            out += '''
            <table class="searchbox lightsearch">
              <tr valign="top">
                <td class="searchboxbody"><input type="text" name="p" size="%(sizepattern)d" value="%(p)s" class="lightsearchfield"/></td>
                <td class="searchboxbody">
                  <input class="formbutton" type="submit" name="action_search" value="%(search)s" />
                </td>
                <td class="searchboxbody" align="left" rowspan="2" valign="top">
                  <small><small>
                  <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a><br/>
                  %(advanced_search)s
                </td>
              </tr>
            </table>
            <small>%(search_in)s</small>
            ''' % {
              'sizepattern' : CFG_WEBSEARCH_LIGHTSEARCH_PATTERN_BOX_WIDTH,
              'advanced_search': create_html_link(self.build_search_url(p1=p,
                                                                        f1=f,
                                                                        rm=rm,
                                                                        aas=max(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES),
                                                                        cc=cc,
                                                                        jrec=jrec,
                                                                        ln=ln,
                                                                        rg=rg),
                                                  {}, _("Advanced Search")),

              'leading' : leadingtext,
              'p' : cgi.escape(p, 1),
              'searchwithin' : self.tmpl_searchwithin_select(
                                  ln=ln,
                                  fieldname='f',
                                  selected=f,
                                  values=self._add_mark_to_field(value=f, fields=fieldslist, ln=ln)
                                ),
              'search' : _("Search"),
              'browse' : _("Browse"),
              'siteurl' : CFG_BASE_URL,
              'ln' : ln,
              'langlink': '?ln=' + ln,
              'search_tips': _("Search Tips"),
              'search_in': search_in
            }
        ## secondly, print Collection(s) box:

        if show_colls and aas > -1:
            # display collections only if there is more than one
            selects = ''
            for sel in coll_selects:
                selects += self.tmpl_select(fieldname='c', values=sel)

            out += """
                <table class="searchbox">
                 <thead>
                  <tr>
                   <th colspan="3" class="searchboxheader">
                    %(leading)s %(msg_coll)s:
                   </th>
                  </tr>
                 </thead>
                 <tbody>
                  <tr valign="bottom">
                   <td valign="top" class="searchboxbody">
                     %(colls)s
                   </td>
                  </tr>
                 </tbody>
                </table>
                 """ % {
                   'leading' : leadingtext,
                   'msg_coll' : _("collections"),
                   'colls' : selects,
                 }

        ## thirdly, print search limits, if applicable:
        if action != _("Browse") and pl:
            out += """<table class="searchbox">
                       <thead>
                        <tr>
                          <th class="searchboxheader">
                            %(limitto)s
                          </th>
                        </tr>
                       </thead>
                       <tbody>
                        <tr valign="bottom">
                          <td class="searchboxbody">
                           <input type="text" name="pl" size="%(sizepattern)d" value="%(pl)s" />
                          </td>
                        </tr>
                       </tbody>
                      </table>""" % {
                        'limitto' : _("Limit to:"),
                        'sizepattern' : CFG_WEBSEARCH_ADVANCEDSEARCH_PATTERN_BOX_WIDTH,
                        'pl' : cgi.escape(pl, 1),
                      }

        ## fourthly, print from/until date boxen, if applicable:
        if action == _("Browse") or (d1y == 0 and d1m == 0 and d1d == 0 and d2y == 0 and d2m == 0 and d2d == 0):
            pass # do not need it
        else:
            cell_6_a = self.tmpl_inputdatetype(dt, ln) + self.tmpl_inputdate("d1", ln, d1y, d1m, d1d)
            cell_6_b = self.tmpl_inputdate("d2", ln, d2y, d2m, d2d)
            out += """<table class="searchbox">
                       <thead>
                        <tr>
                          <th class="searchboxheader">
                            %(added)s
                          </th>
                          <th class="searchboxheader">
                            %(until)s
                          </th>
                        </tr>
                       </thead>
                       <tbody>
                        <tr valign="bottom">
                          <td class="searchboxbody">%(added_or_modified)s %(date1)s</td>
                          <td class="searchboxbody">%(date2)s</td>
                        </tr>
                       </tbody>
                      </table>""" % {
                        'added' : _("Added/modified since:"),
                        'until' : _("until:"),
                        'added_or_modified': self.tmpl_inputdatetype(dt, ln),
                        'date1' : self.tmpl_inputdate("d1", ln, d1y, d1m, d1d),
                        'date2' : self.tmpl_inputdate("d2", ln, d2y, d2m, d2d),
                      }

        ## fifthly, print Display results box, including sort/rank, formats, etc:
        if action != _("Browse") and aas > -1:

            rgs = []
            for i in [10, 25, 50, 100, 250, 500]:
                if i <= CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS:
                    rgs.append({ 'value' : i, 'text' : "%d %s" % (i, _("results"))})
            # enrich sort fields list if we are sorting by some MARC tag:
            sort_fields = self._add_mark_to_field(value=sf, fields=sort_fields, ln=ln)
            # create sort by HTML box:
            out += """<table class="searchbox">
                 <thead>
                  <tr>
                   <th class="searchboxheader">
                    %(sort_by)s
                   </th>
                   <th class="searchboxheader">
                    %(display_res)s
                   </th>
                   <th class="searchboxheader">
                    %(out_format)s
                   </th>
                  </tr>
                 </thead>
                 <tbody>
                  <tr valign="bottom">
                   <td class="searchboxbody">
                     %(select_sf)s %(select_so)s %(select_rm)s
                   </td>
                   <td class="searchboxbody">
                     %(select_rg)s %(select_sc)s
                   </td>
                   <td class="searchboxbody">%(select_of)s</td>
                  </tr>
                 </tbody>
                </table>""" % {
                  'sort_by' : _("Sort by:"),
                  'display_res' : _("Display results:"),
                  'out_format' : _("Output format:"),
                  'select_sf' : self.tmpl_select(fieldname='sf', values=sort_fields, selected=sf, css_class='address'),
                  'select_so' : self.tmpl_select(fieldname='so', values=[{
                                    'value' : 'a',
                                    'text' : _("asc.")
                                  }, {
                                    'value' : 'd',
                                    'text' : _("desc.")
                                  }], selected=so, css_class='address'),
                  'select_rm' : self.tmpl_select(fieldname='rm', values=ranks, selected=rm, css_class='address'),
                  'select_rg' : self.tmpl_select(fieldname='rg', values=rgs, selected=rg, css_class='address'),
                  'select_sc' : self.tmpl_select(fieldname='sc', values=[{
                                    'value' : 0,
                                    'text' : _("single list")
                                  }, {
                                    'value' : 1,
                                    'text' : _("split by collection")
                                  }], selected=sc, css_class='address'),
                  'select_of' : self.tmpl_select(
                                  fieldname='of',
                                  selected=of,
                                  values=self._add_mark_to_field(value=of, fields=formats, chars=3, ln=ln),
                                  css_class='address'),
                }

        ## last but not least, print end of search box:
        out += """</form>"""
        return out
