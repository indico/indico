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

from MaKaC.services.implementation.base import ParameterManager, \
    TextModificationBase
from MaKaC.services.implementation.base import ProtectedModificationService

from MaKaC import conference
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.utils import sortContributionByDate
import MaKaC.webinterface.locators as locators


class MinutesEdit(TextModificationBase, ProtectedModificationService):

    def _checkParams(self):
        ProtectedModificationService._checkParams(self)

        pm = ParameterManager(self._params)

        l = locators.WebLocator()

        # TODO: This chain could (should) be repalced by a more generic
        # locator, something like:
        # l.setParams(self._params)
        # l.getObject() # retrieves whatever object has been extracted

        # will check cotnribution and session as well, as fallback cases
        l.setSubContribution(self._params, 0)
        # will check if it is compiling minutes
        self._compile = self._params.get("compile", False)

        self._target = l.getObject()

        # TODO: change str to some kind of html sanitization
        self._text = pm.extract("value", pType=str, allowEmpty=True)

    def _checkProtection(self):
        if isinstance(self._target, conference.Session) and self._target.canCoordinate(self.getAW()):
            return
        if isinstance(self._target, conference.Contribution) and self._target.canUserSubmit(self._getUser()):
            return
        ProtectedModificationService._checkProtection(self)

    def _handleSet(self):

        # Account for possible retries (due to conflicts)
        # If 'minutesFileId' is defined, there was a previous try
        fileId = ContextManager.setdefault('minutesFileId', None)

        minutes = self._target.getMinutes()
        if not minutes:
            minutes = self._target.createMinutes()
        minutes.setText(self._text, forcedFileId=fileId)

        # save the fileId, in case there is a conflict error
        # in the worst case scenario the file will be rewritten multiple times
        res = minutes.getResourceById('minutes')
        ContextManager.set('minutesFileId', res.getRepositoryId())

    def _handleGet(self):
        if self._compile:
            return self._getCompiledMinutes()
        minutes = self._target.getMinutes()
        if not minutes:
            return None
        else:
            return minutes.getText()

    def _addMinutes(self, minutes, entry):
        if entry.getMinutes():
            minText = entry.getMinutes().getText()
            minutes.append([entry.getTitle(), minText])

    def _getSessionMinutes(self, minutes, session):
        self._addMinutes(minutes, session)
        for contrib in session.getContributionList():
            self._getContributionMinutes(minutes, contrib)

    def _getContributionMinutes(self, minutes, contrib):
        self._addMinutes(minutes, contrib)
        for subContrib in contrib.getSubContributionList():
            self._addMinutes(minutes, subContrib)

    def _getCompiledMinutes(self):
        minutes = []
        entrylist = self._target.getSchedule().getEntries()
        cList = self._target.getContributionList()
        cList.sort(sortContributionByDate)
        for c in entrylist:
            if isinstance(c.getOwner(), conference.SessionSlot):
                self._getSessionMinutes(minutes, c.getOwner().getSession())
            elif isinstance(c.getOwner(), conference.Contribution):
                self._getContributionMinutes(minutes, c.getOwner())
        lb = "<br/>"
        text = "%s (%s)%s" % (self._target.getTitle(),
                              self._target.getStartDate().strftime("%d %b %Y"),
                              lb)
        part = self._target.getParticipation().getPresentParticipantListText()
        if part != "":
            text += "Present: %s%s" % (part, lb)
        uList = self._target.getChairList()
        chairs = ""
        for chair in uList:
            if chairs != "":
                chairs += "; "
            chairs += chair.getFullName()
        if len(uList) > 0:
            text += "Chaired by: %s%s%s" % (chairs, lb, lb)
        for min in minutes:
            text += "==================%s%s%s==================%s%s%s%s" % \
                (lb, min[0], lb, lb, min[1], lb, lb)

        return text


class MinutesDelete(MinutesEdit):
    def _getAnswer(self):
        self._target.removeMinutes()
        if self._target.getMinutes() is None:
            return True
        else:
            return False


methodMap = {
    "edit": MinutesEdit,
    "delete": MinutesDelete
    }
