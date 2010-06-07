# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
from MaKaC.common.logger import Logger

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
               "s","samp","small","span","strike","strong","style","sub","sup",
               "table","tbody","td","tfoot","th","thead","tr","tt",
               "u","ul",
               "var"]

notAllowedTags = [ "applet",
                   "base", "basefont", "button",
                   "form", "frame", "frameset",
                   "head",
                   "iframe", "input", "isindex",
                   "label", "link",
                   "meta",
                   "noframe", "noscript",
                   "object", "optgroup", "option"
                   "param",
                   "script", "select",
                   "textarea",
                   "title", "embed"]


# Generate the regular expression objects to found the not allowed tags
tagSearch = re.compile("< *[^<^>^ ]+",re.IGNORECASE|re.DOTALL)

scriptStr = "\s*(s|&#115;|&#83;)"\
            "\s*(c|&#99;|&#67;)"\
            "\s*(r|&#114;|&#82;)"\
            "\s*(i|&#105;|&#73;)"\
            "\s*(p|&#112;|&#80;)"\
            "\s*(t|&#112;|&#84)"
script = re.compile("< *%s"%scriptStr,re.IGNORECASE|re.DOTALL)

iframeStr = "\s*(i|&#105;|&#73;)"\
            "\s*(f|&#102;|&#70;)"\
            "\s*(r|&#114;|&#82;)"\
            "\s*(a|&#97;|&#65;)"\
            "\s*(m|&#109;|&#77;)"\
            "\s*(e|&#101;|&#69;)"
iframe = re.compile("< *%s"%iframeStr,re.IGNORECASE|re.DOTALL)

formStr = "\s*(f|&#102;|&#70;)"\
          "\s*(o|&#111;|&#79;)"\
          "\s*(r|&#114;|&#82;)"\
          "\s*(m|&#109;|&#77;)"
form = re.compile("< *%s"%formStr,re.IGNORECASE|re.DOTALL)

onList = ["onblur","onchange","onclick","ondblclick","onerror","onfocus",
          "onkeydown","onkeypress","onkeyup","onload","onmousedown","onmousemove",
          "onmouseout","onmouseover","onmouseup","onreset","onresize","onselect",
          "onsubmit","onunload"]

on = re.compile("<[^>]*(%s)"%"|".join(onList), re.IGNORECASE|re.DOTALL)

style = re.compile("<[^>]*style")

def scriptDetection(txt, allowStyle=False):
    #search for "<script> tag
    if script.findall(txt):
        return True
    #search for javascript event manager
    if on.findall(txt):
        return True
    if not allowStyle:
        #search for style
        if style.findall(txt):
            return True
    return False

##def restrictedHTML(txt):
##    if iframe.findall(txt):
##        return False
##    if form.findall(txt):
##        return False
##    return True

def restrictedHTML(txt):
    #use a black list
    notFound = True
    for tag in tagSearch.findall(txt):
        tag = tag[1:].strip()
        if tag:
            if tag[0] == "/":
                tag = tag[1:].strip()
            if tag:
                if tag.lower() in notAllowedTags:
                    notFound = False
    return notFound

##def restrictedHTML(txt):
##    #use a white list
##    for tag in tagSearch.findall(txt):
##        tag = tag[1:].strip()
##        if tag[0] == "/":
##            tag = tag[1:].strip()
##        if not tag.lower() in allowedTags:
##            return False
##    return True


def hasTags(s):
    """ Returns if a given string has any tags
    """
    return tagSearch.search(s) is not None

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
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    if escape_quotes:
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#34;')
    return text

def unescape_html(text):
    """ Replaces instances of escaped entities by their characters
        &nbsp; => (space)
        &lt; => <
        &gt; => >
        &amp; => &
        &quot; => "
        &#34; => '

        Also replaces '\xc2\xa0' (a kind of space char) by ' '
    """
    return text.replace('&nbsp;', ' ').replace('\xc2\xa0', ' ').replace('&lt;', '<').replace('&gt;','>').replace('&quot','"').replace('&#34;',"'").replace('&amp;','&')

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

# Method that remove all the problematic characters from a filename used
# in HTML Headers.
def cleanHTMLHeaderFilename(fn):
    fn=fn.replace("/", "")
    fn=fn.replace("\r","")
    fn=fn.replace("\n","")
    return fn
