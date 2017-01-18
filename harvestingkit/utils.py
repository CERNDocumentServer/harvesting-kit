# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2014, 2015, 2016, 2017 CERN.
#
# Harvesting Kit is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Harvesting Kit is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Harvesting Kit; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Utility functions for Harvesting Kit."""

import re
import os
import pkg_resources
import htmlentitydefs
import requests
import subprocess
import logging
import fnmatch
import zipfile

from datetime import datetime
from tempfile import mkdtemp, mkstemp
from lxml import etree
from unidecode import unidecode

from .config import COMMON_ACRONYMS, OA_LICENSES


def make_user_agent(component=None):
    """ create string suitable for HTTP User-Agent header """
    packageinfo = pkg_resources.require("harvestingkit")[0]
    useragent = "{0}/{1}".format(packageinfo.project_name, packageinfo.version)
    if component is not None:
        useragent += " {0}".format(component)
    return useragent


def create_record():
    """Return a new XML document."""
    return etree.Element("record")


def record_add_field(rec, tag, ind1='', ind2='', subfields=[],
                     controlfield_value=''):
    """Add a MARCXML datafield as a new child to a XML document."""
    if controlfield_value:
        doc = etree.Element("controlfield",
                            attrib={
                                "tag": tag,
                            })
        doc.text = unicode(controlfield_value)
    else:
        doc = etree.Element("datafield",
                            attrib={
                                "tag": tag,
                                "ind1": ind1,
                                "ind2": ind2,
                            })
        for code, value in subfields:
            field = etree.SubElement(doc, "subfield", attrib={"code": code})
            field.text = value
    rec.append(doc)
    return rec


def record_xml_output(rec, pretty=True):
    """Given a document, return XML prettified."""
    from .html_utils import MathMLParser
    ret = etree.tostring(rec, xml_declaration=False)

    # Special MathML handling
    ret = re.sub("(&lt;)(([\/]?{0}))".format("|[\/]?".join(MathMLParser.mathml_elements)), '<\g<2>', ret)
    ret = re.sub("&gt;", '>', ret)
    if pretty:
        # We are doing our own prettyfication as etree pretty_print is too insane.
        ret = ret.replace('</datafield>', '  </datafield>\n')
        ret = re.sub(r'<datafield(.*?)>', r'  <datafield\1>\n', ret)
        ret = ret.replace('</subfield>', '</subfield>\n')
        ret = ret.replace('<subfield', '    <subfield')
        ret = ret.replace('record>', 'record>\n')
    return ret


def escape_for_xml(data, tags_to_keep=None):
    """Transform & and < to XML valid &amp; and &lt.

    Pass a list of tags as string to enable replacement of
    '<' globally but keep any XML tags in the list.
    """
    data = re.sub("&", "&amp;", data)
    if tags_to_keep:
        data = re.sub(r"(<)(?![\/]?({0})\b)".format("|".join(tags_to_keep)), '&lt;', data)
    else:
        data = re.sub("<", "&lt;", data)
    return data


def unescape(text):
    """Remove HTML or XML character references and entities from a text string.

    NOTE: Does not remove &amp; &lt; and &gt;.

    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        elif text[1:-1] not in ("gt", "lt", "amp"):
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub("&#?\w+;", fixup, text)


def format_arxiv_id(arxiv_id):
    """Properly format arXiv IDs."""
    if arxiv_id and "/" not in arxiv_id and "arXiv" not in arxiv_id:
        return "arXiv:%s" % (arxiv_id,)
    elif arxiv_id and '.' not in arxiv_id and arxiv_id.lower().startswith('arxiv:'):
        return arxiv_id[6:]  # strip away arxiv: for old identifiers
    else:
        return arxiv_id


def safe_title(text):
    """Perform a UTF-8 safe str.title() wrapper."""
    return unicode(text, "utf-8").title().encode("utf-8")


def collapse_initials(name):
    """Remove the space between initials, eg T. A. --> T.A."""
    if len(name.split(".")) > 1:
        name = re.sub(r'([A-Z]\.)[\s\-]+(?=[A-Z]\.)', r'\1', name)
    return name


def fix_journal_name(journal, knowledge_base):
    """Convert journal name to Inspire's short form."""
    if not journal:
        return '', ''
    if not knowledge_base:
        return journal, ''
    if len(journal) < 2:
        return journal, ''
    volume = ''
    if (journal[-1] <= 'Z' and journal[-1] >= 'A') \
            and (journal[-2] == '.' or journal[-2] == ' '):
        volume += journal[-1]
        journal = journal[:-1]
    try:
        journal = journal.strip()
        journal = knowledge_base[journal.upper()].strip()
    except KeyError:
        try:
            journal = knowledge_base[journal].strip()
        except KeyError:
            pass
    journal = journal.replace('. ', '.')
    return journal, volume


