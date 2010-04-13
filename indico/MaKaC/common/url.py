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

"""This file contains classes which allow to handle URLs in a transparent way
"""
import urllib
from UserList import UserList
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.errors import MaKaCError


class URL:
    """This class represents an internet URL and provides methods in order to 
        handle it in an easy way; it encapsulates the encoding of the parameters
        so clients don't need to worry about that. It also implements the 
        __str__ method which will allow to treat it as a simple string.
       
       Attributes:
        _base - (String) base url containing the protocol, hostname and path 
            in a correct way
        _params - (Dict) parameters to be added to the URL
    """
    
    def __init__( self, base, **params ):
        self._segment = ""
        self.setBase( base )
        self.setParams( params )
        """ 
            Spearator might need to be set to &amp; by default inorder to 
            follow the W3C standard, but this seems to give problems in IE.
        """
        self._separator = "&"

    def getBase( self ):
        return self._base

    def setBase( self, newBase ):
        self._base = str( newBase ).strip()

    def getSegment( self ):
        return self._segment

    def setSegment( self, newSegment ):
        self._segment = newSegment.strip()
        
    def getSeparator(self):
        if not hasattr(self, "_separator"):
            self._separator = "&"
        return self._separator
    
    def setSeparator(self, separator):
        self._separator = separator

    def setParams(self,params):
        self._params = {}
        if params != None:
            for name in params.keys():
                self.addParam( name, params[name] )

    def addParams(self,params):
        for name in params.keys():
            self.addParam( name, params[name] )

    def addParam( self, name, value ):
        self._params[name.strip()] = value

    def delParam( self, name ):
        if self._params.has_key( name.strip() ):
            del self._params[name.strip()]

    def _encodeParamValue( self, value ): 
        return urllib.quote_plus( str( value ).strip() )

    def _getParamsURLForm( self ):
        l = []
        for name in self._params.keys():
            value = self._params[name]
            if type(value) == list or isinstance(value, UserList):
                for v in value:
                    l.append("%s=%s"%(name, self._encodeParamValue( v )))
            else:
                l.append("%s=%s"%(name, self._encodeParamValue( value )))
        return self._separator.join( l )

    def __str__( self ):
        params = self._getParamsURLForm()
        if params.strip() != "":
            params = "?%s"%self._getParamsURLForm()
        segment = self.getSegment()
        if segment != "":
            segment = "#%s"%segment
        return "%s%s%s"%( self.getBase(), params, segment )


class MailtoURL:
    
    def __init__( self, dest, **params ):
        self._destination = dest
        self.setSubject( params.get("subject", "") )

    def setSubject( self, newSubject ):
        self._subject = newSubject.strip()

    def _encodeParamValue( self, value ):
        return urllib.quote( str( value ) )

    def _getParamsURLForm( self ):
        l = []
        l.append("subject=%s"%self._subject)
        return "&amp;".join(l)

    def __str__( self ):
        res = "mailto:%s"%self._destination
        params = self._getParamsURLForm()
        if params != "":
            res = "%s?%s"%(res, params)
        return res

            

class ShortURLMapper(ObjectHolder):
    
    idxName = "shorturl"
    
    def add( self, tag, newItem ):
        if not tag:
            raise MaKaCError("Invalid tag for short URL : \"%s\""%tag)
        if self.hasKey(tag):
            raise MaKaCError("Short URL tag already used: \"%s\""%tag)
        tree = self._getIdx()
        tree[tag] = newItem
        return tag
    
    def remove( self, item ):
        """removes the specified object from the index.
        """
        tree = self._getIdx()
        if not tree.has_key( item.getUrlTag() ):
            return
        del tree[item.getUrlTag()]
    
        
    