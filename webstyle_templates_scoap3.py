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
WebStyle templates for SCOAP3
"""
import cgi

from invenio.config import (CFG_SITE_LANG,
                            CFG_SITE_NAME,
                            CFG_BASE_URL,
                            CFG_INSPIRE_SITE,
                            CFG_SITE_RECORD,
                            CFG_SITE_NAME_INTL,
                            CFG_SITE_SECURE_URL,
                            CFG_SITE_SUPPORT_EMAIL,
                            CFG_SITE_URL,
                            CFG_WEBLINKBACK_TRACKBACK_ENABLED,
                            CFG_WEBSTYLE_INSPECT_TEMPLATES,
                            CFG_WEBSTYLE_TEMPLATE_SKIN,
                            CFG_VERSION)
from invenio.messages import gettext_set_language, is_language_rtl
from invenio.dateutils import convert_datecvs_to_datestruct, convert_datestruct_to_dategui
from invenio.webstyle_templates import Template as DefaultTemplate

class Template(DefaultTemplate):

    def tmpl_pageheader(self, req, ln=CFG_SITE_LANG, headertitle="",
                        description="", keywords="", userinfobox="",
                        useractivities_menu="", adminactivities_menu="",
                        navtrailbox="", pageheaderadd="", uid=0,
                        secure_page_p=0, navmenuid="admin", metaheaderadd="",
                        rssurl=CFG_BASE_URL+"/rss", body_css_classes=None):

        """Creates a page header

           Parameters:

          - 'ln' *string* - The language to display

          - 'headertitle' *string* - the title of the HTML page, not yet escaped for HTML

          - 'description' *string* - description goes to the metadata in the header of the HTML page,
                                     not yet escaped for HTML

          - 'keywords' *string* - keywords goes to the metadata in the header of the HTML page,
                                  not yet escaped for HTML

          - 'userinfobox' *string* - the HTML code for the user information box

          - 'useractivities_menu' *string* - the HTML code for the user activities menu

          - 'adminactivities_menu' *string* - the HTML code for the admin activities menu

          - 'navtrailbox' *string* - the HTML code for the navigation trail box

          - 'pageheaderadd' *string* - additional page header HTML code

          - 'uid' *int* - user ID

          - 'secure_page_p' *int* (0 or 1) - are we to use HTTPS friendly page elements or not?

          - 'navmenuid' *string* - the id of the navigation item to highlight for this page

          - 'metaheaderadd' *string* - list of further tags to add to the <HEAD></HEAD> part of the page

          - 'rssurl' *string* - the url of the RSS feed for this page

          - 'body_css_classes' *list* - list of classes to add to the body tag

           Output:

          - HTML code of the page headers
        """
        # Including HEPData headers ( Ugly hack but no obvious way to avoid this ...)
        if CFG_INSPIRE_SITE:
            hepDataAdditions = """<script type="text/javascript" src="%s/js/hepdata.js"></script>""" \
            % (CFG_BASE_URL, )
            hepDataAdditions += """<link rel="stylesheet" href="%s/img/hepdata.css" type="text/css" />""" \
            % (CFG_BASE_URL, )
        else:
            hepDataAdditions = ""
        # load the right message language
        _ = gettext_set_language(ln)

        if body_css_classes is None:
            body_css_classes = []
        body_css_classes.append(navmenuid)

        uri = req.unparsed_uri
        headerLinkbackTrackbackLink = ''
        if CFG_WEBLINKBACK_TRACKBACK_ENABLED:
            from invenio.weblinkback_templates import get_trackback_auto_discovery_tag
            # Embed a link in the header to subscribe trackbacks
            # TODO: This hack must be replaced with the introduction of the new web framework
            recordIndexInURI = uri.find('/' + CFG_SITE_RECORD + '/')
            # substring found --> offer trackback link in header
            if recordIndexInURI != -1:
                recid = uri[recordIndexInURI:len(uri)].split('/')[2].split("?")[0] #recid might end with ? for journal records
                headerLinkbackTrackbackLink = get_trackback_auto_discovery_tag(recid)

        if CFG_WEBSTYLE_INSPECT_TEMPLATES:
            inspect_templates_message = '''
<table width="100%%" cellspacing="0" cellpadding="2" border="0">
<tr bgcolor="#aa0000">
<td width="100%%">
<font color="#ffffff">
<strong>
<small>
CFG_WEBSTYLE_INSPECT_TEMPLATES debugging mode is enabled.  Please
hover your mouse pointer over any region on the page to see which
template function generated it.
</small>
</strong>
</font>
</td>
</tr>
</table>
'''
        else:
            inspect_templates_message = ""

        sitename = CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)
        if headertitle == sitename:
            pageheadertitle = headertitle
        else:
            pageheadertitle = headertitle + ' - ' + sitename

        metabase = ""
        stripped_url = CFG_SITE_URL.replace("://", "")
        if not CFG_BASE_URL and '/' in stripped_url:
            metabase = "<base href='%s'>" % (CFG_SITE_URL,)

        out = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="%(ln_iso_639_a)s" xml:lang="%(ln_iso_639_a)s" xmlns:og="http://opengraphprotocol.org/schema/" >
<head>
 <title>%(pageheadertitle)s</title>
 %(metabase)s
 <link rev="made" href="mailto:%(sitesupportemail)s" />
 <link rel="stylesheet" href="%(cssurl)s/img/invenio%(cssskin)s.css" type="text/css" />
 <!--[if lt IE 8]>
    <link rel="stylesheet" type="text/css" href="%(cssurl)s/img/invenio%(cssskin)s-ie7.css" />
 <![endif]-->
 <!--[if gt IE 8]>
    <style type="text/css">div.restrictedflag {filter:none;}</style>
 <![endif]-->
 %(canonical_and_alternate_urls)s
 <link rel="alternate" type="application/rss+xml" title="%(sitename)s RSS" href="%(rssurl)s" />
 <link rel="search" type="application/opensearchdescription+xml" href="%(siteurl)s/opensearchdescription" title="%(sitename)s" />
 <link rel="unapi-server" type="application/xml" title="unAPI" href="%(unAPIurl)s" />
 %(linkbackTrackbackLink)s
 <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
 <meta http-equiv="Content-Language" content="%(ln)s" />
 <meta name="description" content="%(description)s" />
 <meta name="keywords" content="%(keywords)s" />
 <script type="text/javascript" src="%(cssurl)s/js/jquery.min.js"></script>
 %(hepDataAdditions)s
 %(metaheaderadd)s
</head>
<body%(body_css_classes)s lang="%(ln_iso_639_a)s"%(rtl_direction)s>
<div class="pageheader">
%(inspect_templates_message)s
<!-- replaced page header -->
<div class="headerlogo">
<table class="headerbox" cellspacing="0">
 <tr>
  <td align="right" valign="top" colspan="12">
  <div class="headerboxbodylogo">
   <a href="%(cssurl)s/?ln=%(ln)s">%(sitename)s</a>
  </div>
  </td>
 </tr>
 <!--
 <tr class="menu">
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody%(search_selected)s">
             <a class="header%(search_selected)s" href="%(cssurl)s/?ln=%(ln)s">%(msg_search)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody%(submit_selected)s">
             <a class="header%(submit_selected)s" href="%(cssurl)s/submit?ln=%(ln)s">%(msg_submit)s</a>
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody%(personalize_selected)s">
             %(useractivities)s
       </td>
       <td class="headermoduleboxbodyblank">
             &nbsp;
       </td>
       <td class="headermoduleboxbody%(help_selected)s">
             <a class="header%(help_selected)s" href="%(cssurl)s/help/%(langlink)s">%(msg_help)s</a>
       </td>
       %(adminactivities)s
       <td class="headermoduleboxbodyblanklast">
             &nbsp;
       </td>
 </tr>-->
</table>
</div>
<table class="navtrailbox">
 <tr>
  <td class="navtrailboxbody">
   %(navtrailbox)s
  </td>
 </tr>
</table>
<!-- end replaced page header -->
%(pageheaderadd)s
</div>
        """ % {
          'metabase': metabase,
          'rtl_direction': is_language_rtl(ln) and ' dir="rtl"' or '',
          'siteurl': CFG_SITE_URL,
          'sitesecureurl' : CFG_SITE_SECURE_URL,
          'canonical_and_alternate_urls' : self.tmpl_canonical_and_alternate_urls(uri),
          'cssurl' : CFG_BASE_URL,
          'cssskin' : CFG_WEBSTYLE_TEMPLATE_SKIN != 'default' and '_' + CFG_WEBSTYLE_TEMPLATE_SKIN or '',
          'rssurl': rssurl,
          'ln' : ln,
          'ln_iso_639_a' : ln.split('_', 1)[0],
          'langlink': '?ln=' + ln,

          'sitename' : CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME),
          'pageheadertitle': cgi.escape(pageheadertitle),

          'sitesupportemail' : CFG_SITE_SUPPORT_EMAIL,

          'description' : cgi.escape(description, True),
          'keywords' : cgi.escape(keywords, True),
          'metaheaderadd' : metaheaderadd,

          'userinfobox' : userinfobox,
          'navtrailbox' : navtrailbox,
          'useractivities': useractivities_menu,
          'adminactivities': adminactivities_menu and ('<td class="headermoduleboxbodyblank">&nbsp;</td><td class="headermoduleboxbody%(personalize_selected)s">%(adminactivities)s</td>' % \
          {'personalize_selected': navmenuid.startswith('admin') and "selected" or "",
          'adminactivities': adminactivities_menu}) or '<td class="headermoduleboxbodyblank">&nbsp;</td>',

          'pageheaderadd' : pageheaderadd,
          'body_css_classes' : body_css_classes and ' class="%s"' % ' '.join(body_css_classes) or '',

          'search_selected': navmenuid == 'search' and "selected" or "",
          'submit_selected': navmenuid == 'submit' and "selected" or "",
          'personalize_selected': navmenuid.startswith('your') and "selected" or "",
          'help_selected': navmenuid == 'help' and "selected" or "",

          'msg_search' : _("Search"),
          'msg_submit' : _("Submit"),
          'msg_personalize' : _("Personalize"),
          'msg_help' : _("Help"),
          'unAPIurl' : cgi.escape('%s/unapi' % CFG_SITE_URL),
          'linkbackTrackbackLink': headerLinkbackTrackbackLink,
          'hepDataAdditions': hepDataAdditions,
          'inspect_templates_message' : inspect_templates_message
        }
        return out

    def tmpl_pagefooter(self, req=None, ln=CFG_SITE_LANG, lastupdated=None,
                        pagefooteradd=""):
        """Creates a page footer

           Parameters:

          - 'ln' *string* - The language to display

          - 'lastupdated' *string* - when the page was last updated

          - 'pagefooteradd' *string* - additional page footer HTML code

           Output:

          - HTML code of the page headers
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if lastupdated and lastupdated != '$Date$':
            if lastupdated.startswith("$Date: ") or \
            lastupdated.startswith("$Id: "):
                lastupdated = convert_datestruct_to_dategui(\
                                 convert_datecvs_to_datestruct(lastupdated),
                                 ln=ln)
            msg_lastupdated = _("Last updated") + ": " + lastupdated
        else:
            msg_lastupdated = ""

        out = """
