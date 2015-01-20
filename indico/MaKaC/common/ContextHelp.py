# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import xml.dom.minidom as minidom
from lxml import etree, builder, html as lhtml
from MaKaC.errors import MaKaCError
from indico.core.config import Config
import xml.sax
import xml.sax.saxutils as saxutils
import re, StringIO
from MaKaC.i18n import _


class WOHLParserException( Exception ):
    """
        WOHL Parser Exception
    """

    def __init__( self, value ):
        """
            Constructor
            @param value: the message carried by the exception
            @type value: something convertible to a string
        """
        self.value = value

    def __str__(self):
        s = str( self.value )
        return s

class WOHLParser:
    """
        A simple WOHL Parser
    """

    def __readText(self, textNode):
        """
            Read a Text Node

            @param textNode: An XML DOM text node
            @type textNode: xml.dom.Node

            @return: the content as a string
        """
        return textNode.toxml()

    def __readHelpRef(self, refNode):
        """
            Read a <helpref /> node, and return a tuple representing it

            @param refNode: the helpref, a DOM Node
            @type refNode: xml.dom.Node

            @return: tuple with the url and text of the helpref
        """
        return (refNode.attributes['url'].nodeValue,
                refNode.attributes['text'].nodeValue)

    def __readTranslation(self, transNode):
        """
            Read a <translation /> node, and return a tuple representing it

            @param transNode: the translation, a DOM Node
            @type transNode: xml.dom.Node

            @return: tuple with the text and helpref structures, for this specific language
        """

        text = None
        refs = []

        for child in transNode.childNodes:
            if child.nodeType != minidom.Node.ELEMENT_NODE:
                continue

            if child.tagName == "text":
                text = self.__readText(child)
            elif child.tagName == "helpref":
                refs.append(self.__readHelpRef(child))
            else:
                raise WOHLParserException( _("Element not allowed here!"))

        if text == None:
            raise WOHLParserException( _("Translation should have a <text /> element!"))

        return (text,refs)

    def __readTooltip(self, ttNode):
        """
            Read a <tooltip /> node, and return a tuple representing it

            @param ttNode: the tooltip, a DOM node
            @type ttNode: xml.dom.Node

            @return: the tooltip, represented by a tuple with its target, translation, type
        """

        translation = None
        type = "explicit"

        for child in ttNode.childNodes:
            if child.nodeType != minidom.Node.ELEMENT_NODE:
                continue

            if child.tagName != "translation":
                raise WOHLParserException( _("Element not allowed here!"))
            if child.attributes["language"].nodeValue == self.__language:
                translation = self.__readTranslation(child)

        if ttNode.attributes.has_key("type"):
            type = ttNode.attributes["type"].nodeValue

        return ('tooltip', ttNode.attributes["target"].nodeValue,translation,type)

    def __readInformation(self, ttNode):
        """
            Read an <information /> node, and return a tuple representing it

            @param ttNode: the information, a DOM node
            @type ttNode: xml.dom.Node

            @return: the information, represented by a tuple with its target, translation
        """

        translation = None
        type = "explicit"

        for child in ttNode.childNodes:
            if child.nodeType != minidom.Node.ELEMENT_NODE:
                continue

            if child.tagName != "translation":
                raise WOHLParserException("Element not allowed here!")
            if child.attributes["language"].nodeValue == self.__language:
                translation = self.__readTranslation(child)

        return ('information', ttNode.attributes["target"].nodeValue,translation)

    def __readPage(self, pageNode):
        """
            Read a <page /> node, and return a dictionary representing it

            @param pageNode: a <page /> node
            @type pageNode: xml.dom.Node

            @return: a dictionary, with a tooltip name as key, and its content tuple as value
        """
        page = {}

        for child in pageNode.childNodes:
            if child.nodeType != minidom.Node.ELEMENT_NODE:
                continue

            if child.tagName == "tooltip":
                page[child.attributes["name"].nodeValue] = self.__readTooltip(child)
            elif child.tagName == "information":
                page[child.attributes["name"].nodeValue] = self.__readInformation(child)
            else:
                raise WOHLParserException("Element not allowed here!")


        return page

    def getPages(self):
        """
        @return: All the pages in the file, in a dictionary
        """
        return self.__pages

    def __init__(self, helpString, language):
        """
        Constructor

            @param helpString: the XML input for the parser
            @type helpString: string
            @param language: the language which the translations should be fetched in
            @type language: string (TLD/ISO 3166-1 alpha-2 code)
        """

        dom = minidom.parseString(helpString)

        self.__pages = {}
        self.__language = language

        root = dom.documentElement

        if root.tagName != "wohl":
            raise WOHLParserException( _("Wrong root node!"))

        for child in root.childNodes:
            if child.nodeType != minidom.Node.ELEMENT_NODE:
                continue

            if child.tagName != "page":
                raise WOHLParserException( _("Element not allowed here!"))
            self.__pages[child.attributes["name"].nodeValue] = self.__readPage(child)


