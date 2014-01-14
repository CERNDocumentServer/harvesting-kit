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
