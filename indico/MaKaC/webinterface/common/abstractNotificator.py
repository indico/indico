# -*- coding: utf-8 -*-
##
## $Id: abstractNotificator.py,v 1.15 2008/06/19 16:07:11 jose Exp $
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

"""
"""
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.review as review
from MaKaC.webinterface.mail import GenericMailer
from MaKaC.webinterface.common.baseNotificator import TplVar, Notification
from MaKaC.errors import MaKaCError
from MaKaC.i18n import _
from MaKaC.common.info import HelperMaKaCInfo

class ConfTitleTplVar(TplVar):
    _name="conference_title"
    _description=""

    def getValue(cls,abstract):
        return abstract.getConference().getTitle()
    getValue=classmethod(getValue)


class ConfURLTplVar(TplVar):
    _name="conference_URL"
    _description=""

    def getValue(cls,abstract):
        return str(urlHandlers.UHConferenceDisplay.getURL(abstract.getConference()))
    getValue=classmethod(getValue)


class AbsTitleTplVar(TplVar):
    _name="abstract_title"
    _description=""

    def getValue(cls,abstract):
        return abstract.getTitle()
    getValue=classmethod(getValue)


class AbsReviewCommentsTplVar(TplVar):
    _name="abstract_review_comments"
    _description=""

    def getValue(cls,abstract):
        st=abstract.getCurrentStatus()
        if isinstance(st, review.AbstractStatusAccepted) or \
                isinstance(st, review.AbstractStatusRejected) or \
                isinstance(st, review.AbstractStatusWithdrawn) or \
                isinstance(st, review.AbstractStatusDuplicated) or \
                isinstance(st, review.AbstractStatusMerged):
            return st.getComments()
        return ""
    getValue=classmethod(getValue)


class AbsTrackTplVar(TplVar):
    _name="abstract_track"
    _description=""

    def getValue(cls,abstract):
        status=abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusAccepted):
            if status.getTrack() is not None:
                return status.getTrack().getTitle()
        return _("""--_("not specified")--""")
    getValue=classmethod(getValue)


class AbsContribTypeTplVar(TplVar):
    _name="contribution_type"
    _description=""

    def getValue(cls,abstract):
        status=abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusAccepted):
            if status.getType() is not None:
                return status.getType().getName()
        return _("""--_("not specified")--""")
    getValue=classmethod(getValue)


class AbsSubFisrtNameTplVar(TplVar):
    _name="submitter_first_name"
    _description=""

    def getValue(cls,abstract):
        return abstract.getSubmitter().getFirstName()
    getValue=classmethod(getValue)


class AbsSubFamNameTplVar(TplVar):
    _name="submitter_family_name"
    _description=""

    def getValue(cls,abstract):
        return abstract.getSubmitter().getSurName()
    getValue=classmethod(getValue)


class AbsSubTitleTplVar(TplVar):
    _name="submitter_title"
    _description=""

    def getValue(cls,abstract):
        return abstract.getSubmitter().getTitle()
    getValue=classmethod(getValue)


class AbsURLTplVar(TplVar):
    _name="abstract_URL"
    _description=""

    def getValue(cls,abstract):
        return str(urlHandlers.UHAbstractDisplay.getURL(abstract))
    getValue=classmethod(getValue)


class AbsIDTplVar(TplVar):
    _name="abstract_id"
    _description=""

    def getValue(cls,abstract):
        return str(abstract.getId())
    getValue=classmethod(getValue)


class MergedAbsIDTplVar(TplVar):
    _name="merge_target_abstract_id"
    _description=""

    def getValue(cls,abstract):
        status=abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusMerged):
            return str(status.getTargetAbstract().getId())
        return ""
    getValue=classmethod(getValue)

class MergedAbsTitleTplVar(TplVar):
    _name="merge_target_abstract_title"
    _description=""

    def getValue(cls,abstract):
        status=abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusMerged):
            return str(status.getTargetAbstract().getTitle())
        return ""
    getValue=classmethod(getValue)

class MergedAbsSubFamNameTplVar(TplVar):
    _name="merge_target_submitter_family_name"
    _description=""

    def getValue(cls,abstract):
        status=abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusMerged):
            return status.getTargetAbstract().getSubmitter().getSurName()
        return ""
    getValue=classmethod(getValue)

class MergedAbsSubFirstNameTplVar(TplVar):
    _name="merge_target_submitter_first_name"
    _description=""

    def getValue(cls,abstract):
        status=abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusMerged):
            return status.getTargetAbstract().getSubmitter().getFirstName()
        return ""
    getValue=classmethod(getValue)

class AbsPrimAuthTplVar(TplVar):
    _name="primary_authors"
    _description=""

    def getValue(cls,abstract):
        l=[]
        for author in abstract.getPrimaryAuthorList():
            tmp="%s"%author.getSurName()
            if author.getTitle()!="":
                tmp="%s %s"%(author.getTitle(),tmp)
            l.append(tmp)
        return ", ".join(l)
    getValue=classmethod(getValue)

class Notificator:
    _vars=[ConfTitleTplVar,ConfURLTplVar,AbsTitleTplVar,AbsTrackTplVar,
            AbsContribTypeTplVar,AbsSubFisrtNameTplVar,
            AbsSubFamNameTplVar,AbsSubTitleTplVar,AbsURLTplVar,AbsIDTplVar,
            MergedAbsIDTplVar,MergedAbsTitleTplVar,MergedAbsSubFamNameTplVar, MergedAbsSubFirstNameTplVar, AbsPrimAuthTplVar, AbsReviewCommentsTplVar]

    def getVarList(cls):
        return cls._vars
    getVarList=classmethod(getVarList)
    
    def _getVars(self,abstract):
        d={}
        for v in self.getVarList():
            d[v.getName()]=v.getValue(abstract)
        return d


class EmailNotificator(Notificator):
    
    def apply(self,abstract,tpl):
        vars=self._getVars(abstract)
        subj=tpl.getTplSubject()%vars
        try:
            b=tpl.getTplBody()%vars
        except ValueError, e:
            raise MaKaCError( _("Some of the the notification template's tags are invalid. Note that the format of the tags should be: %(tag_name)s"))
        fa=tpl.getFromAddr()
        cc=tpl.getCCAddrList()
        tl = []
        for user in tpl.getToAddrs(abstract):
            if not user.getEmail() in tl:
                tl.append(user.getEmail())
        return Notification(subject=subj,body=b,fromAddr=fa,toList=tl,ccList=cc)
    
    def notify(self,abstract,tpl):
        #if no from address is specified we should put the default one
        if tpl.getFromAddr().strip() == "":
            tpl.setFromAddr(tpl.getConference().getSupportEmail(returnNoReply=True))

        sm=GenericMailer.send(self.apply(abstract,tpl))
        
