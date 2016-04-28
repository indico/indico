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


class RCContributionPaperReviewingStaff(object):
    @staticmethod
    def hasRights(request, contribution=None, includingContentReviewer=True):
        """Returns true if the user is a PRM, or a Referee / Editor / Reviewer of the target contribution"""
        user = request.getAW().getUser()
        confPaperReview = request._target.getConference().getConfPaperReview()
        paperReviewChoice = confPaperReview.getChoice()
        if contribution:
            reviewManager = confPaperReview.getReviewManager(contribution)
        else:
            reviewManager = confPaperReview.getReviewManager(request.contrib)
        return (confPaperReview.isPaperReviewManager(user) or
                (reviewManager.hasReferee() and reviewManager.isReferee(user)) or
                ((paperReviewChoice == 3 or paperReviewChoice == 4) and
                 reviewManager.hasEditor() and reviewManager.isEditor(user)) or
                (includingContentReviewer and ((paperReviewChoice == 2 or paperReviewChoice == 4) and
                                               reviewManager.isReviewer(user))))


class RCContributionReferee(object):
    @staticmethod
    def hasRights(request):
        """Returns true if the user is a referee of the target contribution"""
        user = request.getAW().getUser()
        reviewManager = request.contrib.event_new.as_legacy.getReviewManager(request.contrib)
        return reviewManager.hasReferee() and reviewManager.isReferee(user)


class RCContributionEditor(object):
    @staticmethod
    def hasRights(request):
        """Returns true if the user is an editor of the target contribution"""
        user = request.getAW().getUser()
        reviewManager = request._conf.getReviewManager(request.contrib)
        return reviewManager.hasEditor() and reviewManager.isEditor(user)


class RCContributionReviewer(object):
    @staticmethod
    def hasRights(request):
        """Returns true if the user is a reviewer of the target contribution"""
        user = request.getAW().getUser()
        reviewManager = request._conf.getReviewManager(request.contrib)
        return reviewManager.isReviewer(user)
