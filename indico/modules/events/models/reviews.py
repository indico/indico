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

from __future__ import unicode_literals

from sqlalchemy.ext.hybrid import hybrid_property

from indico.util.caching import memoize_request
from indico.util.i18n import _
from indico.util.struct.enum import RichIntEnum
from indico.web.flask.util import url_for


class ProposalMixin(object):
    proposal_type = None
    call_for_proposals_attr = None

    # endpoints
    delete_comment_endpoint = None
    create_comment_endpoint = None
    edit_comment_endpoint = None
    create_review_endpoint = None
    edit_review_endpoint = None

    @property
    def cfp(self):
        return getattr(self.event_new, self.call_for_proposals_attr)

    def can_comment(self, user):
        raise NotImplementedError

    def can_review(self, user, check_state=False):
        raise NotImplementedError

    def get_delete_comment_url(self, comment):
        return url_for(self.delete_comment_endpoint, comment)

    def get_save_comment_url(self, comment=None):
        return (url_for(self.edit_comment_endpoint, comment)
                if comment
                else url_for(self.create_comment_endpoint, self))

    def get_save_review_url(self, group=None, review=None):
        return (url_for(self.edit_review_endpoint, review)
                if review
                else url_for(self.create_review_endpoint, self, group))

    def get_timeline(self, user=None):
        raise NotImplementedError

    def get_reviews(self, group=None, user=None):
        reviews = self.reviews[:]
        if group:
            reviews = [x for x in reviews if x.group == group]
        if user:
            reviews = [x for x in reviews if x.user == user]
        return reviews

    def get_reviewed_for_groups(self, user, include_reviewed=False):
        raise NotImplementedError

    @memoize_request
    def get_reviewer_render_data(self, user):
        groups = self.get_reviewed_for_groups(user, include_reviewed=True)
        reviews = {x.group: x for x in self.get_reviews(user=user)}
        reviewed_groups = {x.group for x in reviews.itervalues()}
        missing_groups = groups - reviewed_groups
        return {'groups': groups,
                'missing_groups': missing_groups,
                'reviewed_groups': reviewed_groups,
                'reviews': reviews}


class ProposalCommentMixin(object):
    timeline_item_type = 'comment'

    def can_edit(self, user):
        raise NotImplementedError


class ProposalCommentVisibility(RichIntEnum):
    """Most to least restrictive visibility for abstract comments"""
    __titles__ = [None,
                  _("Visible only to judges"),
                  _("Visible to conveners and judges"),
                  _("Visible to reviewers, conveners, and judges"),
                  _("Visible to contributors, reviewers, conveners, and judges"),
                  _("Visible to all users")]
    judges = 1
    conveners = 2
    reviewers = 3
    contributors = 4
    users = 5


class ProposalReviewMixin(object):
    timeline_item_type = 'review'
    proposal_relationship = None
    group_relationship = None

    @hybrid_property
    def proposal(self):
        return getattr(self, self.proposal_relationship)

    @property
    def group(self):
        return getattr(self, self.group_relationship)

    @property
    def visibility(self):
        return ProposalCommentVisibility.reviewers

    @property
    def score(self):
        return None

    def can_edit(self, user):
        raise NotImplementedError
