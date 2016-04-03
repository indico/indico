# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from operator import attrgetter

from BTrees.IOBTree import IOBTree
import transaction

from indico.modules.events.paper_reviewing.models.roles import PaperReviewingRole
from indico.util.console import verbose_iterator
from indico_zodbimport import Importer

from MaKaC.contributionReviewing import ReviewManager


def _invert_mapping(mapping):
    result = defaultdict(list)
    for user, contribs in mapping.iteritems():
        for contrib in contribs:
            result[contrib].append(user)
    return result


class EventPaperReviewingImporter(Importer):
    def migrate(self):
        self.migrate_reviewing()

    def _zodb_committing_iterator(self, iterable):
        for i, data in enumerate(iterable, 1):
            yield data
            if i % 100 == 0:
                transaction.commit()
        transaction.commit()

    def _migrate_contribution_roles(old_contribution, mapping, role):
        contribution = old_contribution.as_new
        for avatars in mapping[old_contribution]:
            for avatar in avatars:
                contribution.paper_reviewing_roles.append(PaperReviewingRole(user=avatar.as_user, role=role))

    def migrate_reviewing(self):
        self.print_step('building new ZODB index for reviewing objects')

        for old_event in self._zodb_committing_iterator(self._iter_events()):
            conference_settings = old_event._confPaperReview
            contrib_index = conference_settings._contribution_index = IOBTree()
            contrib_reviewers = _invert_mapping(conference_settings._reviewerContribution)
            contrib_referees = _invert_mapping(conference_settings._refereeContribution)
            contrib_editors = _invert_mapping(conference_settings._editorContribution)

            for old_contribution in old_event.contributions.itervalues():
                review_manager = getattr(old_contribution, '_reviewManager')
                if not review_manager:
                    self.print_warning('Contribution {} had no ReviewManager. Fixed.'.format(old_contribution._id),
                                       event_id=event.id)
                    cid = int(old_contribution._id)
                    contrib_index[cid] = old_contribution._reviewManager = ReviewManager(old_contribution)

                _migrate_contribution_roles(old_contribution, contrib_reviewers, PaperReviewingRoleType.reviewer)
                _migrate_contribution_roles(old_contribution, contrib_referees, PaperReviewingRoleType.referee)
                _migrate_contribution_roles(old_contribution, contrib_editors, PaperReviewingRoleType.editor)

    def _iter_events(self):
        old_events = self.zodb_root['conferences']
        return verbose_iterator(old_events.itervalues(), len(old_events), attrgetter('id'),
                                attrgetter('title')):
