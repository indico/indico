# -*- coding: utf-8 -*-
##
## $Id: news.py,v 1.4 2009/02/12 13:46:03 jose Exp $
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

import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.pages.main import WPMainBase
import MaKaC.webinterface.wcomponents as wcomponents      
from MaKaC.modules.base import ModulesHolder

class WPNews(WPMainBase):

    def _getBody(self, params):
        wc = WNews()
        return wc.getHTML()
    
    def _getTitle(self):
        return WPMainBase._getTitle(self) + " - " + _("News")


class WNews(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        newsModule=ModulesHolder().getById("news")
        newslist=[]
        newsTypes = newsModule.getNewsTypes()
        for id, label in newsTypes:
            newslist.append( (label, []) )
        newstypesIds = map(lambda (x,y): x, newsTypes)
        for newItem in newsModule.getNewsItemsList():
            newslist[newstypesIds.index(newItem.getType())][1].append(newItem)
        vars["news"]=newslist
        return vars
        
