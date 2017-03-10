# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.
from indico.core.logger import Logger
from HTMLParser import HTMLParser, HTMLParseError
from xml.sax.saxutils import  unescape

import re

allowedTags = ["a","abbr","acronym","address","area",
               "b","bdo","big","blockquote","br",
               "caption","center","cite","code","col","colgroup",
               "dd","del","dir","div","dfn","dl","dt",
               "em",
               "fieldset","font",
               "h1","h2","h3","h4","h5","h6","hr",
               "i","img","ins",
               "kbd",
               "legend","li",
               "map","menu",
               "ol",
               "p","pre",
               "q",
               "s","samp","small","span","strike","strong","sub","sup",
               "table","tbody","td","tfoot","th","thead","tr","tt",
               "u","ul",
               "var"]

allowedAttrs = ["align", "abbr", "alt",
                "border", "bgcolor",
                "class", "cellpadding", "cellspacing", "color", "char", "charoff", "cite", "clear", "colspan",
                "compact",
                "dir", "disabled", "face",
                "href", "height", "headers","hreflang","hspace",
                "id", "ismap",
                "lang",
                "name", "noshade", "nowrap",
                "rel", "rev", "rowspan", "rules",
                "size", "scope", "shape", "span", "src", "start", "summary",
                "tabindex", "target", "title", "type",
                "valign", "value", "vspace",
                "width", "wrap"]

allowedCssProperties = [ "background-color", "border-top-color", "border-top-style", "border-top-width",
                         "border-top", "border-right-color", "border-right-style",  "border-right-width",
                         "border-right", "border-bottom-color", "border-bottom-style", "border-bottom-width",
                         "border-bottom", "border-left-color", "border-left-style", "border-left-width",
                         "border-left", "border-color", "border-style", "border-width", "border", "bottom",
                         "border-collapse", "border-spacing",
                         "color", "clear", "clip", "caption-side",
                         "display", "direction",
                         "empty-cells",
                         "float","font-size","font-family","font-style","font","font-variant","font-weight",
                         "font-size-adjust", "font-stretch",
                         "height",
                         "left", "list-style-type", "list-style-position", "line-height", "letter-spacing",
                         "marker-offset","margin","margin-left","margin-right","margin-top","margin-bottom","max-height",
                         "min-height","max-width", "min-width", "marks",
                         "overflow", "outline-color", "outline-style", "outline-width", "outline", "orphans",
                         "position", "padding-top", "padding-right", "padding-bottom", "padding-left", "padding",
                         "page", "page-break-after", "page-break-before", "page-break-inside",
                         "quotes",
                         "right",
                         "size",
                         "text-align", "top", "table-layout", "text-decoration", "text-indent", "text-shadow",
                         "text-transform",
                         "unicode-bidi",
                         "visibility", "vertical-align",
                         "width", "widows", "white-space", "word-spacing", "word-wrap",
                         "z-index"]

allowedProtocols = [    'afs', 'aim',
                        'callto',
                        'feed', 'ftp',
                        'http', 'https',
                        'irc',
                        'mailto',
                        'news',
                        'gopher',
                        'nntp',
                        'rsync', 'rtsp',
                        'ssh', 'sftp',
                        'tag', 'telnet',
                        'urn',
                        'webcal',
                        'xmpp' ]

urlProperties = ['action',
                 'cite',
                 'href',
                 'longdesc',
                 'src',
                 'xlink:href', 'xml:base']

specialAcceptedTags = [
               "^([a-zA-Z0-9\-_]+.)*[a-zA-Z0-9\-_]+@([a-zA-Z0-9\-_]+.)*[a-zA-Z0-9\-_]+$", # email
               "^(" + "|".join(allowedProtocols) + ")://[^<>.][^<>]*$" # url
               ]

locatestartendtag = re.compile(r"""
  <([a-zA-Z][^\s<>]*)>
""", re.VERBOSE)


class HarmfulHTMLException(Exception):

    def __init__(self, msg, pos = 0):
        self.msg = _("""Using forbidden HTML: "%s" found at %s""") % (msg, pos)

    def __str__(self):
        return self.msg


