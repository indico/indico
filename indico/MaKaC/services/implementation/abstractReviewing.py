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

from MaKaC.services.implementation.base import ParameterManager, TextModificationBase
from MaKaC.services.implementation.conference import ConferenceModifBase
from MaKaC.common.fossilize import fossilize
import MaKaC.user as user


##########################################
###  Abstract reviewing questions classes
##########################################
class AbstractReviewingBase(ConferenceModifBase):

    ''' Base Clase for Abstract Reviewing'''

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._confAbstractReview = self._conf.getConfAbstractReview()


class AbstractReviewingChangeNumAnswers(AbstractReviewingBase):

    ''' Change the number of answers per question '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._value = pm.extract("value", pType=int, allowEmpty=False)

    def _getAnswer(self):
        self._confAbstractReview.setNumberOfAnswers(self._value)
        # update the labels and titles
        self._confAbstractReview.recalculateRBLabelsAndTitles()
        return self._value


class AbstractReviewingChangeScale(AbstractReviewingBase):

    ''' Change the limits for the ratings '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        pm = ParameterManager(self._params)
        # we need to do like this because the value sent is an str (inherit of InlineEditWidget)
        self._value = pm.extract("value", pType=dict, allowEmpty=False)
        self._min = int(self._value["min"])
        self._max = int(self._value["max"])

    def _getAnswer(self):
        self._confAbstractReview.setScale(self._min, self._max)
        # recalculate the current values for the judgements
        self._conf.getAbstractMgr().recalculateAbstractsRating(self._min, self._max)
        # update the labels and titles again
        self._confAbstractReview.recalculateRBLabelsAndTitles()
        return self._value


class AbstractReviewingUpdateExampleQuestion(AbstractReviewingBase):

    ''' Get the required data for the example question '''

    def _getAnswer(self):
        # get the necessary values
        numAnswers = range(self._confAbstractReview.getNumberOfAnswers())
        labels = self._confAbstractReview.getRBLabels()
        rbValues = self._confAbstractReview.getRBTitles()
        return {"numberAnswers": numAnswers, "labels": labels, "rbValues": rbValues}


class AbstractReviewingGetQuestions(AbstractReviewingBase):

    ''' Get the current list of questions '''

    def _getAnswer(self):
        reviewingQuestions = self._confAbstractReview.getReviewingQuestions()
        return fossilize(reviewingQuestions)


class AbstractReviewingAddQuestion(AbstractReviewingBase):

    ''' Add a new question '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._value = pm.extract("value", pType=str, allowEmpty=False) # value is the question text

    def _getAnswer(self):
        self._confAbstractReview.addReviewingQuestion(self._value)
        reviewingQuestions = self._confAbstractReview.getReviewingQuestions()
        return fossilize(reviewingQuestions)


class AbstractReviewingRemoveQuestion(AbstractReviewingBase):

    ''' Remove a question '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._value = pm.extract("value", pType=str, allowEmpty=False) # value is the question id
        self._keepJud = pm.extract("keepJud", pType=bool, allowEmpty=False) # keep the previous judgements of the question

    def _getAnswer(self):
        # remove the question
        self._confAbstractReview.removeReviewingQuestion(self._value, self._keepJud)
        if not self._keepJud:
            # Purge all the judgements already exist with answers of this question
            self._conf.getAbstractMgr().removeAnswersOfQuestion(self._value)
            self._conf.getAbstractMgr().recalculateAbstractsRating(self._confAbstractReview.getScaleLower(), self._confAbstractReview.getScaleHigher())
        reviewingQuestions = self._confAbstractReview.getReviewingQuestions()
        # Build the answer
        return fossilize(reviewingQuestions)


class AbstractReviewingEditQuestion(AbstractReviewingBase):

    ''' Edit a question '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._id = pm.extract("id", pType=str, allowEmpty=False) # value is the question id
        self._text = pm.extract("text", pType=str, allowEmpty=True)

    def _getAnswer(self):
        self._confAbstractReview.editReviewingQuestion(self._id, self._text)
        reviewingQuestions = self._confAbstractReview.getReviewingQuestions()
        return fossilize(reviewingQuestions)


##########################################
###  Abstract reviewing team classes
##########################################

class AbstractReviewingAddReviewer(AbstractReviewingBase):

    ''' Add a reviewer for the indicated track '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._trackId = pm.extract("track", pType=str, allowEmpty=False)
        self._reviewerList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        for reviewer in self._reviewerList:
            ah = user.AvatarHolder()
            av = ah.getById(reviewer["id"])
            self._conf.getTrackById(self._trackId).addCoordinator(av)
        return fossilize(self._conf.getTrackById(self._trackId).getCoordinatorList())


class AbstractReviewingRemoveReviewer(AbstractReviewingBase):

    ''' Add a reviewer for the indicated track '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._trackId = pm.extract("track", pType=str, allowEmpty=False)
        self._reviewerId = pm.extract("userId", pType=str, allowEmpty=True, defaultValue=None)
        if (self._reviewerId == None):
            self._reviewerId = pm.extract("user", pType=str, allowEmpty=False)

    def _getAnswer(self):
        ah = user.AvatarHolder()
        av = ah.getById(self._reviewerId)
        self._conf.getTrackById(self._trackId).removeCoordinator(av)
        return fossilize(self._conf.getTrackById(self._trackId).getCoordinatorList())


class AbstractReviewingChangeReviewerRights(TextModificationBase, AbstractReviewingBase):

    def _handleSet(self):
        self._confAbstractReview.setCanReviewerAccept(self._value)

    def _handleGet(self):
        return self._confAbstractReview.canReviewerAccept()


methodMap = {
    "questions.changeNumberofAnswers": AbstractReviewingChangeNumAnswers,
    "questions.changeScale": AbstractReviewingChangeScale,
    "questions.updateExampleQuestion": AbstractReviewingUpdateExampleQuestion,
    "questions.getQuestions": AbstractReviewingGetQuestions,
    "questions.addQuestion": AbstractReviewingAddQuestion,
    "questions.removeQuestion": AbstractReviewingRemoveQuestion,
    "questions.editQuestion": AbstractReviewingEditQuestion,

    "settings.changeReviewerRights": AbstractReviewingChangeReviewerRights,

    "team.addReviewer": AbstractReviewingAddReviewer,
    "team.removeReviewer": AbstractReviewingRemoveReviewer
    }

