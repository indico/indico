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

from xml.sax.saxutils import quoteattr

from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
from MaKaC.webinterface import wcomponents, navigation, urlHandlers
from MaKaC.errors import MaKaCError
from MaKaC.common import Config
from MaKaC.i18n import _

class WAuthorDisplay(wcomponents.WTemplated):
    
    def __init__(self,conf, authId):
        self._conf = conf
        self._authorId = authId

    def _getMaterialHTML(self, contrib):
        lm=[]
        paper=contrib.getPaper()
        if paper is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="paper"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(paper))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallPaper" ))),
                self.htmlText("paper")))
        slides=contrib.getSlides()
        if slides is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="slides"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(slides))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallSlides" ))),
                self.htmlText("slides")))
        poster=contrib.getPoster()
        if poster is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="poster"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(poster))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallPoster" ))),
                self.htmlText("poster")))
        slides=contrib.getSlides()
        video=contrib.getVideo()
        if video is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="video"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(video))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallVideo" ))),
                self.htmlText("video")))
        return ", ".join(lm)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        authorList=self._conf.getAuthorIndex().getById(self._authorId)
        author = None
        if authorList is not None:
            author=authorList[0]
        else:
            raise MaKaCError( _("Not found the author: %s")%self._authorId)
        contribList = []
        for auth in authorList:
            contrib=auth.getContribution()
            url=urlHandlers.UHContributionDisplay.getURL(contrib)
            material = self._getMaterialHTML(contrib)
            if material.strip()!="":
                material = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;( %s )"%material
            contribList.append("""<p style="text-indent: -3em;margin-left:3em"><a href=%s">%s-%s</a>%s</p>"""%(quoteattr(str(url)),self.htmlText(contrib.getId()),self.htmlText(contrib.getTitle()), material ))
        vars["contributions"] = "".join(contribList)
        vars["title"] = author.getTitle() 
        vars["fullName"] = author.getFullName()
        email = author.getEmail()
        vars["mailURL"]=urlHandlers.UHConferenceEmail.getURL(author)   
        vars["email"] = email
        vars["address"] = author.getAddress()
        vars["telephone"] = author.getPhone()
        vars["fax"] = author.getFax()
        vars["organisation"] = author.getAffiliation()
        return vars



class WPAuthorDisplay(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEAuthorDisplay

    def __init__(self, rh, conf, authId):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._authorId = authId

    def _getBody(self,params):
        wc=WAuthorDisplay(self._conf, self._authorId)
        return wc.getHTML()

    def _defineSectionMenu( self ): 
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._authorIndexOpt)
