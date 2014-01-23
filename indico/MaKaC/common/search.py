# -*- coding: utf-8 -*-
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
        people = AvatarHolder().match(criteria, exact=exactMatch, searchInAuthenticators=searchExt)
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
        # search not obsolete groups
        groups = [ group for group in GroupHolder().match(criteria, searchInAuthenticators=searchExt) if not group.isObsolete()]
        return groups
    else:
        return []
