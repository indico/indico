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

class ConferenceAbstractsBookCorrespondingAuthor( ConferenceTextModificationBase ):

    def _handleSet(self):
        self._conf.getBOAConfig().setCorrespondingAuthor(self._value)

    def _handleGet(self):
        return self._conf.getBOAConfig().getCorrespondingAuthor()


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
    "abstractsbook.changeCorrespondingAuthor": ConferenceAbstractsBookCorrespondingAuthor,
    "abstractsbook.toggleCache": ConferenceAbstractsBookToggleCache,
    "abstractsbook.dirtyCache": ConferenceAbstractsBookDirtyCache
    }
