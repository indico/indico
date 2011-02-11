# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

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
        self._value = int(self._params.get("value"))

    def _getAnswer(self):
        self._confAbstractReview.setNumberOfAnswers(self._value)
        # update the labels
        self._confAbstractReview.setRadioButtonsLabels()
        self._confAbstractReview.setRadioButtonsTitles()
        return self._value


class AbstractReviewingChangeScale(AbstractReviewingBase):

    ''' Change the limits for the ratings '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        self._value = self._params.get("value")
        self._min = int(self._value["min"])
        self._max = int(self._value["max"])

    def _getAnswer(self):
        self._confAbstractReview.setScale(self._min, self._max)
        # recalculate the current values for the judgements
        self._conf.getAbstractMgr().recalculateAbstractsRating(self._min, self._max)
        # update the labels and titles again
        self._confAbstractReview.setRadioButtonsLabels()
        self._confAbstractReview.setRadioButtonsTitles()
        return self._value


class AbstractReviewingUpdateExampleQuestion(AbstractReviewingBase):

    ''' Get the required data for the example question '''

    def _getAnswer(self):
        # get the necessary values
        numAnswers = range(self._confAbstractReview.getNumberOfAnswers())
        labels = self._confAbstractReview.getRadioButtonsLabels()
        rbValues = self._confAbstractReview.getRadioButtonsTitles()
        return {"numberAnswers": numAnswers, "labels": labels, "rbValues": rbValues}


class AbstractReviewingGetQuestions(AbstractReviewingBase):

    ''' Get the current list of questions '''

    def _getAnswer(self):
        reviewingQuestions = self._confAbstractReview.getReviewingQuestions()
        fossils = []
        for question in reviewingQuestions:
            fossils.append(fossilize(question))
        return fossils


class AbstractReviewingAddQuestion(AbstractReviewingBase):

    ''' Add a new question '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        self._value = self._params.get("value") # value is the question text

    def _getAnswer(self):
        self._confAbstractReview.addReviewingQuestion(self._value)
        reviewingQuestions = self._confAbstractReview.getReviewingQuestions()
        fossils = []
        for question in reviewingQuestions:
            fossils.append(fossilize(question))
        return fossils


class AbstractReviewingRemoveQuestion(AbstractReviewingBase):

    ''' Remove a question '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        self._value = self._params.get("value") # value is the question id
        self._keepJud = self._params.get("keepJud") # keep the previous judgements of the question

    def _getAnswer(self):
        # remove the question
        self._confAbstractReview.removeReviewingQuestion(self._value, self._keepJud)
        if not self._keepJud:
            # Purge all the judgements already exist with answers of this question
            self._conf.getAbstractMgr().removeAnswersOfQuestion(self._value)
            self._conf.getAbstractMgr().recalculateAbstractsRating(self._confAbstractReview.getScaleLower(), self._confAbstractReview.getScaleHigher())
        reviewingQuestions = self._confAbstractReview.getReviewingQuestions()
        # Build the answer
        fossils = []
        for question in reviewingQuestions:
            fossils.append(fossilize(question))
        return fossils


class AbstractReviewingEditQuestion(AbstractReviewingBase):

    ''' Edit a question '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        self._id = self._params.get("id") # value is the question id
        self._text = self._params.get("text")

    def _getAnswer(self):
        self._confAbstractReview.editReviewingQuestion(self._id, self._text)
        reviewingQuestions = self._confAbstractReview.getReviewingQuestions()
        fossils = []
        for question in reviewingQuestions:
            fossils.append(fossilize(question))
        return fossils


##########################################
###  Abstract reviewing team classes
##########################################

class AbstractReviewingAddReviewer(AbstractReviewingBase):

    ''' Add a reviewer for the indicated track '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        self._trackId = self._params.get("track")
        self._reviewerId = self._params.get("user")

    def _getAnswer(self):
        ah = user.AvatarHolder()
        av = ah.getById(self._reviewerId)
        self._conf.getTrackById(self._trackId).addCoordinator(av)
        return True


class AbstractReviewingRemoveReviewer(AbstractReviewingBase):

    ''' Add a reviewer for the indicated track '''

    def _checkParams(self):
        AbstractReviewingBase._checkParams(self)
        self._trackId = self._params.get("track")
        self._reviewerId = self._params.get("user")

    def _getAnswer(self):
        ah = user.AvatarHolder()
        av = ah.getById(self._reviewerId)
        self._conf.getTrackById(self._trackId).removeCoordinator(av)
        return True

methodMap = {
    "questions.changeNumberofAnswers": AbstractReviewingChangeNumAnswers,
    "questions.changeScale": AbstractReviewingChangeScale,
    "questions.updateExampleQuestion": AbstractReviewingUpdateExampleQuestion,
    "questions.getQuestions": AbstractReviewingGetQuestions,
    "questions.addQuestion": AbstractReviewingAddQuestion,
    "questions.removeQuestion": AbstractReviewingRemoveQuestion,
    "questions.editQuestion": AbstractReviewingEditQuestion,

    "team.addReviewer": AbstractReviewingAddReviewer,
    "team.removeReviewer": AbstractReviewingRemoveReviewer
    }

