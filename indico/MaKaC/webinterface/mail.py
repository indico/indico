# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.


class GenericNotification:
    def __init__(self, data=None):
        if data is None:
            self._fromAddr = ""
            self._replyAddr = ""
            self._toList = []
            self._ccList = []
            self._bccList = []
            self._subject = ""
            self._body = ""
            self._contenttype = "text/plain"
            self._attachments = []
        else:
            self._fromAddr = data.get("fromAddr", "")
            self._replyAddr = data.get('replyAddr', '')
            self._toList = data.get("toList", [])
            self._ccList = data.get("ccList", [])
            self._bccList = data.get("bccList", [])
            self._subject = data.get("subject", "")
            self._body = data.get("body", "")
            self._contenttype = data.get("content-type", "text/plain")
            self._attachments = data.get("attachments", [])

    def getAttachments(self):
        return self._attachments

    def addAttachment(self, attachment):
        """
        Attachment is a dictionary with two keys:
        - name: containing the filename of the file
        - binary: containing the file data
        """

        self._attachments.append(attachment)

    def getContentType(self):
        return self._contenttype

    def setContentType(self, contentType):
        self._contenttype = contentType

    def getFromAddr(self):
        return self._fromAddr

    def setFromAddr(self, fromAddr):
        if fromAddr is None :
            return False
        self._fromAddr = fromAddr
        return True

    def getToList(self):
        return self._toList

    def setToList(self, toList):
        if toList is None :
            return False
        self._toList = toList
        return True

    def getCCList(self):
        return self._ccList

    def setCCList(self, ccList):
        if ccList is None :
            return False
        self._ccList = ccList
        return True

    def setBCCList(self, bccList):
        if bccList is None :
            return False
        self._bccList = bccList
        return True

    def getBCCList(self):
        return self._bccList

    def getSubject(self):
        return self._subject

    def setSubject(self, subject):
        if subject is None :
            return False
        self._subject = subject
        return True

    def getBody(self):
        return self._body

    def setBody(self, body):
        if body is None :
            return False
        self._body = body
        return True
