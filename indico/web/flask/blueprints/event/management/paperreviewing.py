# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import reviewingControlModif, reviewingModif, reviewingUserCompetencesModif, \
    reviewingAssignContributions, reviewingListContribToJudge, contribReviewingModif
from indico.web.flask.blueprints.event.management import event_mgmt


# Entrance (redirects to most appropriate page)
event_mgmt.add_url_rule('/paper-reviewing/', 'confModifReviewing-access', reviewingModif.RHConfModifReviewingAccess)

# Setup
event_mgmt.add_url_rule('/paper-reviewing/setup/', 'confModifReviewing-paperSetup',
                        reviewingModif.RHConfModifReviewingPaperSetup)
event_mgmt.add_url_rule('/paper-reviewing/setup/templates/<reviewingTemplateId>', 'confModifReviewing-downloadTemplate',
                        reviewingModif.RHDownloadTemplate)
event_mgmt.add_url_rule('/paper-reviewing/setup/templates/upload', 'confModifReviewing-setTemplate',
                        reviewingModif.RHSetTemplate, methods=('POST',))

# Team
event_mgmt.add_url_rule('/paper-reviewing/team', 'confModifReviewingControl',
                        reviewingControlModif.RHConfModifReviewingControl)

# Competences
event_mgmt.add_url_rule('/paper-reviewing/competences/', 'confModifUserCompetences',
                        reviewingUserCompetencesModif.RHConfModifUserCompetences)

# Assign papers
event_mgmt.add_url_rule('/paper-reviewing/assign/', 'assignContributions',
                        reviewingAssignContributions.RHReviewingAssignContributionsList)

# Accepted papers
event_mgmt.add_url_rule('/paper-reviewing/accepted-papers.zip', 'assignContributions-downloadAcceptedPapers',
                        reviewingAssignContributions.RHDownloadAcceptedPapers)

# Assess papers
event_mgmt.add_url_rule('/paper-reviewing/assess/referee', 'confListContribToJudge',
                        reviewingListContribToJudge.RHContribListToJudge)
event_mgmt.add_url_rule('/paper-reviewing/assess/reviewer/layout', 'confListContribToJudge-asEditor',
                        reviewingListContribToJudge.RHContribListToJudgeAsEditor)
event_mgmt.add_url_rule('/paper-reviewing/assess/reviewer/content', 'confListContribToJudge-asReviewer',
                        reviewingListContribToJudge.RHContribListToJudgeAsReviewer)

with event_mgmt.add_prefixed_rules('/session/<sessionId>'):
    # Contribution reviewing: team
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/', 'contributionReviewing',
                            contribReviewingModif.RHContributionReviewing, methods=('GET', 'POST'))
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/assign/referee',
                            'contributionReviewing-assignReferee', contribReviewingModif.RHAssignReferee,
                            methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/unassign/referee',
                            'contributionReviewing-removeAssignReferee', contribReviewingModif.RHRemoveAssignReferee,
                            methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/assign/reviewer/layout',
                            'contributionReviewing-assignEditing', contribReviewingModif.RHAssignEditing,
                            methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/unassign/reviewer/layout',
                            'contributionReviewing-removeAssignEditing', contribReviewingModif.RHRemoveAssignEditing,
                            methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/assign/reviewer/content',
                            'contributionReviewing-assignReviewing', contribReviewingModif.RHAssignReviewing,
                            methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/unassign/reviewer/content',
                            'contributionReviewing-removeAssignReviewing',
                            contribReviewingModif.RHRemoveAssignReviewing, methods=('POST',))

    # Contribution reviewing: assessments
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/assess/referee',
                            'contributionReviewing-contributionReviewingJudgements',
                            contribReviewingModif.RHContributionReviewingJudgements)
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/assess/layout', 'contributionEditingJudgement',
                            contribReviewingModif.RHContributionEditingJudgement)
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/assess/content', 'contributionGiveAdvice',
                            contribReviewingModif.RHContributionGiveAdvice)
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/material',
                            'contributionReviewing-contributionReviewingMaterials',
                            contribReviewingModif.RHContribModifReviewingMaterials)
    event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/history', 'contributionReviewing-reviewingHistory',
                            contribReviewingModif.RHReviewingHistory)
