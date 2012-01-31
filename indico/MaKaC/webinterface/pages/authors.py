# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from xml.sax.saxutils import quoteattr

from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
from MaKaC.webinterface import wcomponents, navigation, urlHandlers
from MaKaC.errors import MaKaCError
from MaKaC.common import Config
from MaKaC.i18n import _

class WAuthorDisplay(wcomponents.WTemplated):

    def __init__(self,contrib, authId):
        self._conf = contrib.getConference()
        self._contrib = contrib
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
        authorObj = self._contrib.getAuthorById(self._authorId)
        if authorObj is None:
            raise MaKaCError( _("Not found the author: %s")%self._authorId)
        authorList=self._conf.getAuthorIndex().getByAuthorObj(authorObj)
        author = None
        if authorList is not None:
            author=authorList[0]
        else:
            raise MaKaCError( _("Not found the author: %s")%self._authorId)
        contribList = []
        for auth in authorList:
            contrib=auth.getContribution()
            if contrib is not None:
                url=urlHandlers.UHContributionDisplay.getURL(contrib)
                material = self._getMaterialHTML(contrib)
                if material.strip()!="":
                    material = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;( %s )"%material
                    contribList.append("""<p style="text-indent: -3em;margin-left:3em"><a href=%s">%s-%s</a>%s</p>"""%(quoteattr(str(url)),self.htmlText(contrib.getId()),self.htmlText(contrib.getTitle()), material ))
        vars["contributions"] = "".join(contribList)
        vars["fullName"] = author.getFullName()
        vars["mailURL"]=urlHandlers.UHConferenceEmail.getURL(author)
        vars["mailIcon"]=Config.getInstance().getSystemIconURL("mail_big")
        vars["address"] = author.getAddress()
        vars["telephone"] = author.getPhone()
        vars["fax"] = author.getFax()
        vars["organisation"] = author.getAffiliation()
        return vars



class WPAuthorDisplay(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEAuthorDisplay

    def __init__(self, rh, contrib, authId):
        WPConferenceDefaultDisplayBase.__init__(self, rh, contrib.getConference())
        self._authorId = authId
        self._contrib = contrib

    def _getBody(self,params):
        wc=WAuthorDisplay(self._contrib, self._authorId)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._authorIndexOpt)
