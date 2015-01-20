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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from MaKaC.common.fossilize import IFossil
from MaKaC.common.Conversion import Conversion
from MaKaC.fossils.user import IAvatarMinimalFossil

class IJudgementFossil(IFossil):
    """
    Fossil for the Judgement object
    """

    def isSubmitted(self):
        pass

    def getJudgement(self):
        pass

class IReviewFossil(IFossil):
    """
    Fossil for the review object
    """

    def getRefereeDueDate(self):
        pass
    getRefereeDueDate.convert = Conversion.datetime

    def getRefereeJudgement(self):
        pass
    getRefereeJudgement.result = IJudgementFossil

    def getReviewingStatus(self):
        pass

    def isAuthorSubmitted(self):
        pass

class IReviewManagerFossil(IFossil):
    """
    Fossil for review manager
    """

    def getReferee(self):
        pass
    getReferee.convert = lambda r: r and r.getStraightFullName()

    def getEditor(self):
        pass
    getEditor.convert = lambda e: e and e.getStraightFullName()

    def getReviewersList(self):
        pass
    getReviewersList.result = IAvatarMinimalFossil

    def getLastReview(self):
        pass
    getLastReview.result = IReviewFossil

    def getVersioningLen(self):
        pass


class IReviewingQuestionFossil(IFossil):
    """
    Fossil for the reviewing questions
    """
    def getId(self):
        pass

    def getText(self):
        pass

class IReviewingStatusFossil(IFossil):
    """
    Fossil for the reviewing status
    """
    def getId(self):
        pass

    def getName(self):
        pass
    getName.name = 'text'




