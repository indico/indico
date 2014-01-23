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

from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface                      import urlHandlers
from MaKaC.webinterface.pages                import evaluations
from MaKaC.evaluation                        import Evaluation,Question,Submission
from MaKaC.errors                            import FormValuesError
from MaKaC.common.info import HelperMaKaCInfo

from indico.core.config import Config


class RHBaseEvaluation( RHConferenceBaseDisplay ):
    """Base for evaluation."""

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._evaluation = self._conf.getEvaluation()

    def _processIfActive( self ):
        """ only override this method if the Evaluation must be activated for
            carrying on the handler execution.
        """
        return "evaluation"

    def _process( self ):
        """ If the Evaluation is not activated we show up a form informing about that.
            This must be done at RH level because there can be some RH not displaying pages.
        """
        if not self._evaluation.isVisible() or not self._conf.hasEnabledSection("evaluation"):
            return self._wpEvaluation("Inactive").display()
        else:
            return self._processIfActive()

    def _wpEvaluation(self, pageToShow):
        """redirection to the right class, dependending on conference type.
            Params:
                pageToShow -- [str] name of evaluation page to show (e.g. "WPEvaluationDisplay"->"Display")
        """
        wf = self.getWebFactory()
        if wf!=None : #Event == Meeting/Lecture
            return eval("wf.getEvaluation"+str(pageToShow)+"(self, self._conf)")
        else : #Event == Conference
            return eval("evaluations.WPEvaluation"+str(pageToShow)+"(self, self._conf)")


class RHEvaluationMainInformation( RHBaseEvaluation ):
    """General information display."""
    _uh = urlHandlers.UHConfEvaluationMainInformation

    def _processIfActive( self ):
        if self.getWebFactory()!=None : #Event == Meeting/Lecture
            self._redirect(urlHandlers.UHConferenceDisplay.getURL(self._conf))
        else : #Event == Conference
            return evaluations.WPEvaluationMainInformation(self, self._conf).display()


class RHEvaluationSignIn( RHBaseEvaluation ):
    """Invite user to login/signin."""
    _uh = urlHandlers.UHConfEvaluationSignIn
    _tohttps = True
    _isMobile = False

    def _getLoginURL(self):
        return RHConferenceBaseDisplay._getLoginURL(self, urlHandlers.UHConfEvaluationDisplay.getURL(self._conf))

    def _processIfActive(self):
        if self._getUser():
            self._redirect(urlHandlers.UHConfEvaluationDisplay.getURL(self._conf))
        else:
            return self._wpEvaluation("SignIn").display()


class RHEvaluationDisplayBase( RHBaseEvaluation ):
    """Base for evaluation display."""
    _uh = urlHandlers.UHConfEvaluationDisplay

    def _checkProtection( self ):
        RHBaseEvaluation._checkProtection(self)
        if self._evaluation.inEvaluationPeriod() and self._evaluation.isMandatoryAccount() and not self._getUser():
            self._redirect(urlHandlers.UHConfEvaluationSignIn.getURL(self._conf))
            self._doProcess = False


class RHEvaluationDisplay(RHEvaluationDisplayBase):
    """Evaluation display."""

    def _processIfActive(self):
        return self._evaluationDisplay().display()

    def _evaluationDisplay(self):
        """What to display."""
        if not self._evaluation.inEvaluationPeriod():
            return self._wpEvaluation("Closed")
        elif self._getUser() and self._getUser().hasSubmittedEvaluation(self._evaluation):
            return self._wpEvaluation("DisplayModif")
        elif self._evaluation.isFull():
            return self._wpEvaluation("Full")
        else:
            return self._wpEvaluation("Display")


