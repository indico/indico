# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.hybrid import hybrid_property

from indico.util.caching import memoize_request
from indico.util.locators import locator_property
from indico.web.flask.util import url_for


class ProposalGroupProxy(object):
    """The object that the proposals can be grouped by.

    It provides all necessary methods for building the URLs, displaying the
    grouping information, etc.
    """

    title_attr = 'title'
    full_title_attr = 'full_title'

    def __init__(self, group):
        self.instance = group

    def __eq__(self, other):
        if isinstance(other, ProposalGroupProxy):
            return self.instance == other.instance
        elif isinstance(other, type(self.instance)):
            return self.instance == other
        else:
            return False

    def __hash__(self):
        return hash(self.instance)

    def __ne__(self, other):
        return not (self == other)

    @property
    def title(self):
        return getattr(self.instance, self.title_attr)

    @property
    def full_title(self):
        return (getattr(self.instance, self.full_title_attr)
                if hasattr(self.instance, self.full_title_attr)
                else self.title)

    @locator_property
    def locator(self):
        return self.instance.locator

    def __repr__(self):
        return '<ProposalGroupProxy: {}>'.format(self.instance)


class ProposalRevisionMixin(object):
    """Properties and methods of a proposal revision."""

    #: The attribute  of the revision used to fetch the proposal object.
    proposal_attr = None
    #: Whether the reviewing process supports multiple revisions per proposal.
    #: If set to false it is assumed that the reviewing process supports only
    #: one revision per proposal.
    revisions_enabled = True

    @property
    def proposal(self):
        # Property to fetch the proposal object. If multiple revisions are
        # disabled, the revision is represented by the proposal object itself.
        return getattr(self, self.proposal_attr) if self.revisions_enabled else self

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


class ProposalMixin(object):
    """
    Classes that represent a proposal object should extend this class (ex:
    Abstract, Paper).
    """

    #: A unique identifier to handle rendering differences between proposal
    #: types
    proposal_type = None
    #: Attribute to retrieve the object with access to the reviewing settings
    call_for_proposals_attr = None
    #: Whether there is support for multiple revisions per proposal or just one
    revisions_enabled = True

    # endpoints
    delete_comment_endpoint = None
    create_comment_endpoint = None
    edit_comment_endpoint = None
    create_review_endpoint = None
    edit_review_endpoint = None
    create_judgment_endpoint = None

    @property
    def cfp(self):
        return getattr(self.event, self.call_for_proposals_attr)

    @property
    def is_in_final_state(self):
        raise NotImplementedError

    def get_revisions(self):
        if self.revisions_enabled:
            raise NotImplementedError
        else:
            return [self]

    def get_last_revision(self):
        if self.revisions_enabled:
            raise NotImplementedError
        else:
            return self

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

    def get_save_judgment_url(self):
        return url_for(self.create_judgment_endpoint, self)


class ProposalCommentMixin(object):
    timeline_item_type = 'comment'

    def can_edit(self, user):
        raise NotImplementedError


class ProposalReviewMixin(object):
    """Mixin for proposal reviews.

    Classes that represent a review of a proposal should extend this class
    (ex: AbstractReview, PaperReview).
    """

    #: A unique identifier to handle rendering differences between timeline
    #: items
    timeline_item_type = 'review'
    #: The revision object that the review refers to
    revision_attr = None
    #: Object used to group reviews together
    group_attr = None
    #: Proxy class to provide the necessary properties and methods to the
    #: review grouping object
    group_proxy_cls = ProposalGroupProxy

    @hybrid_property
    def revision(self):
        return getattr(self, self.revision_attr)

    @property
    def group(self):
        return self.group_proxy_cls(getattr(self, self.group_attr))

    @property
    def score(self):
        return None

    def can_edit(self, user):
        raise NotImplementedError