def add_nations_field(authors_subfields):
    """Add correct nations field according to mapping in NATIONS_DEFAULT_MAP."""
    from .config import NATIONS_DEFAULT_MAP
    result = []
    for field in authors_subfields:
        if field[0] == 'v':
            values = [x.replace('.', '') for x in field[1].split(', ')]
            possible_affs = filter(lambda x: x is not None,
                                   map(NATIONS_DEFAULT_MAP.get, values))
            if 'CERN' in possible_affs and 'Switzerland' in possible_affs:
                # Don't use remove in case of multiple Switzerlands
                possible_affs = [x for x in possible_affs
                                 if x != 'Switzerland']

            result.extend(possible_affs)

    result = sorted(list(set(result)))

    if result:
        authors_subfields.extend([('w', res) for res in result])
    else:
        authors_subfields.append(('w', 'HUMAN CHECK'))


def fix_dashes(string):
    """Fix bad Unicode special dashes in string."""
    string = string.replace(u'\u05BE', '-')
    string = string.replace(u'\u1806', '-')
    string = string.replace(u'\u2E3A', '-')
    string = string.replace(u'\u2E3B', '-')
    string = unidecode(string)
    return re.sub(r'--+', '-', string)


def fix_title_capitalization(title):
    """Try to capitalize properly a title string."""
    if re.search("[A-Z]", title) and re.search("[a-z]", title):
        return title
    word_list = re.split(' +', title)
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        if word.upper() in COMMON_ACRONYMS:
            final.append(word.upper())
        elif len(word) > 3:
            final.append(word.capitalize())
        else:
            final.append(word.lower())
    return " ".join(final)


def convert_html_subscripts_to_latex(text):
    """Convert some HTML tags to latex equivalents."""
    text = re.sub("<sub>(.*?)</sub>", r"$_{\1}$", text)
    text = re.sub("<sup>(.*?)</sup>", r"$^{\1}$", text)
    return text


def download_file(from_url, to_filename=None,
                  chunk_size=1024 * 8, retry_count=3):
    """Download URL to a file."""
    if not to_filename:
        to_filename = get_temporary_file()

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_count)
    session.mount(from_url, adapter)
    response = session.get(from_url, stream=True)
    with open(to_filename, 'wb') as fd:
        for chunk in response.iter_content(chunk_size):
            fd.write(chunk)
    return to_filename


def run_shell_command(commands, **kwargs):
    """Run a shell command."""
    p = subprocess.Popen(commands,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         **kwargs)
    output, error = p.communicate()
    return p.returncode, output, error


def create_logger(name,
                  filename=None,
                  logging_level=logging.DEBUG):
    """Create a logger object."""
    logger = logging.getLogger(name)
    formatter = logging.Formatter(('%(asctime)s - %(name)s - '
                                   '%(levelname)-8s - %(message)s'))

    if filename:
        fh = logging.FileHandler(filename=filename)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.setLevel(logging_level)

    return logger


def unzip(zipped_file, output_directory=None,
          prefix="harvestingkit_unzip_", suffix=""):
    """Uncompress a zipped file from given filepath to an (optional) location.

    If no location is given, a temporary folder will be generated inside
    CFG_TMPDIR, prefixed with "apsharvest_unzip_".
    """
    if not output_directory:
        # We create a temporary directory to extract our stuff in
        try:
            output_directory = mkdtemp(suffix=suffix,
                                       prefix=prefix)
        except Exception, e:
            try:
                os.removedirs(output_directory)
            except TypeError:
                pass
            raise e
    return _do_unzip(zipped_file, output_directory)


def _do_unzip(zipped_file, output_directory):
    """Perform the actual uncompression."""
    z = zipfile.ZipFile(zipped_file)
    for path in z.namelist():
        relative_path = os.path.join(output_directory, path)
        dirname, dummy = os.path.split(relative_path)
        try:
            if relative_path.endswith(os.sep) and not os.path.exists(dirname):
                os.makedirs(relative_path)
            elif not os.path.exists(relative_path):
                dirname = os.path.join(output_directory, os.path.dirname(path))
                if os.path.dirname(path) and not os.path.exists(dirname):
                    os.makedirs(dirname)
                fd = open(relative_path, "w")
                fd.write(z.read(path))
                fd.close()
        except IOError, e:
            raise e
    return output_directory


