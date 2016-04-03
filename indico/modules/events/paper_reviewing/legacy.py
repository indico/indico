from indico.core import signals
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.paper_reviewing.models.roles import PaperReviewingRole, PaperReviewingRoleType


@signals.event.contributions.contribution_created.connect
def _add_legacy_index_entry(contribution, **kwargs):
    from MaKaC.contributionReviewing import ReviewManager
    cpr = contribution.event_new.as_legacy.getConferencePaperReviewing()
    cpr._contribution_index[contribution.id] = ReviewManager(contribution.id)


def _add_contribution_role(user, contribution, role):
    contribution.paper_reviewing_roles.append(PaperReviewingRole(user=user,
                                                                 role=PaperReviewingRoleType.get(role)))


def _get_contribution_role(user, contribution, role):
    return contribution.paper_reviewing_roles.filter_by(user=user, role=PaperReviewingRoleType.get(role))


def _remove_contribution_role(user, contribution, role):
    roles = contribution.paper_reviewing_roles
    role = roles.filter_by(user=user, role=PaperReviewingRoleType.get(role))
    roles.remove(role)


def _get_contributions_for_role(user, event, role):
    return PaperReviewingRole.find_all(user=user, role=PaperReviewingRoleType.get(role),
                                       event_id=int(event.id), _join=Contribution)


class ConferencePaperReviewLegacyMixin(object):

    def addRefereeContribution(self, user, contribution):
        _add_contribution_role(user, contribution, 'referee')
        self.notifyModification()

    def removeRefereeContribution(self, user, contribution):
        _remove_contribution_role(user, contribution, 'referee')
        self.notifyModification()

    def isRefereeContribution(self, user, contribution):
        return bool(_get_contribution_role(user, contribution, 'referee'))

    def getJudgedContributions(self, referee):
        return _get_contributions_for_role(user=referee, event=int(self._conference.id), role='referee')

    def addEditorContribution(self, user, contribution):
        _add_contribution_role(user, contribution, 'editor')
        self.notifyModification()

    def removeEditorContribution(self, user, contribution):
        _remove_contribution_role(user, contribution, 'editor')
        self.notifyModification()

    def isEditorContribution(self, user, contribution):
        return bool(_get_contribution_role(user, contribution, 'editor'))

    def getEditedContributions(self, user):
        return _get_contributions_for_role(user=user, event=int(self._conference.id), role='editor')

    def addReviewerContribution(self, user, contribution):
        _add_contribution_role(user, contribution, 'reviewer')
        self.notifyModification()

    def removeReviewerContribution(self, user, contribution):
        _remove_contribution_role(user, contribution, 'reviewer')
        self.notifyModification()

    def isReviewerContribution(self, user, contribution):
        return bool(_get_contribution_role(user, contribution, 'reviewer'))

    def getReviewedContributions(self, editor):
        return _get_contributions_for_role(user=editor, event=int(self._conference.id), role='reviewer')


class ReviewManagerLegacyMixin(object):

    @property
    def contribution(self):
        return Contribution.get(self._contribution_id)

    def getConference(self):
        return self.contribution.event_new.as_legacy
