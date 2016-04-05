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


from indico.core import signals
from indico.core.db import db
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.paper_reviewing.models.roles import PaperReviewingRole, PaperReviewingRoleType


@signals.event.contributions.contribution_created.connect
def _add_legacy_index_entry(contribution, **kwargs):
    from MaKaC.contributionReviewing import ReviewManager
    cpr = contribution.event_new.as_legacy.getConfPaperReview()
    cpr._contribution_index[contribution.id] = ReviewManager(contribution.id)


def _add_contribution_role(user, contribution, role):
    contribution.paper_reviewing_roles.append(PaperReviewingRole(user=user,
                                                                 role=PaperReviewingRoleType.get(role)))


def _get_contribution_role(user, contribution, role):
    return next((r for r in contribution.paper_reviewing_roles if r.user == user and
                 r.role == PaperReviewingRoleType.get(role)), None)


def _remove_contribution_role(user, contribution, role):
    role = _get_contribution_role(user, contribution, role)
    db.session.delete(role)


def _get_contributions_for_role(user, event, role):
    return [r.contribution for r in PaperReviewingRole.find_all(
        Contribution.event_id == int(event.id), user=user, role=PaperReviewingRoleType.get(role), _join=Contribution)]


class ConferencePaperReviewLegacyMixin(object):

    def addRefereeContribution(self, user, contribution):
        _add_contribution_role(user.user, contribution, 'referee')
        self.notifyModification()

    def removeRefereeContribution(self, user, contribution):
        _remove_contribution_role(user.user, contribution, 'referee')
        self.notifyModification()

    def isRefereeContribution(self, user, contribution):
        return bool(_get_contribution_role(user.user, contribution, 'referee'))

    def getJudgedContributions(self, referee):
        return _get_contributions_for_role(referee.user, self._conference.as_event, 'referee')

    def addEditorContribution(self, user, contribution):
        _add_contribution_role(user.user, contribution, 'editor')
        self.notifyModification()

    def removeEditorContribution(self, user, contribution):
        _remove_contribution_role(user.user, contribution, 'editor')
        self.notifyModification()

    def isEditorContribution(self, user, contribution):
        return bool(_get_contribution_role(user.user, contribution, 'editor'))

    def getEditedContributions(self, user):
        return _get_contributions_for_role(user.user, self._conference.as_event, 'editor')

    def addReviewerContribution(self, user, contribution):
        _add_contribution_role(user.user, contribution, 'reviewer')
        self.notifyModification()

    def removeReviewerContribution(self, user, contribution):
        _remove_contribution_role(user.user, contribution, 'reviewer')
        self.notifyModification()

    def isReviewerContribution(self, user, contribution):
        return bool(_get_contribution_role(user.user, contribution, 'reviewer'))

    def getReviewedContributions(self, editor):
        return _get_contributions_for_role(editor.user, self._conference.as_event, 'reviewer')


class ReviewManagerLegacyMixin(object):

    @property
    def contribution(self):
        return Contribution.get(self._contrib_id)

    def getConference(self):
        return self.contribution.event_new.as_legacy