class RHEvaluationSubmit (RHBaseEvaluation):
    """Submit the evaluation."""

    def _checkParams( self, params ):
        RHBaseEvaluation._checkParams( self, params )
        self._submit = params.has_key("submit")
        self._cancel = params.has_key("cancel")

    def _process( self ):
        ########
        #CANCEL#
        ########
        if self._cancel:
            if self.getWebFactory()!=None : #Event == Meeting/Lecture
                self._redirect(urlHandlers.UHConferenceDisplay.getURL(self._conf))
            else : #Event == Conference
                self._redirect(urlHandlers.UHConfEvaluationMainInformation.getURL(self._conf))

        ########
        #SUBMIT#
        ########
        if self._submit:

            ####################
            #get some variables#
            ####################
            params = self.getRequestParams()
            evaluation = self._conf.getEvaluation()
            mode = params.get("mode","")
            user = self._getUser()

            ##########
            #Checking#
            ##########
            #checking consistency for ALL the questions
            for question in evaluation.getQuestions():
                questionFromForm = "q%s"%question.getPosition()
                answerFromForm = params.get(questionFromForm, [])
                if question.isRequired() and len(answerFromForm)<=0: #len() available for strings and lists
                    raise FormValuesError("Some required fields are not filled in.", "Evaluation")
            #Access checking. (In most cases everything should be ok!)
            #disturbance example: User may log in/out in another window and cause trouble! (very rare!)
            if user!=None:
                if user.hasSubmittedEvaluation(evaluation):                 #evaluation submitted
                    if mode==Evaluation._SUBMIT : mode=Evaluation._EDIT
                else:                                                       #evaluation not submitted
                    if mode==Evaluation._EDIT : mode=Evaluation._SUBMIT
            elif evaluation.isMandatoryAccount() or mode==Evaluation._EDIT :
                    self._userShouldBeLoggedIn()

            ##########
            #Add mode#
            ##########
            if self._submit and mode==Evaluation._SUBMIT:
                #submission
                submission = Submission(evaluation, user)
                #for each question...
                for question in evaluation.getQuestions():
                    questionFromForm = "q%s"%question.getPosition()
                    answerFromForm = params.get(questionFromForm, [])
                    #answer
                    submission.addNewAnswer(question, answerFromForm)
                #notification
                submission.notifySubmissionSubmitted()

            ###########
            #Edit mode#
            ###########
            elif self._submit and mode==Evaluation._EDIT:
                submission = evaluation.getUserSubmission(user)
                if submission!=None :    #should always be the case... but we never know!
                    #for each question...
                    for question in evaluation.getQuestions():
                        questionFromForm = "q%s"%question.getPosition()
                        answerFromForm = params.get(questionFromForm, [])
                        answer = question.getUserAnswer(user)
                        if answer!=None:
                            answer.setAnswerValue(answerFromForm)
                        else: #rare case
                            submission.addNewAnswer(question, answerFromForm)
                    #modification date
                    submission.setModificationDate()
                    #notification
                    submission.notifySubmissionModified()
                elif HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive() :
                    raise Exception("Evaluation - Strange error... the submission of this user was not found!")

            ##########
            #Redirect#
            ##########
            self._redirect(urlHandlers.UHConfEvaluationSubmitted.getURL(self._conf, mode=mode))

    def _userShouldBeLoggedIn(self):
        """Strange error: the logged user is no more logged in..."""
        raise FormValuesError("""Something strange happened here: you are supposed to be logged in.<br/><br/>
                                What I can suggest you to keep your modifications is
                                to open a new window and log in to your indico account.<br/>
                                Then back to this windows, "Go Back" to the previous page and save your changes.
                                """, "Evaluation")


class RHEvaluationSubmitted( RHBaseEvaluation ):
    """Show message : Evaluation submitted."""
    _uh = urlHandlers.UHConfEvaluationMainInformation

    def _processIfActive( self ):
        mode = self.getRequestParams().get("mode","") or Evaluation._SUBMIT
        wf = self.getWebFactory()
        if wf!=None : #Event == Meeting/Lecture
            return wf.getEvaluationSubmitted(self, self._conf, mode).display()
        else : #Event == Conference
            return evaluations.WPEvaluationSubmitted(self, self._conf, mode).display()
