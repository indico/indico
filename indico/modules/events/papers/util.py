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

from indico.core.db import db
from indico.modules.events.contributions import Contribution
from indico.modules.users import User


def _query_contributions_with_user_as_reviewer(event, user):
    query = Contribution.query.with_parent(event)
    query = query.filter(db.or_(Contribution.paper_content_reviewers.any(User.id == user.id),
                                Contribution.paper_layout_reviewers.any(User.id == user.id)),
                         Contribution._paper_revisions.any())
    return query


def get_user_reviewed_contributions(event, user):
    """Get the list of contributions where user already reviewed paper"""
    contribs = _query_contributions_with_user_as_reviewer(event, user).all()
    contribs = [contrib for contrib in contribs if contrib.paper.last_revision.has_user_reviewed(user)]
    return contribs


def get_user_contributions_to_review(event, user):
    """Get the list of contributions where user has paper to review"""
    contribs = _query_contributions_with_user_as_reviewer(event, user).all()
    contribs = [contrib for contrib in contribs if not contrib.paper.last_revision.has_user_reviewed(user)]
    return contribs
