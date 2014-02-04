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
    CFG_WEBSEARCH_SIMPLESEARCH_PATTERN_BOX_WIDTH, CFG_WEBSEARCH_SPLIT_BY_COLLECTION, CFG_SITE_URL, CFG_SITE_RECORD
from invenio.urlutils import drop_default_urlargd, create_html_link
from invenio.messages import gettext_set_language
from invenio.websearch_external_collections import external_collection_get_state, get_external_collection_engine
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

    def tmpl_nbrecs_info(self, number, prolog=None, epilog=None, ln=CFG_SITE_LANG, none_yet_support=False):
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

        if number is 0 and none_yet_support:
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
                    <!-- <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a> :: -->
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
                    <!-- <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a> :: -->
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
                  <!-- <a href="%(siteurl)s/help/search-tips%(langlink)s">%(search_tips)s</a><br/> -->
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
                   'msg_coll' : _("journals or publishers"),
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
                   <!--
                   <th class="searchboxheader">
                    %(sort_by)s
                   </th> -->
                   <th class="searchboxheader">
                    %(display_res)s
                   </th>
                   <!--
                   <th class="searchboxheader">
                    %(out_format)s
                   </th> -->
                  </tr>
                 </thead>
                 <tbody>
                  <tr valign="bottom">
                   <!--
                   <td class="searchboxbody">
                     %(select_sf)s %(select_so)s %(select_rm)s
                   </td> -->
                   <td class="searchboxbody">
                     %(select_rg)s %(select_sc)s
                   </td>
                   <!--
                   <td class="searchboxbody">%(select_of)s</td> -->
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
                                    'text' : _("split by publisher/journal")
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

    def tmpl_searchfor_simple(self, ln, collection_id, collection_name, record_count, middle_option):
        """Produces simple *Search for* box for the current collection.

        Parameters:

          - 'ln' *string* - *str* The language to display

          - 'collection_id' - *str* The collection id

          - 'collection_name' - *str* The collection name in current language

          - 'record_count' - *str* Number of records in this collection

          - 'middle_option' *string* - HTML code for the options (any field, specific fields ...)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''
        <!--create_searchfor_simple()-->
        '''

        argd = drop_default_urlargd({'ln': ln, 'cc': collection_id, 'sc': CFG_WEBSEARCH_SPLIT_BY_COLLECTION},
                                    self.search_results_default_urlargd)

        # Only add non-default hidden values
        for field, value in argd.items():
            out += self.tmpl_input_hidden(field, value)


        header = _("Search %s records for:") % \
                 self.tmpl_nbrecs_info(record_count, "", "")
        asearchurl = self.build_search_interface_url(c=collection_id,
                                                     aas=max(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES),
                                                     ln=ln)
        # print commentary start:
        out += '''
        <table class="searchbox simplesearch">
         <thead>
          <tr align="left">
           <th colspan="3" class="searchboxheader">%(header)s</th>
          </tr>
         </thead>
         <tbody>
          <tr valign="baseline">
           <td class="searchboxbody" align="left"><input type="text" name="p" size="%(sizepattern)d" value="" class="simplesearchfield"/></td>
           <td class="searchboxbody" align="left">%(middle_option)s</td>
           <td class="searchboxbody" align="left">
             <input class="formbutton" type="submit" name="action_search" value="%(msg_search)s" />
             <!-- <input class="formbutton" type="submit" name="action_browse" value="%(msg_browse)s" /> --></td>
          </tr>
          <tr valign="baseline">
           <td class="searchboxbody" colspan="3" align="right">
             <small>
               <!-- <a href="%(siteurl)s/help/search-tips%(langlink)s">%(msg_search_tips)s</a> :: -->
               %(asearch)s
             </small>
           </td>
          </tr>
         </tbody>
        </table>
        <!--/create_searchfor_simple()-->
        ''' % {'ln' : ln,
               'sizepattern' : CFG_WEBSEARCH_SIMPLESEARCH_PATTERN_BOX_WIDTH,
               'langlink': '?ln=' + ln,
               'siteurl' : CFG_BASE_URL,
               'asearch' : create_html_link(asearchurl, {}, _('Advanced Search')),
               'header' : header,
               'middle_option' : middle_option,
               'msg_search' : _('Search'),
               'msg_browse' : _('Browse'),
               'msg_search_tips' : _('Search Tips')}

        return out

    def tmpl_searchfor_advanced(self,
                                ln, # current language
                                collection_id,
                                collection_name,
                                record_count,
                                middle_option_1, middle_option_2, middle_option_3,
                                searchoptions,
                                sortoptions,
                                rankoptions,
                                displayoptions,
                                formatoptions
                                ):
        """
          Produces advanced *Search for* box for the current collection.

          Parameters:

            - 'ln' *string* - The language to display

            - 'middle_option_1' *string* - HTML code for the first row of options (any field, specific fields ...)

            - 'middle_option_2' *string* - HTML code for the second row of options (any field, specific fields ...)

            - 'middle_option_3' *string* - HTML code for the third row of options (any field, specific fields ...)

            - 'searchoptions' *string* - HTML code for the search options

            - 'sortoptions' *string* - HTML code for the sort options

            - 'rankoptions' *string* - HTML code for the rank options

            - 'displayoptions' *string* - HTML code for the display options

            - 'formatoptions' *string* - HTML code for the format options

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''
        <!--create_searchfor_advanced()-->
        '''

        argd = drop_default_urlargd({'ln': ln, 'aas': 1, 'cc': collection_id, 'sc': CFG_WEBSEARCH_SPLIT_BY_COLLECTION},
                                    self.search_results_default_urlargd)

        # Only add non-default hidden values
        for field, value in argd.items():
            out += self.tmpl_input_hidden(field, value)


        header = _("Search %s records for") % \
                 self.tmpl_nbrecs_info(record_count, "", "")
        header += ':'
        ssearchurl = self.build_search_interface_url(c=collection_id, aas=min(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES), ln=ln)

        out += '''
        <table class="searchbox advancedsearch">
         <thead>
          <tr>
           <th class="searchboxheader" colspan="3">%(header)s</th>
          </tr>
         </thead>
         <tbody>
          <tr valign="bottom">
            <td class="searchboxbody" style="white-space: nowrap;">
                %(matchbox_m1)s<input type="text" name="p1" size="%(sizepattern)d" value="" class="advancedsearchfield"/>
            </td>
            <td class="searchboxbody" style="white-space: nowrap;">%(middle_option_1)s</td>
            <td class="searchboxbody">%(andornot_op1)s</td>
          </tr>
          <tr valign="bottom">
            <td class="searchboxbody" style="white-space: nowrap;">
                %(matchbox_m2)s<input type="text" name="p2" size="%(sizepattern)d" value="" class="advancedsearchfield"/>
            </td>
            <td class="searchboxbody">%(middle_option_2)s</td>
            <td class="searchboxbody">%(andornot_op2)s</td>
          </tr>
          <tr valign="bottom">
            <td class="searchboxbody" style="white-space: nowrap;">
                %(matchbox_m3)s<input type="text" name="p3" size="%(sizepattern)d" value="" class="advancedsearchfield"/>
            </td>
            <td class="searchboxbody">%(middle_option_3)s</td>
            <td class="searchboxbody" style="white-space: nowrap;">
              <input class="formbutton" type="submit" name="action_search" value="%(msg_search)s" />
              <input class="formbutton" type="submit" name="action_browse" value="%(msg_browse)s" /></td>
          </tr>
          <tr valign="bottom">
            <td colspan="3" class="searchboxbody" align="right">
              <small>
                <!-- <a href="%(siteurl)s/help/search-tips%(langlink)s">%(msg_search_tips)s</a> :: -->
                %(ssearch)s
              </small>
            </td>
          </tr>
         </tbody>
        </table>
        <!-- @todo - more imports -->
        ''' % {'ln' : ln,
               'sizepattern' : CFG_WEBSEARCH_ADVANCEDSEARCH_PATTERN_BOX_WIDTH,
               'langlink': '?ln=' + ln,
               'siteurl' : CFG_BASE_URL,
               'ssearch' : create_html_link(ssearchurl, {}, _("Simple Search")),
               'header' : header,

               'matchbox_m1' : self.tmpl_matchtype_box('m1', ln=ln),
               'middle_option_1' : middle_option_1,
               'andornot_op1' : self.tmpl_andornot_box('op1', ln=ln),

               'matchbox_m2' : self.tmpl_matchtype_box('m2', ln=ln),
               'middle_option_2' : middle_option_2,
               'andornot_op2' : self.tmpl_andornot_box('op2', ln=ln),

               'matchbox_m3' : self.tmpl_matchtype_box('m3', ln=ln),
               'middle_option_3' : middle_option_3,

               'msg_search' : _("Search"),
               'msg_browse' : _("Browse"),
               'msg_search_tips' : _("Search Tips")}

        if (searchoptions):
            out += """<table class="searchbox">
                      <thead>
                       <tr>
                         <th class="searchboxheader">
                           %(searchheader)s
                         </th>
                       </tr>
                      </thead>
                      <tbody>
                       <tr valign="bottom">
                        <td class="searchboxbody">%(searchoptions)s</td>
                       </tr>
                      </tbody>
                     </table>""" % {
                       'searchheader' : _("Search options:"),
                       'searchoptions' : searchoptions
                     }

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
                      <td class="searchboxbody">%(added_or_modified)s %(date_added)s</td>
                      <td class="searchboxbody">%(date_until)s</td>
                    </tr>
                   </tbody>
                  </table>
                  <table class="searchbox">
                   <thead>
                    <tr>
                      <!--
                      <th class="searchboxheader">
                        %(msg_sort)s
                      </th> -->
                      <th class="searchboxheader">
                        %(msg_display)s
                      </th>
                      <!--
                      <th class="searchboxheader">
                        %(msg_format)s
                      </th> -->
                    </tr>
                   </thead>
                   <tbody>
                    <tr valign="bottom">
                      <!-- <td class="searchboxbody">%(sortoptions)s %(rankoptions)s</td> -->
                      <td class="searchboxbody">%(displayoptions)s</td>
                      <!-- <td class="searchboxbody">%(formatoptions)s</td> -->
                    </tr>
                   </tbody>
                  </table>
                  <!--/create_searchfor_advanced()-->
              """ % {

                    'added' : _("Added/modified since:"),
                    'until' : _("until:"),
                    'added_or_modified': self.tmpl_inputdatetype(ln=ln),
                    'date_added' : self.tmpl_inputdate("d1", ln=ln),
                    'date_until' : self.tmpl_inputdate("d2", ln=ln),

                    'msg_sort' : _("Sort by:"),
                    'msg_display' : _("Display results:"),
                    'msg_format' : _("Output format:"),
                    'sortoptions' : sortoptions,
                    'rankoptions' : rankoptions,
                    'displayoptions' : displayoptions,
                    'formatoptions' : formatoptions
                  }
        return out

    def tmpl_narrowsearch(self, aas, ln, type, father,
                          has_grandchildren, sons, display_grandsons,
                          grandsons):

        """
        Creates list of collection descendants of type *type* under title *title*.
        If aas==1, then links to Advanced Search interfaces; otherwise Simple Search.
        Suitable for 'Narrow search' and 'Focus on' boxes.

        Parameters:

          - 'aas' *bool* - Should we display an advanced search box?

          - 'ln' *string* - The language to display

          - 'type' *string* - The type of the produced box (virtual collections or normal collections)

          - 'father' *collection* - The current collection

          - 'has_grandchildren' *bool* - If the current collection has grand children

          - 'sons' *list* - The list of the sub-collections (first level)

          - 'display_grandsons' *bool* - If the grand children collections should be displayed (2 level deep display)

          - 'grandsons' *list* - The list of sub-collections (second level)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        title = father.get_collectionbox_name(ln, type)

        if has_grandchildren:
            style_prolog = "<strong>"
            style_epilog = "</strong>"
        else:
            style_prolog = ""
            style_epilog = ""

        out = """<table class="%(narrowsearchbox)s">
                   <thead>
                    <tr>
                     <th colspan="2" align="left" class="%(narrowsearchbox)sheader">
                      %(title)s
                     </th>
                    </tr>
                   </thead>
                   <tbody>""" % {'title' : title,
                                 'narrowsearchbox': {'r': 'narrowsearchbox',
                                                     'v': 'focusonsearchbox'}[type]}
        # iterate through sons:
        i = 0
        for son in sons:
            out += """<tr><td class="%(narrowsearchbox)sbody" valign="top">""" % \
                   { 'narrowsearchbox': {'r': 'narrowsearchbox',
                                         'v': 'focusonsearchbox'}[type]}

            if type == 'r':
                if son.restricted_p() and son.restricted_p() != father.restricted_p():
                    out += """<input type="checkbox" name="c" value="%(name)s" /></td>""" % {'name' : cgi.escape(son.name) }
                # hosted collections are checked by default only when configured so
                elif str(son.dbquery).startswith("hostedcollection:"):
                    external_collection_engine = get_external_collection_engine(str(son.name))
                    if external_collection_engine and external_collection_engine.selected_by_default:
                        out += """<input type="checkbox" name="c" value="%(name)s" checked="checked" /></td>""" % {'name' : cgi.escape(son.name) }
                    elif external_collection_engine and not external_collection_engine.selected_by_default:
                        out += """<input type="checkbox" name="c" value="%(name)s" /></td>""" % {'name' : cgi.escape(son.name) }
                    else:
                        # strangely, the external collection engine was never found. In that case,
                        # why was the hosted collection here in the first place?
                        out += """<input type="checkbox" name="c" value="%(name)s" /></td>""" % {'name' : cgi.escape(son.name) }
                else:
                    out += """<input type="checkbox" name="c" value="%(name)s" checked="checked" /></td>""" % {'name' : cgi.escape(son.name) }
            else:
                out += '</td>'
            out += """<td valign="top">%(link)s%(recs)s """ % {
                'link': son.nbrecs and create_html_link(self.build_search_interface_url(c=son.name, ln=ln, aas=aas),
                                         {}, style_prolog + cgi.escape(son.get_name(ln)) + style_epilog) or style_prolog + cgi.escape(son.get_name(ln)) + style_epilog,
                'recs' : self.tmpl_nbrecs_info(son.nbrecs, ln=ln, none_yet_support=True)}

            # the following prints the "external collection" arrow just after the name and
            # number of records of the hosted collection
            # 1) we might want to make the arrow work as an anchor to the hosted collection as well.
            # That would probably require a new separate function under invenio.urlutils
            # 2) we might want to place the arrow between the name and the number of records of the hosted collection
            # That would require to edit/separate the above out += ...
            if type == 'r':
                if str(son.dbquery).startswith("hostedcollection:"):
                    out += """<img src="%(siteurl)s/img/external-icon-light-8x8.gif" border="0" alt="%(name)s"/>""" % \
                           { 'siteurl' : CFG_BASE_URL, 'name' : cgi.escape(son.name), }

            if son.restricted_p():
                out += """ <small class="warning">[%(msg)s]</small> """ % { 'msg' : _("restricted") }
            if display_grandsons and len(grandsons[i]):
                # iterate trough grandsons:
                out += """<br />"""
                for grandson in grandsons[i]:
                    out += """ <small>%(link)s%(nbrec)s</small> """ % {
                        'link': grandson.nbrecs and create_html_link(self.build_search_interface_url(c=grandson.name, ln=ln, aas=aas),
                                                 {},
                                                 cgi.escape(grandson.get_name(ln))) or cgi.escape(grandson.get_name(ln)),
                        'nbrec' : self.tmpl_nbrecs_info(grandson.nbrecs, ln=ln, none_yet_support=True)}
                    # the following prints the "external collection" arrow just after the name and
                    # number of records of the hosted collection
                    # Some relatives comments have been made just above
                    if type == 'r':
                        if str(grandson.dbquery).startswith("hostedcollection:"):
                            out += """<img src="%(siteurl)s/img/external-icon-light-8x8.gif" border="0" alt="%(name)s"/>""" % \
                                    { 'siteurl' : CFG_BASE_URL, 'name' : cgi.escape(grandson.name), }

            out += """</td></tr>"""
            i += 1
        out += "</tbody></table>"

        return out

    def tmpl_record_links(self, recid, ln, sf='', so='d', sp='', rm=''):
        """
          Displays the *More info* and *Find similar* links for a record

        Parameters:

          - 'ln' *string* - The language to display

          - 'recid' *string* - the id of the displayed record
        """

        return ""

    def tmpl_print_record_brief_links(self, ln, recID, sf='', so='d', sp='', rm='', display_claim_link=False, display_edit_link=False):
        """Displays links for brief record on-the-fly

        Parameters:

          - 'ln' *string* - The language to display

          - 'recID' *int* - The record id
        """
        from invenio.webcommentadminlib import get_nb_reviews, get_nb_comments

        # load the right message language
        _ = gettext_set_language(ln)

        out = '<div class="moreinfo">'

        if display_edit_link:
            out += '<span class="moreinfo"> - %s</span>' % \
                    create_html_link('%s/%s/edit/?ln=%s#state=edit&recid=%s' % \
                                     (CFG_SITE_URL, CFG_SITE_RECORD, ln, str(recID)),
                                     {},
                                     link_label=_("Edit record"),
                                     linkattrd={'class': "moreinfo"})
        out += '</div>'
        return out

    def tmpl_searchfor_light(self, ln, collection_id, collection_name, record_count,
                             example_search_queries): # EXPERIMENTAL
        """Produces light *Search for* box for the current collection.

        Parameters:

          - 'ln' *string* - *str* The language to display

          - 'collection_id' - *str* The collection id

          - 'collection_name' - *str* The collection name in current language

          - 'example_search_queries' - *list* List of search queries given as example for this collection
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''
        <!--create_searchfor_light()-->
        '''

        argd = drop_default_urlargd({'ln': ln, 'sc': CFG_WEBSEARCH_SPLIT_BY_COLLECTION},
                                    self.search_results_default_urlargd)

        # Only add non-default hidden values
        for field, value in argd.items():
            out += self.tmpl_input_hidden(field, value)


        header = _("Search %s records for:") % \
                 self.tmpl_nbrecs_info(record_count, "", "")
        asearchurl = self.build_search_interface_url(c=collection_id,
                                                     aas=max(CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES),
                                                     ln=ln)

        # Build example of queries for this collection
        example_search_queries_links = [create_html_link(self.build_search_url(p=example_query,
                                                                               ln=ln,
                                                                               aas= -1,
                                                                               c=collection_id),
                                                         {},
                                                         cgi.escape(example_query),
                                                         {'class': 'examplequery'}) \
                                        for example_query in example_search_queries]
        example_query_html = ''
        if len(example_search_queries) > 0:
            example_query_link = example_search_queries_links[0]

            # offers more examples if possible
            more = ''
            if len(example_search_queries_links) > 1:
                more = '''
                <script type="text/javascript">
                function toggle_more_example_queries_visibility(){
                    var more = document.getElementById('more_example_queries');
                    var link = document.getElementById('link_example_queries');
                    var sep = document.getElementById('more_example_sep');
                    if (more.style.display=='none'){
                        more.style.display = '';
                        link.innerHTML = "%(show_less)s"
                        link.style.color = "rgb(204,0,0)";
                        sep.style.display = 'none';
                    } else {
                        more.style.display = 'none';
                        link.innerHTML = "%(show_more)s"
                        link.style.color = "rgb(0,0,204)";
                        sep.style.display = '';
                    }
                    return false;
                }
                </script>
                <span id="more_example_queries" style="display:none;text-align:right"><br/>%(more_example_queries)s<br/></span>
                <a id="link_example_queries" href="#" onclick="toggle_more_example_queries_visibility()" style="display:none"></a>
                <script type="text/javascript">
                    var link = document.getElementById('link_example_queries');
                    var sep = document.getElementById('more_example_sep');
                    link.style.display = '';
                    link.innerHTML = "%(show_more)s";
                    sep.style.display = '';
                </script>
                ''' % {'more_example_queries': '<br/>'.join(example_search_queries_links[1:]),
                       'show_less':_("less"),
                       'show_more':_("more")}

            example_query_html += '''<p style="text-align:right;margin:0px;">
            %(example)s<span id="more_example_sep" style="display:none;">&nbsp;&nbsp;::&nbsp;</span>%(more)s
            </p>
            ''' % {'example': _("Example: %(x_sample_search_query)s") % \
                   {'x_sample_search_query': example_query_link},
                   'more': more}

        # display options to search in current collection or everywhere
        search_in = ''
        if collection_name != CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME):
            search_in += '''
           <input type="radio" name="cc" value="%(collection_id)s" id="searchCollection" checked="checked"/>
           <label for="searchCollection">%(search_in_collection_name)s</label>
           <input type="radio" name="cc" value="%(root_collection_name)s" id="searchEverywhere" />
           <label for="searchEverywhere">%(search_everywhere)s</label>
           ''' % {'search_in_collection_name': _("Search in %(x_collection_name)s") % \
                  {'x_collection_name': collection_name},
                  'collection_id': collection_id,
                  'root_collection_name': CFG_SITE_NAME,
                  'search_everywhere': _("Search everywhere")}

        # print commentary start:
        out += '''
        <table class="searchbox lightsearch">
         <tbody>
          <tr valign="baseline">
           <td class="searchboxbody" align="right"><input type="text" name="p" size="%(sizepattern)d" value="" class="lightsearchfield"/><br/>
             <small><small>%(example_query_html)s</small></small>
           </td>
           <td class="searchboxbody" align="left">
             <input class="formbutton" type="submit" name="action_search" value="%(msg_search)s" />
           </td>
           <td class="searchboxbody" align="left" rowspan="2" valign="top">
             <small><small>
             <!-- <a href="%(siteurl)s/help/search-tips%(langlink)s">%(msg_search_tips)s</a><br/> -->
             %(asearch)s
             </small></small>
           </td>
          </tr></table>
          <!--<tr valign="baseline">
           <td class="searchboxbody" colspan="2" align="left">
             <small>
               --><small>%(search_in)s</small><!--
             </small>
           </td>
          </tr>
         </tbody>
        </table>-->
        <!--/create_searchfor_light()-->
        ''' % {'ln' : ln,
               'sizepattern' : CFG_WEBSEARCH_LIGHTSEARCH_PATTERN_BOX_WIDTH,
               'langlink': '?ln=' + ln,
               'siteurl' : CFG_BASE_URL,
               'asearch' : create_html_link(asearchurl, {}, _('Advanced Search')),
               'header' : header,
               'msg_search' : _('Search'),
               'msg_browse' : _('Browse'),
               'msg_search_tips' : _('Search Tips'),
               'search_in': search_in,
               'example_query_html': example_query_html}

        return out
