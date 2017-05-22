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

from collections import defaultdict

from indico.legacy.webinterface.rh.base import RHModificationBaseProtected
from indico.legacy.webinterface.rh.conferenceBase import RHConferenceBase
from indico.modules.events.contributions.models.persons import (AuthorType, ContributionPersonLink,
                                                                SubContributionPersonLink)
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.web.util import jsonify_template


class RHManageEventBase(RHConferenceBase, RHModificationBaseProtected):
    """Base class for event management RHs"""

    DENY_FRAMES = True

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)


class RHContributionPersonListMixin:
    """List of persons somehow related to contributions (co-authors, speakers...)"""

    @property
    def _membership_filter(self):
        raise NotImplementedError

    def _process(self):
        contribution_persons = (ContributionPersonLink
                                .find(ContributionPersonLink.contribution.has(self._membership_filter))
                                .all())
        contribution_persons.extend(SubContributionPersonLink
                                    .find(SubContributionPersonLink.subcontribution
                                          .has(SubContribution.contribution.has(self._membership_filter)))
                                    .all())

        contribution_persons_dict = defaultdict(lambda: {'speaker': False, 'primary_author': False,
                                                         'secondary_author': False})
        for contrib_person in contribution_persons:
            person_roles = contribution_persons_dict[contrib_person.person]
            person_roles['speaker'] |= contrib_person.is_speaker
            person_roles['primary_author'] |= contrib_person.author_type == AuthorType.primary
            person_roles['secondary_author'] |= contrib_person.author_type == AuthorType.secondary
        return jsonify_template(self.template, event_persons=contribution_persons_dict, event=self.event_new)