<div class="pagefooter">
%(pagefooteradd)s
<!-- replaced page footer -->
 <div class="pagefooterstripeleft">
  %(sitename)s&nbsp;::&nbsp;<a class="footer" href="%(siteurl)s/?ln=%(ln)s">%(msg_search)s</a>&nbsp;::&nbsp;<a class="footer" href="%(siteurl)s/submit?ln=%(ln)s">%(msg_submit)s</a>&nbsp;::&nbsp;<a class="footer" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(msg_personalize)s</a>&nbsp;::&nbsp;<a class="footer" href="%(siteurl)s/help/%(langlink)s">%(msg_help)s</a>
  <br />
  %(msg_poweredby)s <a class="footer" href="http://invenio-software.org/">Invenio</a> v%(version)s
  <br />
  %(msg_maintainedby)s <a class="footer" href="mailto:%(sitesupportemail)s">%(sitesupportemail)s</a>
  <br />
  %(msg_lastupdated)s
 </div>
 <div class="pagefooterstriperight">
 <p><em>
 Articles in the SCOAP3 repository are released under a <a target="_blank" rel="license" href="http://creativecommons.org/licenses/by/3.0/"><strong>CC-BY</strong></a> license. Metadata are provided by the corresponding publishers and released under the <a target="_blank"  rel="license"
     href="http://creativecommons.org/publicdomain/zero/1.0/">
    <strong>CC0</strong>
  </a> waiver.
 </em></p>
  %(languagebox)s
 </div>
<!-- replaced page footer -->
</div>
</body>
</html>
        """ % {
          'siteurl': CFG_BASE_URL,
          'sitesecureurl': CFG_SITE_SECURE_URL,
          'ln': ln,
          'langlink': '?ln=' + ln,

          'sitename': CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME),
          'sitesupportemail': CFG_SITE_SUPPORT_EMAIL,

          'msg_search': _("Search"),
          'msg_submit': _("Submit"),
          'msg_personalize': _("Personalize"),
          'msg_help': _("Help"),

          'msg_poweredby': _("Powered by"),
          'msg_maintainedby': _("Maintained by"),

          'msg_lastupdated': msg_lastupdated,
          'languagebox': self.tmpl_language_selection_box(req, ln),
          'version': CFG_VERSION,

          'pagefooteradd': pagefooteradd,
        }
        return out
