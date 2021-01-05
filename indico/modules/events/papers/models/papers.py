# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.settings import AttributeProxyProperty
from indico.modules.events.models.reviews import ProposalMixin
from indico.modules.events.papers.models.revisions import PaperRevisionState
from indico.util.locators import locator_property
from indico.util.string import return_ascii


class Paper(ProposalMixin):
    """Proxy class to facilitate access to all paper-related properties."""

    proxied_attr = 'contribution'

    # Proposal mixin properties
    proposal_type = 'paper'
    call_for_proposals_attr = 'cfp'
    revisions_enabled = True

    def __init__(self, contribution):
        self.contribution = contribution

    @return_ascii
    def __repr__(self):
        state = self.state.name if self.last_revision else None
        return '<Paper(contribution_id={}, state={})>'.format(self.contribution.id, state)

    @locator_property
    def locator(self):
        return self.contribution.locator

    # Contribution-related
    event = AttributeProxyProperty('event')
    title = AttributeProxyProperty('title')
    verbose_title = AttributeProxyProperty('verbose_title')

    # Paper-related
    revisions = AttributeProxyProperty('_paper_revisions')
    last_revision = AttributeProxyProperty('_paper_last_revision')
    accepted_revision = AttributeProxyProperty('_accepted_paper_revision')
    revision_count = AttributeProxyProperty('_paper_revision_count')
    files = AttributeProxyProperty('_paper_files')

    @property
    def state(self):
        return self.last_revision.state

    @state.setter
    def state(self, state):
        self.last_revision.state = state

    @property
    def judgment_comment(self):
        return self.last_revision._judgment_comment

    @property
    def is_in_final_state(self):
        return self.state in {PaperRevisionState.accepted, PaperRevisionState.rejected}

    def can_comment(self, user, check_state=False):
        if not user:
            return False
        if check_state and self.is_in_final_state:
            return False
        return self.can_submit(user) or self.can_judge(user) or self.can_review(user)

    def can_submit(self, user):
        return self.contribution.can_submit_proceedings(user)

    def can_manage(self, user):
        if not user:
            return False
        return self.event.can_manage(user)

    def can_judge(self, user, check_state=False):
        if not user:
            return False
        elif check_state and self.is_in_final_state:
            return False
        elif self.can_manage(user):
            return True
        return user in self.contribution.paper_judges

    def can_review(self, user, check_state=False):
        if not user:
            return False
        elif check_state and self.is_in_final_state:
            return False
        elif self.can_manage(user):
            return True
        return self.contribution.is_paper_reviewer(user)

    def get_revisions(self):
        return self.revisions

    def get_last_revision(self):
        return self.last_revision

    def reset_state(self):
        self.last_revision.state = PaperRevisionState.submitted
        self.last_revision.judgment_comment = ''
        self.last_revision.judge = None
        self.last_revision.judgment_dt = None
