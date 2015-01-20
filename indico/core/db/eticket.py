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

from persistent import Persistent


class ETicket(Persistent):
    """
    This class manages the configuration of the ETicket module.
    """

    def __init__(self):
        self._enabled = False
        self._attachedToEmail = False
        self._showInConferenceMenu = False
        self._showAfterRegistration = False

    def isEnabled(self):
        return self._enabled

    def setEnabled(self, enabled):
        self._enabled = enabled

    def isAttachedToEmail(self):
        return self._attachedToEmail

    def setAttachedToEmail(self, attachedToEmail):
        self._attachedToEmail = attachedToEmail

    def isShownInConferenceMenu(self):
        return self._showInConferenceMenu

    def setShowInConferenceMenu(self, showInConferenceMenu):
        self._showInConferenceMenu = showInConferenceMenu

    def isShownAfterRegistration(self):
        return self._showAfterRegistration

    def setShowAfterRegistration(self, showAfterRegistration):
        self._showAfterRegistration = showAfterRegistration

    def clone(self):
        e_ticket = ETicket()
        e_ticket.setEnabled(self.isEnabled())
        e_ticket.setAttachedToEmail(self.isAttachedToEmail())
        e_ticket.setShowInConferenceMenu(self.isShownInConferenceMenu())
        e_ticket.setShowAfterRegistration(self.isShownAfterRegistration())
        return e_ticket
