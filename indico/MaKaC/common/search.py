# -*- coding: utf-8 -*-
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

from MaKaC.user import AvatarHolder, GroupHolder
from MaKaC.conference import ConferenceHolder

def searchUsers(surName="", name="", organisation="", email="", conferenceId=None, exactMatch=True, searchExt=False):

    if surName != "" or name != "" or organisation != "" or email != "":
        # build criteria
        criteria = {
            "surName": surName,
            "name": name,
            "organisation": organisation,
            "email": email
        }
        # search users
        people = AvatarHolder().match(criteria, exact=exactMatch, forceWithoutExtAuth=(not searchExt))
        # search authors
        if conferenceId != None:
            try:
                conference = ConferenceHolder().getById(conferenceId)
                authorIndex = conference.getAuthorIndex()
                authors = authorIndex.match(criteria, exact=exactMatch)
                # merge with users
                users = people
                people = []
                emails = []
                for user in users:
                    people.append(user)
                    emails.extend(user.getEmails())
                for author in authors:
                    if author.getEmail() not in emails:
                        people.append(author)
            except Exception:
                pass
        return people
    else:
        return []


def searchGroups(group="", searchExt=False):
    if group != "":
        # build criteria
        criteria = {
            "name": group
        }
        # search groups
        groups = GroupHolder().match(criteria, forceWithoutExtAuth=(not searchExt))
        return groups
    else:
        return []