class RestrictedHTMLParser( HTMLParser ):

    _defaultSanitizationLevel = 1

    def __init__( self, sanitizationLevel = _defaultSanitizationLevel):
        HTMLParser.__init__(self)
        if sanitizationLevel not in range(0,3):
            sanitizationLevel = self._defaultSanitizationLevel
        self._sanitizationLevel = sanitizationLevel

    def getSanitizationLevel(self):
        return self._sanitizationLevel

    def setSanitizationLevel(self, sanitizationLevel):
        if sanitizationLevel not in range(0,3):
            sanitizationLevel = self._defaultSanitizationLevel
        self._sanitizationLevel = sanitizationLevel

    def error(self, message):
        # TODO: remove this dependency with HTMLParser. Use a lib that allows
        # parsing of malformed HTML. The reason for this checking is that when
        # there is a paramter (non HTML) containing a '&', it fails.
        if message.startswith("EOF in middle of entity or char ref"):
            return

        raise HTMLParseError(message, self.getpos())

    def handle_inlineStyle(self, style):
        # disallow urls
        style = re.compile('url\s*\(\s*[^\s)]+?\s*\)\s*').sub(' ', style)
        # gauntlet
        if not re.match("""^([\-:,;#%.\sa-zA-Z0-9!]|\w-\w|'[\s\w]+'|"[\s\w]+"|\([\d,\s]+\))*$""", style):
            raise HarmfulHTMLException(style, self.getpos())
        if not re.match("^\s*([-\w]+\s*:[^:;]*(;\s*|$))*$", style):
            raise HarmfulHTMLException(style, self.getpos())
        for prop, value in re.findall("([-\w]+)\s*:\s*([^:;]*)", style):
            if not value: continue
            if not prop.lower() in allowedCssProperties and \
               not prop.split('-')[0].lower() in ['background', 'border', 'margin', 'padding']:
                raise HarmfulHTMLException(style, self.getpos())

    def handle_starttag(self, tag, attrs):
        if tag not in allowedTags:
            raise HarmfulHTMLException( tag, self.getpos() )
        for attr in attrs:
            if self.getSanitizationLevel() >= 2 and attr[0] == 'style':
                self.handle_inlineStyle(attr[1])
            elif attr[0] not in allowedAttrs:
                raise HarmfulHTMLException(attr[0], self.getpos())
            elif attr[0] in urlProperties:
                val_unescaped = re.sub("[`\000-\040\177-\240\s]+", '', unescape(attr[1])).lower()
                try:
                    #remove replacement characters from unescaped characters
                    val_unescaped = val_unescaped.replace(u"\ufffd", "")
                except UnicodeDecodeError, e:
                    Logger.get('RestrictedHTMLParser-urlProperties').exception(str(e))
                if (re.match("^[a-z0-9][-+.a-z0-9]*:", val_unescaped) and
                    (val_unescaped.split(':')[0] not in
                     allowedProtocols)):
                    raise HarmfulHTMLException(val_unescaped.split(':')[0], self.getpos())

    def _isSpecialTag(self, i):
        """ Returns -1 if it is not a special tag. Otherwise it returns the end position."""

        tag = locatestartendtag.match(self.rawdata[i:])
        # check if the tag is a special tag or a real parsing error
        if tag and tag.groups():
            tag = tag.groups()[0]
            for specialTagRE in specialAcceptedTags:
                if re.match(specialTagRE, tag):
                    return i+len(tag)+2 # we add 2 because of < and >
        return -1

    # Internal -- handle starttag, return end or -1 if not terminated
    def parse_starttag(self, i):
        try:
            pos = HTMLParser.parse_starttag(self, i)
            if pos == -1:
                pos = self._isSpecialTag(i)
            return pos
        except HTMLParseError:
            pos = self._isSpecialTag(i)
            if pos != -1:
                return pos
            raise


def restrictedHTML(txt, sanitizationLevel):
    try:
        parser = RestrictedHTMLParser(sanitizationLevel)
        parser.feed(txt + '>')
        parser.close()
    except (HarmfulHTMLException, HTMLParseError),e :
        return e.msg
    return None


def escape_html(text, escape_quotes=False):
    """ Escape all HTML tags, avoiding XSS attacks.
        < => &lt;
        > => &gt;
        & => &amp;
        @param text: text to be escaped from HTML tags
        @param escape_quotes: if True, escape any quote mark to its HTML entity:
                          " => &quot;
                          ' => &#34;
    """
    if type(text) != str:
        text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    if escape_quotes:
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#34;')
    return text


# Routine by Micah D. Cochran
# Submitted on 26 Aug 2005
# This routine is allowed to be put under any license Open Source (GPL, BSD, LGPL, etc.) License
# or any Propriety License. Effectively this routine is in public domain. Please attribute where appropriate.
def strip_ml_tags(in_text):
    """ Description: Removes all HTML/XML-like tags from the input text.
        Inputs: s --> string of text
        Outputs: text string without the tags

        # doctest unit testing framework

        >>> test_text = "Keep this Text <remove><me /> KEEP </remove> 123"
        >>> strip_ml_tags(test_text)
        'Keep this Text  KEEP  123'
    """

    # convert in_text to a mutable object (e.g. list)
    s_list = list(in_text)
    i = 0

    while i < len(s_list):
        # iterate until a left-angle bracket is found
        if s_list[i] == '<':
            try:
                while s_list[i] != '>':
                    # pop everything from the the left-angle bracket until the right-angle bracket
                    s_list.pop(i)
            except IndexError,e:
                Logger.get('strip_ml_tags').debug("Not found '>' (the end of the html tag): %s"%e)
                continue

            # pops the right-angle bracket, too
            s_list.pop(i)
        else:
            i=i+1

    # convert the list back into text
    join_char=''
    return join_char.join(s_list)
