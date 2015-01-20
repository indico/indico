# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the FreeSoftware Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Event-related database objects
"""

# 3rd party imports
from persistent import Persistent

# indico imports
from indico.util.fossilize import fossilizes
from indico.core.fossils.event import ISupportInfoFossil
from indico.core.db import DBMgr

# legacy imports
from indico.core.config import Config
from MaKaC.common.fossilize import IFossil


class SupportInfo(Persistent):
    """
    Stores support-related information for events
    """

    fossilizes(ISupportInfoFossil)

    def __init__(self, owner, caption="", email="", telephone=""):
        self._owner = owner
        self._caption = caption
        self._email = email
        self._telephone = telephone

    def getOwner(self):
        return self._owner

    def getCaption(self):
        return self._caption

    def setCaption(self, caption):
        self._caption = caption

    def getEmail(self, returnNoReply=False, caption=False):
        """
        Returns the support email address associated with the conference
        :param returnNoReply: Return no-reply address in case there's no support e-mail (default True)
        :type returnNoReply: bool

        """
        if self._email.strip() == "" and returnNoReply:
            # In case there's no conference support e-mail, return the no-reply
            # address, and the 'global' support e-mail if there isn't one
            return Config.getInstance().getNoReplyEmail()
        else:
            if caption and self._caption:
                return '"%s" <%s>' % (self._caption, self._email)
            else:
                return self._email

    def setEmail( self, email ):
        self._email = email.strip()

    def hasEmail( self ):
        return self._email != "" and self._email != None

    def getTelephone(self):
        return self._telephone

    def setTelephone( self, telephone ):
        self._telephone = telephone.strip()

    def hasTelephone( self ):
        return self._telephone != "" and self._telephone != None

    def isEmpty(self):
        return not self._email and not self._telephone

    def clone(self, owner):
        supportInfo = SupportInfo(owner)
        supportInfo.setCaption(self.getCaption())
        supportInfo.setEmail(self.getEmail())
        supportInfo.setTelephone(self.getTelephone())
        return supportInfo
