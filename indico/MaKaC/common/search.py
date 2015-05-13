# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import itertools

from flask import session

from MaKaC.user import AvatarHolder
from MaKaC.conference import ContributionParticipation
from indico.modules.users.util import get_user_by_email


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

        return people
    else:
        return []


def get_authors_from_author_index(event, limit):
    """Fetch the authors of an event with the most contributions. An author is a
    ContributionParticipation object or an Avatar object.

    :param event: The event to fetch the author index from
    :param limit: The limit of the authors to be returned
    :return: A list of authors.
    """
    author_index = event.getAuthorIndex()
    fav_users_emails = (set(itertools.chain.from_iterable(f.all_emails for f in session.user.favorite_users))
                        if session.user else [])
    sorted_authors = [x[0] for x in sorted((p for p in author_index.getParticipations()
                                           if p[0].getEmail() not in fav_users_emails), key=len, reverse=True)]
    authors = []
    # Check if there is a corresponding Avatar for the specific user and use that.
    for author in sorted_authors[:limit]:
        user = get_user_by_email(author.getEmail())
        authors.append(user.as_avatar if user else author)
    return authors


def make_participation_from_obj(obj, contrib_participation=None):
    """Convert a user-like object to a ContributionParticipation

    :param obj: The object to take the values of the ContributionParticipation
                from
    :param contrib_participation: In case the return object has been initialised
                                  outside of the function
    :return: a ContributionParticipation object
    """
    if contrib_participation is None:
        contrib_participation = ContributionParticipation()
    contrib_participation.setTitle(obj.getTitle())
    contrib_participation.setFirstName(obj.getName())
    contrib_participation.setFamilyName(obj.getSurName())
    contrib_participation.setEmail(obj.getEmail())
    contrib_participation.setAddress(obj.getAddress())
    contrib_participation.setFax(obj.getFax())
    contrib_participation.setAffiliation(obj.getAffiliation())
    contrib_participation.setPhone(obj.getPhone())
    return contrib_participation
