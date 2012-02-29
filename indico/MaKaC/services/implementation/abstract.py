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


from MaKaC.services.implementation.conference import ConferenceModifBase, ConferenceTextModificationBase


class ConferenceAbstractsBookAdditionalText( ConferenceTextModificationBase ):

    def _handleSet(self):
        self._conf.getBOAConfig().setText(self._value)

    def _handleGet(self):
        return self._conf.getBOAConfig().getText()


class ConferenceAbstractsBookSortBy( ConferenceTextModificationBase ):

    def _handleSet(self):
        self._conf.getBOAConfig().setSortBy(self._value)

    def _handleGet(self):
        return self._conf.getBOAConfig().getSortBy()


class ConferenceAbstractsBookToggleCache (ConferenceModifBase):
    """
    Toggles the state of the BOA cache (enabled or not)
    """

    def _getAnswer(self):
        state = self._conf.getBOAConfig().isCacheEnabled()
        self._conf.getBOAConfig().setCache(not state)
        return not state


class ConferenceAbstractsBookDirtyCache (ConferenceModifBase):
    """
    Dirties the BOA cache (forces refresh next time)
    """

    def _getAnswer(self):
        self._conf.getBOAConfig()._notifyModification()


methodMap = {
    "abstractsbook.changeAdditionalText": ConferenceAbstractsBookAdditionalText,
    "abstractsbook.changeSortBy": ConferenceAbstractsBookSortBy,
    "abstractsbook.toggleCache": ConferenceAbstractsBookToggleCache,
    "abstractsbook.dirtyCache": ConferenceAbstractsBookDirtyCache
    }
