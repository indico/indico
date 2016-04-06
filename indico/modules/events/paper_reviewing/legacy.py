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

from collections import defaultdict

from flask import g

from indico.core import signals
from indico.core.db import db
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.paper_reviewing.models.papers import PaperFile
from indico.modules.events.paper_reviewing.models.roles import PaperReviewingRole, PaperReviewingRoleType
from indico.util.caching import memoize_request


def _load_roles(contribution):
    if not g.get('contribution_roles'):
        g.contribution_roles = {}
    if contribution not in g.contribution_roles:
        g.contribution_roles[contribution] = defaultdict(list)
        for r in contribution.paper_reviewing_roles:
            g.contribution_roles[contribution][r.role.name].append(r)

@signals.event.contributions.contribution_created.connect
def _add_legacy_index_entry(contribution, **kwargs):
    from MaKaC.contributionReviewing import ReviewManager
    cpr = contribution.event_new.as_legacy.getConfPaperReview()
    cpr._contribution_index[contribution.id] = ReviewManager(contribution.id)


def add_contribution_role(user, contribution, role):
    contribution.paper_reviewing_roles.append(PaperReviewingRole(user=user,
                                                                 role=PaperReviewingRoleType.get(role)))


def _get_contribution_role(user, contribution, role):
    _load_roles(contribution)
    return next((r for r in g.contribution_roles[contribution][role] if r.user == user), None)


def _remove_contribution_role(user, contribution, role):
    role = _get_contribution_role(user, contribution, role)
    db.session.delete(role)


def get_contributions_for_role(user, event, role):
    return [r.contribution for r in PaperReviewingRole.find_all(
        Contribution.event_id == int(event.id), PaperReviewingRole.user == user,
        PaperReviewingRole.role == PaperReviewingRoleType.get(role), _join=Contribution)]


def get_users_for_role(contribution, role):
    _load_roles(contribution)
    return g.contribution_roles[contribution][role]


def get_reviewing_status(contrib, conf):
    from MaKaC.paperReviewing import ConferencePaperReview
    review_manager = conf.getReviewManager(contrib)
    versioning = review_manager.getVersioning()
    last_review = review_manager.getLastReview()

    if conf.getConfPaperReview().getChoice() == ConferencePaperReview.LAYOUT_REVIEWING:
        if last_review.getEditorJudgement().isSubmitted():  # editor has accepted or rejected
            return last_review.getEditorJudgement().getJudgement()
        elif last_review.isAuthorSubmitted():
            return 'Submitted'
        elif len(versioning) > 1:  # there was a judgement 'To be corrected' or custom status
            return versioning[-2].getEditorJudgement().getJudgement()
    else:
        if last_review.getRefereeJudgement().isSubmitted():  # referee has accepted or rejected
            return last_review.getRefereeJudgement().getJudgement()
        elif last_review.isAuthorSubmitted():
            return 'Submitted'
        elif len(versioning) > 1:  # there was a judgement 'To be corrected' or custom status
            return versioning[-2].getRefereeJudgement().getJudgement()
    if last_review.isAuthorSubmitted():
        return 'Submitted'
    return None


class ConferencePaperReviewLegacyMixin(object):

    def addRefereeContribution(self, user, contribution):
        add_contribution_role(user.user, contribution, 'referee')
        self.notifyModification()

    def removeRefereeContribution(self, user, contribution):
        _remove_contribution_role(user.user, contribution, 'referee')
        self.notifyModification()

    def isRefereeContribution(self, user, contribution):
        return bool(_get_contribution_role(user.user, contribution, 'referee'))

    def getJudgedContributions(self, referee):
        return get_contributions_for_role(referee.user, self._conference.as_event, 'referee')

    def addEditorContribution(self, user, contribution):
        add_contribution_role(user.user, contribution, 'editor')
        self.notifyModification()

    def removeEditorContribution(self, user, contribution):
        _remove_contribution_role(user.user, contribution, 'editor')
        self.notifyModification()

    def isEditorContribution(self, user, contribution):
        return bool(_get_contribution_role(user.user, contribution, 'editor'))

    def getEditedContributions(self, user):
        return get_contributions_for_role(user.user, self._conference.as_event, 'editor')

    def addReviewerContribution(self, user, contribution):
        add_contribution_role(user.user, contribution, 'reviewer')
        self.notifyModification()

    def removeReviewerContribution(self, user, contribution):
        _remove_contribution_role(user.user, contribution, 'reviewer')
        self.notifyModification()

    def isReviewerContribution(self, user, contribution):
        return bool(_get_contribution_role(user.user, contribution, 'reviewer'))

    def getReviewedContributions(self, editor):
        return get_contributions_for_role(editor.user, self._conference.as_event, 'reviewer')


class ReviewManagerLegacyMixin(object):

    @property
    @memoize_request
    def contribution(self):
        return Contribution.get(self._contrib_id)

    @property
    @memoize_request
    def event_new(self):
        return self.contribution.event_new

    @property
    @memoize_request
    def paper_review(self):
        return self.getConference().getConfPaperReview()

    @memoize_request
    def getConference(self):
        return self.event_new.as_legacy

    def isEditor(self, user):
        if user == 'any' or not user:
            return False
        return self.paper_review.isEditorContribution(user, self.contribution)

    def isReviewer(self, user):
        if user == 'any' or not user:
            return False
        return self.paper_review.isReviewerContribution(user, self.contribution)

    def isReferee(self, user):
        if user == 'any' or not user:
            return False
        return self.paper_review.isRefereeContribution(user, self.contribution)

    def getEditor(self):
        roles = get_users_for_role(self.contribution, 'editor')
        return roles[0].user.as_legacy if roles else None

    def getReviewersList(self):
        return [role.user.as_legacy for role in get_users_for_role(self.contribution, 'reviewer')]

    def getReferee(self):
        roles = get_users_for_role(self.contribution, 'referee')
        return roles[0].user.as_legacy if roles else None

    def hasEditor(self):
        return bool(self.getEditor())

    def hasReviewers(self):
        return bool(self.getReviewersList())

    def hasReferee(self):
        return bool(self.getReferee())


class ReviewLegacyMixin(object):
    def copyMaterials(self):
        for paper_file in PaperFile.find(contribution=self._reviewManager.contribution,
                                         revision_id=None):
            new_paper_file = PaperFile(revision_id=self._version, filename=paper_file.filename,
                                       content_type=paper_file.content_type, contribution=self._reviewManager.contribution)
            new_paper_file.save(paper_file.open())

    @property
    def materials(self):
        return PaperFile.find_all(contribution=self._reviewManager.contribution, revision_id=self._version)