def locate(pattern, root=os.curdir):
    """Locate all files matching supplied filename pattern recursively."""
    for path, dummy, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


def punctuate_authorname(an):
    """Punctuate author names properly.

    Expects input in the form 'Bloggs, J K' and will return 'Bloggs, J. K.'.
    """
    name = an.strip()
    parts = [x for x in name.split(',') if x != '']
    ret_str = ''
    for idx, part in enumerate(parts):
        subparts = part.strip().split(' ')
        for sidx, substr in enumerate(subparts):
            ret_str += substr
            if len(substr) == 1:
                ret_str += '.'
            if sidx < (len(subparts) - 1):
                ret_str += ' '
        if idx < (len(parts) - 1):
            ret_str += ', '
    return ret_str.strip()


def convert_date_to_iso(value):
    """Convert a date-value to the ISO date standard."""
    date_formats = ["%d %b %Y", "%Y/%m/%d"]
    for dformat in date_formats:
        try:
            date = datetime.strptime(value, dformat)
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return value


def convert_date_from_iso_to_human(value):
    """Convert a date-value to the ISO date standard for humans."""
    try:
        year, month, day = value.split("-")
    except ValueError:
        # Not separated by "-". Space?
        try:
            year, month, day = value.split(" ")
        except ValueError:
            # What gives? OK, lets just return as is
            return value

    try:
        date_object = datetime(int(year), int(month), int(day))
    except TypeError:
        return value
    return date_object.strftime("%d %b %Y")


def get_converted_image_name(image):
    """Return the name of the image after it has been converted to png format.

    Strips off the old extension.

    :param image: The fullpath of the image before conversion
    :type image: string

    :return: the fullpath of the image after convertion
    """
    png_extension = '.png'

    if image[(0 - len(png_extension)):] == png_extension:
        # it already ends in png!  we're golden
        return image

    img_dir = os.path.split(image)[0]
    image = os.path.split(image)[-1]

    # cut off the old extension
    if len(image.split('.')) > 1:
        old_extension = '.' + image.split('.')[-1]
        converted_image = image[:(0 - len(old_extension))] + png_extension

    else:
        converted_image = image + png_extension

    return os.path.join(img_dir, converted_image)


def convert_images(image_list):
    """Convert list of images to PNG format.

    @param: image_list ([string, string, ...]): the list of image files
        extracted from the tarball in step 1

    @return: image_list ([str, str, ...]): The list of image files when all
        have been converted to PNG format.
    """
    png_output_contains = 'PNG image'
    ret_list = []
    for image_file in image_list:
        if os.path.isdir(image_file):
            continue

        dummy1, cmd_out, dummy2 = run_shell_command('file %s', (image_file,))
        if cmd_out.find(png_output_contains) > -1:
            ret_list.append(image_file)
        else:
            # we're just going to assume that ImageMagick can convert all
            # the image types that we may be faced with
            # for sure it can do EPS->PNG and JPG->PNG and PS->PNG
            # and PSTEX->PNG
            converted_image_file = get_converted_image_name(image_file)
            cmd_list = ['convert', image_file, converted_image_file]
            dummy1, cmd_out, cmd_err = run_shell_command(cmd_list)
            if cmd_err == '':
                ret_list.append(converted_image_file)
            else:
                raise Exception(cmd_err)
    return ret_list


def get_temporary_file(prefix="tmp_",
                       suffix="",
                       directory=None):
    """Generate a safe and closed filepath."""
    try:
        file_fd, filepath = mkstemp(prefix=prefix,
                                    suffix=suffix,
                                    dir=directory)
        os.close(file_fd)
    except IOError, e:
        try:
            os.remove(filepath)
        except Exception:
            pass
        raise e
    return filepath


def return_letters_from_string(text):
    """Get letters from string only."""
    out = ""
    for letter in text:
        if letter.isalpha():
            out += letter
    return out

def license_is_oa(license):
    """Return True if license is compatible with Open Access"""
    for oal in OA_LICENSES:
        if re.search(oal, license):
            return True
    return False

