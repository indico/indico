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

from indico.core.api import IListener


class IAccessControlListener(IListener):

    def protectionChanged(self, obj, oldProtection, newProtection):
        pass

    def accessGranted(self, obj, who):
        """
        Access was granted to a particular user/group/email
        """

    def accessRevoked(self, obj, who):
        """
        Access was revoked for a particular user/group/email
        """

    def modificationGranted(self, obj, who):
        """
        Modification was revoked for a particular user/group/email
        """


    def modificationRevoked(self, obj, who):
        """
        Modification was revoked for a particular user/group/email
        """

    def accessDomainAdded(self, obj, domain):
        pass

    def accessDomainRemoved(self, obj, domain):
        pass


class ITimeActionListener(IListener):

    def dateChanged(self, obj, oldDate, newDate):
        pass

    def startDateChanged(self, obj, oldSdate, sdate):
        pass

    def endDateChanged(self, obj, oldEdate, edate):
        pass

    def startTimeChanged(self, obj, oldSdate, sdate):
        pass

    def endTimeChanged(self, obj, oldEdate, edate):
        pass

    def eventDatesChanged(self, obj, oldStartDate, oldEndDate,
                          newStartDate, newEndDate):
        pass

    def timezoneChanged(self, obj, oldTimezone, timezone):
        pass


class IObjectLifeCycleListener(IListener):

    def created(self, obj, owner):
        pass

    def moved(self, obj, fromOwner, toOwner):
        pass

    def deleted(self, obj, oldOwner):
        pass


class IMetadataChangeListener(IListener):

    def categoryTitleChanged(self, obj, oldTitle, newTitle):
        pass

    def eventTitleChanged(self, obj, oldTitle, newTitle):
        pass

    def contributionTitleChanged(self, obj, oldTitle, newTitle):
        pass

    def infoChanged(self, obj):
        pass

