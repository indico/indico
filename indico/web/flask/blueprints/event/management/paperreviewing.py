# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.management import event_mgmt


# Entrance (redirects to most appropriate page)
event_mgmt.add_url_rule('/paper-reviewing/', 'confModifReviewing-access',
                        rh_as_view(reviewingModif.RHConfModifReviewingAccess))

# Setup
event_mgmt.add_url_rule('/paper-reviewing/setup/', 'confModifReviewing-paperSetup',
                        rh_as_view(reviewingModif.RHConfModifReviewingPaperSetup))
event_mgmt.add_url_rule('/paper-reviewing/setup/templates/<reviewingTemplateId>', 'confModifReviewing-downloadTemplate',
                        rh_as_view(reviewingModif.RHDownloadTemplate))
event_mgmt.add_url_rule('/paper-reviewing/setup/templates/upload', 'confModifReviewing-setTemplate',
                        rh_as_view(reviewingModif.RHSetTemplate), methods=('POST',))

# Team
event_mgmt.add_url_rule('/paper-reviewing/team', 'confModifReviewingControl',
                        rh_as_view(reviewingControlModif.RHConfModifReviewingControl))

# Competences
event_mgmt.add_url_rule('/paper-reviewing/competences/', 'confModifUserCompetences',
                        rh_as_view(reviewingUserCompetencesModif.RHConfModifUserCompetences))

# Assign papers
event_mgmt.add_url_rule('/paper-reviewing/assign/', 'assignContributions',
                        rh_as_view(reviewingAssignContributions.RHReviewingAssignContributionsList))
event_mgmt.add_url_rule('/paper-reviewing/assign/accepted-papers.zip', 'assignContributions-downloadAcceptedPapers',
                        rh_as_view(reviewingAssignContributions.RHDownloadAcceptedPapers))

# Assess papers
event_mgmt.add_url_rule('/paper-reviewing/assess/referee', 'confListContribToJudge',
                        rh_as_view(reviewingListContribToJudge.RHContribListToJudge))
event_mgmt.add_url_rule('/paper-reviewing/assess/reviewer/layout', 'confListContribToJudge-asEditor',
                        rh_as_view(reviewingListContribToJudge.RHContribListToJudgeAsEditor))
event_mgmt.add_url_rule('/paper-reviewing/assess/reviewer/content', 'confListContribToJudge-asReviewer',
                        rh_as_view(reviewingListContribToJudge.RHContribListToJudgeAsReviewer))


# Contribution reviewing: team
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/', 'contributionReviewing',
                        rh_as_view(contribReviewingModif.RHContributionReviewing), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/assign/referee',
                        'contributionReviewing-assignReferee', rh_as_view(contribReviewingModif.RHAssignReferee),
                        methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/unassign/referee',
                        'contributionReviewing-removeAssignReferee',
                        rh_as_view(contribReviewingModif.RHRemoveAssignReferee), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/assign/reviewer/layout',
                        'contributionReviewing-assignEditing',
                        rh_as_view(contribReviewingModif.RHAssignEditing), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/unassign/reviewer/layout',
                        'contributionReviewing-removeAssignEditing',
                        rh_as_view(contribReviewingModif.RHRemoveAssignEditing), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/assign/reviewer/content',
                        'contributionReviewing-assignReviewing',
                        rh_as_view(contribReviewingModif.RHAssignReviewing), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/team/unassign/reviewer/content',
                        'contributionReviewing-removeAssignReviewing',
                        rh_as_view(contribReviewingModif.RHRemoveAssignReviewing), methods=('POST',))

# Contribution reviewing: assessments
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/assess/referee',
                        'contributionReviewing-contributionReviewingJudgements',
                        rh_as_view(contribReviewingModif.RHContributionReviewingJudgements))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/assess/layout', 'contributionEditingJudgement',
                        rh_as_view(contribReviewingModif.RHContributionEditingJudgement))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/assess/content', 'contributionGiveAdvice',
                        rh_as_view(contribReviewingModif.RHContributionGiveAdvice))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/material',
                        'contributionReviewing-contributionReviewingMaterials',
                        rh_as_view(contribReviewingModif.RHContribModifReviewingMaterials))
event_mgmt.add_url_rule('/contribution/<contribId>/reviewing/history', 'contributionReviewing-reviewingHistory',
                        rh_as_view(contribReviewingModif.RHReviewingHistory))
