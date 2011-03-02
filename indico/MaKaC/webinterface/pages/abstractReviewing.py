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


import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
from xml.sax.saxutils import quoteattr
from MaKaC.common import Config
from MaKaC import review
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
from MaKaC.webinterface.pages.conferences import WPConferenceModifAbstractBase

class WPAbstractReviewingSetup(WPConferenceModifAbstractBase):
    """ Tab for setup of general aspects of the abstract reviewing process
    """

    def _setActiveTab( self ):
        self._tabCFAR.setActive()
        self._subTabARSetup.setActive()

    def _getTabContent( self, params ):
        wc = WAbstractReviewingSetup(self._conf)
        params = {}
        return wc.getHTML( params )

class WAbstractReviewingSetup(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractReview"] = self._conf.getConfAbstractReview()
        return vars


class WPAbstractReviewingTeam(WPConferenceModifAbstractBase):
    """ Tab to select the team of abstract reviewing process
    """

    def _setActiveTab( self ):
        self._tabCFAR.setActive()
        self._subTabARTeam.setActive()

    def _getTabContent( self, params ):
        wc = WAbstractReviewingTeam(self._conf)
        params = {}
        return wc.getHTML( params )

class WAbstractReviewingTeam(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        # Get the track ids and titles
        vars["tracks"] = self._conf.getTrackList()
        trackIdsList = []
        coordinatorsByTrack = {}
        for track in self._conf.getTrackList():
            trackIdsList.append(track.getId())
            coordinatorsByTrack[track.getId()] = track.getCoordinatorList()
        vars["conf"] = self._conf
        vars["trackIds"] = trackIdsList
        vars["coordinatorsByTrack"] = coordinatorsByTrack
        return vars

### Classes for the NOTIFICATION TEMPLATES ###
#class for setting up abstract notification templates
class WPConfModifAbstractsReviewingNotifTplBase( WPConferenceModifAbstractBase ):

    def _setActiveTab( self ):
        self._tabCFAR.setActive()
        self._subTabARNotifTpl.setActive()

class WPConfModifAbstractsReviewingNotifTplList( WPConfModifAbstractsReviewingNotifTplBase ):

    def _getTabContent( self, params ):
        wc = WAbstractsReviewingNotifTpl( self._conf )
        return wc.getHTML()

class WAbstractsReviewingNotifTpl( wcomponents.WTemplated ):
    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["conf"] = self._conf
        vars["addNotifTplURL"]=urlHandlers.UHAbstractModNotifTplNew.getURL(self._conf)
        vars["remNotifTplURL"]=urlHandlers.UHAbstractModNotifTplRem.getURL(self._conf)
        return vars

class NotifTplToAddrWrapper:
    _id=""
    _label=""
    _klass=None

    def getId(cls):
        return cls._id
    getId=classmethod(getId)

    def getLabel(cls):
        return _(cls._label)
    getLabel=classmethod(getLabel)

    def getToAddrKlass(cls):
        return cls._klass
    getToAddrKlass=classmethod(getToAddrKlass)

    def addToAddr(cls,tpl):
         tpl.addToAddr(cls._klass())
    addToAddr=classmethod(addToAddr)

    def isSelectedByDefault(cls):
        return False
    isSelectedByDefault = classmethod(isSelectedByDefault)


class NotifTplToAddrSubmitterWrapper(NotifTplToAddrWrapper):

    _id="submitter"
    _klass=review.NotifTplToAddrSubmitter
    _label="Submitters"

    def isSelectedByDefault(cls):
        return True
    isSelectedByDefault = classmethod(isSelectedByDefault)

class NotifTplToAddrPrimaryAuthorsWrapper(NotifTplToAddrWrapper):

    _id="primaryAuthors"
    _label= "Primary authors"
    _klass=review.NotifTplToAddrPrimaryAuthors


class NotifTplToAddrsFactory:

    _avail_toAddrs={
        NotifTplToAddrSubmitterWrapper.getId():NotifTplToAddrSubmitterWrapper,\
        NotifTplToAddrPrimaryAuthorsWrapper.getId():NotifTplToAddrPrimaryAuthorsWrapper}

    def getToAddrList(cls):
        return cls._avail_toAddrs.values()
    getToAddrList=classmethod(getToAddrList)

    def getToAddrById(cls,id):
        return cls._avail_toAddrs.get(id,None)
    getToAddrById=classmethod(getToAddrById)


class WConfModCFANotifTplNew(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            res.append("""<input name="toAddrs" type="checkbox" value=%s>%s<br>"""%(quoteattr(toAddr.getId()),self.htmlText(toAddr.getLabel())))
        return "&nbsp;".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"] = quoteattr(str(urlHandlers.UHAbstractModNotifTplNew.getURL(self._conf)))
        vars["errors"] = vars.get("errorList",[])
        vars["title"] = quoteattr(str(vars.get("title","")))
        vars["description"] = self.htmlText(vars.get("description",""))
        vars["subject"] = quoteattr(str(vars.get("subject","")))
        vars["body"] = self.htmlText(vars.get("body",""))
        vars["fromAddr"] = quoteattr(str(vars.get("fromAddr","")))
        vars["CCAddrs"] = quoteattr(str(",".join(vars.get("ccList",[]))))
        vars["toAddrs"] = self._getToAddrsHTML()
        vars["availableConditions"] = NotifTplConditionsFactory.getConditionList()
        return vars


class WConfModCFANotifTplEditData(wcomponents.WTemplated):

    def __init__(self,notifTpl):
        self._notifTpl=notifTpl

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            checked = ""
            if self._notifTpl:
                if self._notifTpl.hasToAddr(toAddr.getToAddrKlass()):
                    checked = "checked"
            else:
                if toAddr.isSelectedByDefault():
                    checked = "checked"
            res.append("""<input name="toAddrs" type="checkbox" value=%s %s>%s<br>"""%(quoteattr(toAddr.getId()),checked,self.htmlText(toAddr.getLabel())))
        return "&nbsp;".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"] = quoteattr(str(urlHandlers.UHAbstractModNotifTplEdit.getURL(self._notifTpl)))
        vars["errors"] = vars.get("errorList",[])
        if not vars.has_key("title"):
            vars["title"] = quoteattr(str(self._notifTpl.getName()))
        else:
            vars["title"] = quoteattr(str(vars["title"]))
        if not vars.has_key("description"):
            vars["description"] = self.htmlText(self._notifTpl.getDescription())
        else:
            vars["description"] = self.htmlText(vars["description"])
        if not vars.has_key("subject"):
            vars["subject"] = quoteattr(str(self._notifTpl.getTplSubjectShow(EmailNotificator.getVarList())))
        else:
            vars["subject"] = quoteattr(str(vars["subject"]))
        if not vars.has_key("body"):
            vars["body"] = self.htmlText(self._notifTpl.getTplBodyShow(EmailNotificator.getVarList()))
        else:
            vars["body"] = self.htmlText(vars["body"])
        if not vars.has_key("fromAddr"):
            vars["fromAddr"] = quoteattr(str(self._notifTpl.getFromAddr()))
        else:
            vars["fromAddr"] = quoteattr(str(vars["fromAddr"]))
        vars["toAddrs"] = self._getToAddrsHTML()
        if not vars.has_key("ccList"):
            vars["CCAddrs"] = quoteattr(str(",".join(self._notifTpl.getCCAddrList())))
        else:
            vars["CCAddrs"] = quoteattr(str(",".join(vars["ccList"])))
        return vars

class WPModCFANotifTplNew(WPConfModifAbstractsReviewingNotifTplBase):

    def _getTabContent(self,params):
        wc = WConfModCFANotifTplNew(self._conf)
        params["errorList"]=params.get("errorList",[])
        return wc.getHTML(params)

    def getJSFiles(self):
        return WPConfModifAbstractsReviewingNotifTplBase.getJSFiles(self) + \
           self._includeJSPackage('Abstracts')

class WPModCFANotifTplBase(WPConferenceModifAbstractBase):

    def __init__(self, rh, notifTpl):
        WPConferenceModifAbstractBase.__init__(self, rh, notifTpl.getConference())
        self._notifTpl = notifTpl

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHAbstractModNotifTplDisplay.getURL( self._notifTpl ) )
        self._tabPreview = self._tabCtrl.newTab( "preview", _("Preview"), \
                urlHandlers.UHAbstractModNotifTplPreview.getURL( self._notifTpl ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

#    def _applyFrame( self, body ):
#        frame = wcomponents.WNotifTPLModifFrame( self._notifTpl, self._getAW() )
#        p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
#            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
#            "confModifURLGen": urlHandlers.UHConfModifCFA.getURL}
#        return frame.getHTML( body, **p )

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WNotifTplBannerModif(self._notifTpl).getHTML()
        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner + body

    def _getTabContent( self, params ):
        return "nothing"


class WPModCFANotifTplDisplay(WPModCFANotifTplBase):

    def __init__(self, rh, notifTpl):
        WPModCFANotifTplBase.__init__(self, rh, notifTpl)
        self._conf = self._notifTpl.getConference()

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent(self, params):
        wc = WConfModCFANotifTplDisplay(self._conf, self._notifTpl)
        return wc.getHTML()


class WPModCFANotifTplEdit(WPModCFANotifTplBase):

    def __init__(self, rh, notifTpl):
        WPConferenceModifAbstractBase.__init__(self, rh, notifTpl.getConference())
        self._notifTpl=notifTpl


    def _getTabContent(self, params):
        wc=WConfModCFANotifTplEditData(self._notifTpl)
        params["errorList"]=params.get("errorList",[])
        return wc.getHTML(params)

    def getJSFiles(self):
        return WPConferenceModifAbstractBase.getJSFiles(self) + \
            self._includeJSPackage('Abstracts')



class WPModCFANotifTplPreview(WPModCFANotifTplBase):

    def _setActiveTab(self):
        self._tabPreview.setActive()

    def _getTabContent(self, params):
        wc = WConfModCFANotifTplPreview(self._notifTpl)
        return wc.getHTML()


class WConfModCFANotifTplPreview(wcomponents.WTemplated):

    def __init__(self,notifTpl):
        self._notifTpl=notifTpl

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        conf = self._notifTpl.getConference()
        vars["conf"] = conf
        if conf.getAbstractMgr().getAbstractList():
            abstract = conf.getAbstractMgr().getAbstractList()[0]
            notif=EmailNotificator().apply(abstract,self._notifTpl)
            vars["From"]=notif.getFromAddr()
            vars["to"]=notif.getToList()
            vars["cc"]=notif.getCCList()
            vars["subject"]=notif.getSubject()
            vars["body"] = notif.getBody()
        else:
            vars["From"]= vars["to"] = vars["cc"] = vars["subject"]= _("No preview available")
            vars["body"] = _("An abstract must be submitted to display the preview")
        vars["cfaURL"]=quoteattr(str(urlHandlers.UHConfModifCFA.getURL(conf)))
        return vars

class NotifTplConditionWrapper:
    _id=""
    _label=""
    _klass=None

    def getId(cls):
        return cls._id
    getId=classmethod(getId)

    def getLabel(cls):
        return _(cls._label)
    getLabel=classmethod(getLabel)

    def getConditionKlass(cls):
        return cls._klass
    getConditionKlass=classmethod(getConditionKlass)

    def addCondition(cls,tpl,**data):
        pass
    addCondition=classmethod(addCondition)

    def needsDialog(cls,**data):
        return False
    needsDialog=classmethod(needsDialog)

    def getDialogKlass(cls):
        return None
    getDialogKlass=classmethod(getDialogKlass)


class NotifTplCondAcceptedWrapper(NotifTplConditionWrapper):

    _id="accepted"
    _label= _("in status ACCEPTED")
    _klass=review.NotifTplCondAccepted

    @classmethod
    def addCondition(cls,tpl,**data):
        cType=data.get("contribType","--any--")
        t=data.get("track","--any--")
        tpl.addCondition(cls._klass(track=t,contribType=cType))

    @classmethod
    def needsDialog(cls,**data):
        if data.has_key("contribType") and data["contribType"]!="":
            return False
        return True

    @classmethod
    def getDialogKlass(cls):
        return WPModNotifTplCondAcc


class NotifTplCondRejectedWrapper(NotifTplConditionWrapper):

    _id="rejected"
    _label= _("in status REJECTED")
    _klass=review.NotifTplCondRejected

    @classmethod
    def addCondition(cls,tpl,**data):
        tpl.addCondition(cls._klass())

class NotifTplCondMergedWrapper(NotifTplConditionWrapper):

    _id="merged"
    _label= _("in status MERGED")
    _klass=review.NotifTplCondMerged

    @classmethod
    def addCondition(cls,tpl,**data):
        tpl.addCondition(cls._klass())


class NotifTplConditionsFactory:

    _avail_conds={
        NotifTplCondAcceptedWrapper.getId():NotifTplCondAcceptedWrapper,\
        NotifTplCondRejectedWrapper.getId():NotifTplCondRejectedWrapper,\
        NotifTplCondMergedWrapper.getId():NotifTplCondMergedWrapper}

    def getConditionList(cls):
        return cls._avail_conds.values()
    getConditionList=classmethod(getConditionList)

    def getConditionById(cls,id):
        return cls._avail_conds.get(id,None)
    getConditionById=classmethod(getConditionById)


class WConfModNotifTplCondAcc(wcomponents.WTemplated):

    def __init__(self,tpl):
        self._notifTpl=tpl

    def _getContribTypeItemsHTML(self):
        res=["""<option value="--any--">--any--</option>""",
                """<option value="--none--">--none--</option>"""]
        for t in self._notifTpl.getConference().getContribTypeList():
            res.append("""<option value=%s>%s</option>"""%(quoteattr(t.getId()),self.htmlText(t.getName())))
        return "".join(res)

    def _getTrackItemsHTML(self):
        res=["""<option value="--any--">--any--</option>""",
                """<option value="--none--">--none--</option>"""]
        for t in self._notifTpl.getConference().getTrackList():
            res.append("""<option value=%s>%s</option>"""%(quoteattr(t.getId()),self.htmlText(t.getTitle())))

        return "".join(res)
    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=urlHandlers.UHConfModNotifTplConditionNew.getURL(self._notifTpl)
        vars["condType"]=quoteattr(str(NotifTplCondAcceptedWrapper.getId()))
        vars["contribTypeItems"]=self._getContribTypeItemsHTML()
        vars["trackItems"]=self._getTrackItemsHTML()
        return vars


class WPModNotifTplCondAcc(WPModCFANotifTplBase):

    def _getTabContent( self, params ):
        wc=WConfModNotifTplCondAcc(self._notifTpl)
        return wc.getHTML()


class WConfModCFANotifTplDisplay(wcomponents.WTemplated):

    def __init__(self, conf, notifTpl):
        self._conf = conf
        self._notifTpl = notifTpl

    def _getConditionItemsHTML(self):
        res=[]
        for cond in NotifTplConditionsFactory.getConditionList():
            res.append("<option value=%s>%s</option>"""%(quoteattr(cond.getId()),self.htmlText(cond.getLabel())))
        return "".join(res)

    def _getConditionsHTML(self):
        res=[]
        for cond in self._notifTpl.getConditionList():
            caption=""
            if isinstance(cond,review.NotifTplCondAccepted):
                track=cond.getTrack()
                if track is None or track=="":
                    track="--none--"
                elif track not in ["--none--","--any--"]:
                    track=track.getTitle()
                cType=cond.getContribType()
                if cType is None or cType=="":
                    cType="--none--"
                elif cType not in ["--none--","--any--"]:
                    cType=cType.getName()
                caption= _("""ACCEPTED - type: %s - track: %s""")%(self.htmlText(cType),self.htmlText(track))
            elif isinstance(cond,review.NotifTplCondRejected):
                caption= _("""REJECTED""")
            elif isinstance(cond,review.NotifTplCondMerged):
                caption= _("""MERGED""")
            res.append(""" <input type="image" src="%s" onclick="javascript:this.form.selCond.value = '%s'; this.form.submit();return false;"> %s"""%(Config.getInstance().getSystemIconURL( "remove" ), cond.getId(), caption))
        return "<br>".join(res)

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            if self._notifTpl.hasToAddr(toAddr.getToAddrKlass()):
                res.append("%s"%self.htmlText(toAddr.getLabel()))
        return ", ".join(res)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["name"] = self._notifTpl.getName()
        vars["description"] = self._notifTpl.getDescription()
        vars["From"] = self._notifTpl.getFromAddr()
        vars["toAddrs"] = self._getToAddrsHTML()
        vars["CCAddrs"]=",".join(self._notifTpl.getCCAddrList())
        vars["subject"] = self._notifTpl.getTplSubjectShow(EmailNotificator.getVarList())
        vars["body"] = self._notifTpl.getTplBodyShow(EmailNotificator.getVarList())
        vars["conditions"]=self._getConditionsHTML()
        vars["availableConditions"]=self._getConditionItemsHTML()
        vars["remConditionsURL"]=quoteattr(str(urlHandlers.UHConfModNotifTplConditionRem.getURL(self._notifTpl)))
        vars["newConditionURL"]=quoteattr(str(urlHandlers.UHConfModNotifTplConditionNew.getURL(self._notifTpl)))
        vars["modifDataURL"]=quoteattr(str(urlHandlers.UHAbstractModNotifTplEdit.getURL(self._notifTpl)))
        return vars

### End of Notification Templates classes ###