class ContextHelp:
    """
        Performs the merge between a normal HTML page, and a WOHL help file,
        returning, as a result, a "context help-enhanced" webpage.
    """

    def __init__(self):
        self.__stripExpr = re.compile('^<\![^>]*>[\n]*<html>[\n]*<body>(.*)</body>[\n]*</html>[\n]*$',re.DOTALL)

    class __TextContentHandler(xml.sax.ContentHandler):
        """
            Content handler for SAX parser. Takes care of text markup inside the
            <text /> node of a tooltip
        """

        def __init__(self):
            """
                Constructor
            """
            self.__inside = []
            self.__trace = []
            self.__html = ""

            self.__translation = {'text':('div', 'padding: 3px;'),
                                  'em':'em',
                                  'strong':'strong',
                                  'important':('span','font-weight: bold; color: red;'),
                                  'title':('span','text-decoration: underline; margin-top: 5px; display: block;'),
                                  'p':('span','display:block;'),
                                  'ul': 'ul',
                                  'li': 'li'}


        def getHTML(self):
            """
                @return: HTML code built by the handler
            """
            return self.__html

        def __translateTag(self,name,closing=False):
            """
                Performs a translation between a WOHL in-text tag and an actual HTML tag

                @param name: the name of the tag to be translated
                @type name: string
                @param closing: is the tag a closing tag?
                @type closing: boolean

                @return: the HTML tag, as a string
            """

            try:
                translation = self.__translation[name]

                if (type(translation).__name__ == "tuple"):
                    transTag = translation[0]
                    transStyle = translation[1]
                else:
                    transTag = translation
                    transStyle = None

            except KeyError:
                raise WOHLParserException( _("No translation found for tag '%s'") % name)

            if (closing):
                return "</%s>" % transTag
            else:
                if (transStyle == None):
                    return "<%s>" % transTag
                else:
                    return "<%s style=%s>" % (transTag, saxutils.quoteattr(transStyle))


        def startElement(self, name, attrs):
            """
                Overrides SAX API handler
            """
            self.__inside.append(name)

            self.__trace.append(('open',name))

            self.__html += self.__translateTag(name)

        def endElement(self, name):
            """
                Overrides SAX API handler
            """
            elem = self.__inside[-1]
            self.__trace.append(('close',name))

            if (elem != name):
                raise WOHLParserException( _("Malformed expression! '%s' when '%s' expected (trace: %s)") % (name, elem, str(self.__trace)))
            else:
                self.__inside.pop()

            self.__html += self.__translateTag(name, closing=True)

        def characters(self, data):
            self.__html += saxutils.escape(data)

    def __processRefs(self, refs):
        """
            Transform a list of <linkref /> translated objects into an HTML list

            @param refs: list of references
            @type refs: list with reference tuples

            @return: HTML code for a reference list
        """

        if len(refs) == 0:
            return ""

        html = "<ul>"

        for ref in refs:
            html += "<li><a href=\"%s\">%s</a></li>" % (ref[0], ref[1])

        return html + "</ul>"

    def __searchId(self, wholPage, id):
        """
            Searches for the WHOL entry which describes a given node id

            @param wholPage: a translated WHOL <page />
            @type wholPage: dictionary, with tooltip name as key and translation tuple as value
            @param id: the id of the node
            @type id: string

            @return: tooltip text and type (tuple) if found, or None otherwise\
            @rtype: string or None
        """

        for ttName in wholPage:
            (ttTarget, ttText, ttType) = wholPage[ttName]
            if ttTarget == id:
                return (ttText, ttType)
        return None

    def __convertTextToHTML(self, source):
        """
            Converts a <text /> content to HTML

            @param source: source XML
            @type source: string

            @return: HTML code for the node
        """
        try:
            tContentHandler = self.__TextContentHandler()
            xml.sax.parseString(source[0].encode('utf-8'), tContentHandler)
            refHTML = self.__processRefs(source[1])
        except Exception, e:
            raise WOHLParserException( _("Error parsing: %s - %s\n") % (source[0], e))

        return tContentHandler.getHTML().encode('utf-8') + refHTML

    def __stripWrapper(self, text):
        # very dirty hack to remove enclosing entities

        m = self.__stripExpr.match(text)

        if m == None:
            raise WOHLParserException("Error parsing generated HTML! "+ text)

        return m.group(1)

    def __mergeTooltip(self, tooltip, snippets, count, doc):

            (ttTarget, ttText, ttType) = tooltip

            xpathRes= doc.xpath(ttTarget)

            ttText =  self.__convertTextToHTML(ttText)

            for elem in xpathRes:

                content =   '{indico:help ref=snip%s}' % count

                filteredText = ttText.replace('\n', '').replace('"', '&quot;')

                if ttType == 'explicit':
                    snippets['snip'+str(count)] ="""<span class="contextHelp" title="%s">
                                                <span style="color: Green; margin-left: 6px; font-size:smaller;"><img style="border: None;display:inline-block;vertical-align: middle" src="%s"/></span>
                                                </span>""" % (filteredText,Config.getInstance().getSystemIconURL( "help" ))

                    elem.append(builder.E.span(content))
                elif ttType == 'hover':
                    elem.set('class', ('contextHelp ' + elem.get('class')).strip())
                    elem.set('title', filteredText)

                else:
                    raise Exception( _('Tooltip type not recognized: ') + str(type))

                count += 1

            return count


    def __mergeInformation(self, information, snippets, count, xpathCtxt):

        (ttTarget, ttText) = information

        xpathRes = doc.xpath(ttTarget)

        ttText =  self.__convertTextToHTML(ttText)

        for elem in xpathRes:

            content =   '{indico:help ref=snip%s}' % count

            filteredText = ttText.replace('\n', '').replace('"', '&quot;')

            snippets['snip'+str(count)] = filteredText
            elem.append(builder.E.div(content, {'class': 'ctxtInfo'}))

            count += 1

        return count

    def __doMerge(self, html, wohl):

        parser = etree.HTMLParser()
        doc  = etree.parse(StringIO.StringIO(html), parser)

        snippets = {}
        count = 0

        for name in wohl:
            if wohl[name][0] == "tooltip":
                count = self.__mergeTooltip(wohl[name][1:],snippets, count, doc)
            elif wohl[name][0] == "information":
                count = self.__mergeInformation(wohl[name][1:],snippets, count, doc)

        docSer = lhtml.tostring(doc)

        if (len(snippets)!=0):
            # stripWrapper is a dirty dirty hack to bypass the problem
            # that lxml outputs HTML documents, and no isolated blocks

            newHtml = re.sub(r'{indico:help ref=([a-z0-9]+)}',
                             lambda m: snippets[m.group(1)],
                             str(self.__stripWrapper(docSer)))
        else:
            newHtml = str(self.__stripWrapper(docSer))

        return newHtml

    def merge(self, tplId, htmlText, helpText):
        """
            Perform the merge between a regular HTML document and a WOHL specification

            @param tplId: the id of the page template (name)
            @type tplId: string

            @param htmlText: (X)HTML code
            @type htmlText: string

            @param helpText: XML code
            @type helpText: string
        """

        try:
            parser = WOHLParser(helpText,"en")

            if not parser.getPages().has_key(tplId):
                raise MaKaCError( _("WOHL File has no reference to page %s") % tplId)
            else:
#                f = file("c:/logMerge.log", 'a')
#                f.write("\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#Entree de Merge dans contextHelp\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\n\n\n\n")
#                f.write("%s\n\n\n\n\n\n"%htmlText)
#                f.close()
                return self.__doMerge(htmlText,parser.getPages()[tplId])

        except WOHLParserException, e:
            raise MaKaCError( _("Exception parsing context help information: ")+str(e))
