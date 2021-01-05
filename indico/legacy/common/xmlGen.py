# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# flake8: noqa

from xml.sax import saxutils

from indico.legacy.common.utils import encodeUnicode
from indico.util.string import encode_if_unicode


class XMLGen:

    def __init__(self, init=True):
        self.setSourceEncoding( "utf-8" )
        if init:
            self.initXml()
        else:
            self.xml=[]
        self.indent = 0

    def setSourceEncoding( self, newEnc = "utf-8" ):
        self._sourceEncoding = newEnc

    def initXml(self):
        self.xml=["""<?xml version="1.0" encoding="UTF-8"?>\n"""]

    def getXml(self):
        return "".join(self.xml)

    def escapeString(self,text):
        tmp = encodeUnicode(text, self._sourceEncoding)
        return saxutils.escape( tmp )

    def openTag(self, name, listAttrib=[], single=False):
        #open an XML tag
        #listAttrib is the list of the attribute. each attribute must be set in a 2 elements list like [name,value]
        #the single parameter, when false, place a '\n\r' after the tag
        LAtt = ""
        for att in listAttrib:
            LAtt= LAtt + ' ' + att[0] + '=' + saxutils.quoteattr(self.escapeString(att[1]))
        for i in range(0, self.indent):
            self.xml.append(" ")
        self.xml.append("<" + name + LAtt + ">")
        if not single:
            self.xml.append(self.escapeString("\r\n"))
        self.indent = self.indent + 1

    def closeTag(self,name,single=False):
        #close an XML tag
        self.indent = self.indent-1
        if not single:
            for i in range(0,self.indent):
                self.xml.append(" ")
        self.xml.append( "</" + name + ">\r\n")

    def writeText(self,text, single=False):
        #add text to the response
        #the single parameter, when false, place a '\n\r' after the text
        if text != "":
            text = self.cleanText(text)
            self.xml.append(self.escapeString(text))
        if not single:
            self.xml.append( self.escapeString("\r\n"))

    def writeTag(self, name, value, ListAttrib=[]):
        #add a full tag
        self.openTag(name, ListAttrib, True)
        self.writeText(value, True)
        self.closeTag(name, True)

    def writeXML(self,text):
        #add already well-formated text
        self.xml.append( text )

    def cleanText(self, text):
        # clean the text from illegal XML characters
        cm = []
        for c in range(256):
            if c < 0x20 and chr(c) not in '\t\r\n':
                cm.append(" ")
            else:
                cm.append(chr(c))
        return str(encode_if_unicode(text)).translate("".join(cm))
