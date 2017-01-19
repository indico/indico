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

from indico.core.settings.proxy import AttributeProxyProperty
from indico.modules.events.models.reviews import ProposalMixin
from indico.util.locators import locator_property
from indico.util.string import return_ascii


class Paper(ProposalMixin):
    """Proxy class to facilitate access to all paper-related properties"""

    proxied_attr = 'contribution'

    # Proposal mixin properties
    proposal_type = 'paper'
    call_for_proposals_attr = 'cfp'
    create_comment_endpoint = 'papers.submit_comment'
    delete_comment_endpoint = 'papers.delete_comment'
    edit_comment_endpoint = 'papers.edit_comment'
    create_review_endpoint = 'papers.submit_review'
    edit_review_endpoint = 'papers.edit_review'

    def __init__(self, contribution):
        self.contribution = contribution

    @return_ascii
    def __repr__(self):
        return '<Paper(contribution_id={}, state={})>'.format(self.contribution.id, self.state.name)

    @locator_property
    def locator(self):
        return self.contribution.locator

    # Contribution-related
    event_new = AttributeProxyProperty('event_new')
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
