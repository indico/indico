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

from datetime     import datetime, timedelta
from persistent   import Persistent
from registration import Notification
from MaKaC.common import utils
from MaKaC.common.Counter import Counter
from MaKaC.user   import Avatar
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.i18n import _
from pytz import timezone
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.webinterface.mail import GenericMailer, GenericNotification

from indico.modules.scheduler import Client
from indico.modules.scheduler.tasks import AlarmTask
from indico.core.config import Config


class Evaluation(Persistent):
    """Evaluation class : an evaluation belongs to a conference."""

    ###########
    #Constants#
    ###########
    _SUBMIT = "submit"
    _EDIT   = "edit"
    _REMOVE = "remove"
    _SELECT_SUBMITTERS = "select"
    _REMOVE_SUBMITTERS = "remove"
    _CSV_FILENAME      = "evaluation-results.csv"
    _XML_FILENAME      = "myEvaluation.xml"
    _EVALUATION_START  = "evaluationStartNotify" #never change this value!
    _NEW_SUBMISSION    = "newSubmissionNotify"   #never change this value!
    _ALL_NOTIFICATIONS = [_EVALUATION_START, _NEW_SUBMISSION]

    def __init__(self, conf, id=None):
        if id==None :
            self._id = str( conf._getEvaluationCounter().newCount() )
        else :
            self._id = id
        self._conf = conf
        self._questions = []
        self._submissions = []
        self.title = ""                    #must be "" because conf isn't yet ready
        self.setStartDate(datetime(1,1,1)) #must be datetime(1,1,1) because conf isn't yet ready
        self.setEndDate(datetime(1,1,1))   #must be datetime(1,1,1) because conf isn't yet ready
        self.notifications = {}            #contains pairs like this (notificationKey: notification)
        self.alarms = {}                   #contains pairs like this (notificationKey: alarm)
        self.visible = False
        self.anonymous = True
        self.announcement = ""
        self.submissionsLimit = 0
        self.contactInfo = ""
        self.mandatoryParticipant = False
        self.mandatoryAccount = False
        self._submissionCounter = Counter(1)

    def getTimezone(self):
        return self._conf.getTimezone()

    def reinit(self):
        """ reinit the evaluation.
            Note: all current information are lost, except '_id' and '_conf' attributes.
            Advice: the session variable 'selectedSubmissions_<ConfId>_<EvalId>' should be deleted.
        """
        self.removeAllQuestions()
        self.__init__(self.getConference(), self.getId())

    def removeReferences(self):
        """remove all pointers to other objects."""
        self.removeAllAlarms()
        self.removeAllNotifications()
        self.removeAllQuestions()
        self.removeAllSubmissions()
        self._conf = None

    def clone(self, conference):
        """returns a new Evaluation which is a copy of the current one (self)."""
        evaluation = Evaluation(conference)
        evaluation.setId(self.getId())
        evaluation.setTitle(self.getTitle())
        evaluation.setVisible(self.isVisible())
        evaluation.setAnonymous(self.isAnonymous())
        evaluation.setAnnouncement(self.getAnnouncement())
        evaluation.setSubmissionsLimit(self.getSubmissionsLimit())
        evaluation.setContactInfo(self.getContactInfo())
        timeDifference = conference.getStartDate() - self.getConference().getStartDate()
        evaluation.setStartDate(self.getStartDate() + timeDifference)
        evaluation.setEndDate(self.getEndDate() + timeDifference)
        evaluation.setMandatoryAccount(self.isMandatoryAccount())
        evaluation.setMandatoryParticipant(self.isMandatoryParticipant())
        for (notificationKey,notification) in self.getNotifications().items() :
            evaluation.setNotification(notificationKey, notification.clone())
        for q in self.getQuestions():
            evaluation.insertQuestion(q.clone())
        return evaluation

    def exportXml(self, xmlGen):
        """Write xml tags about this object in the given xml generator of type XMLGen."""
        #evaluations/evaluation/ - start
        xmlGen.openTag("evaluation")
        xmlGen.writeTag("id", self.getId())
        xmlGen.writeTag("conferenceId", self.getConference().getId())
        xmlGen.writeTag("title", self.getTitle())
        xmlGen.writeTag("visible", self.isVisible())
        xmlGen.writeTag("anonymous", self.isAnonymous())
        xmlGen.writeTag("announcement", self.getAnnouncement())
        xmlGen.writeTag("submissionsLimit", self.getSubmissionsLimit())
        xmlGen.writeTag("contactInfo", self.getContactInfo())
        xmlGen.writeTag("mandatoryParticipant", self.isMandatoryParticipant())
        xmlGen.writeTag("mandatoryAccount", self.isMandatoryAccount())
        #evaluations/evaluation/notifications/ - start
        xmlGen.openTag("notifications")
        for (notificationKey,notification) in self.getNotifications().items() :
            xmlGen.openTag(notificationKey)
            xmlGen.writeTag( "toList", ", ".join(notification.getToList()) )
            xmlGen.writeTag( "ccList", ", ".join(notification.getCCList()) )
            xmlGen.closeTag(notificationKey)
        #evaluations/evaluation/notifications/ - end
        xmlGen.closeTag("notifications")
        #evaluations/evaluation/questions/ - start
        xmlGen.openTag("questions")
        for question in self.getQuestions() :
            question.exportXml(xmlGen)
        #evaluations/evaluation/questions/ - end
        xmlGen.closeTag("questions")
        #evaluations/evaluation/ - end
        xmlGen.closeTag("evaluation")

    def notifyModification(self):
        """indicates to the database that current object attributes have changed."""
        self._p_changed=1

    def setVisible(self, visible):
        """If visible, the evaluation is allowed to be shown in the Display Area."""
        self.visible = utils._bool(visible)
    def isVisible(self):
        """returns if the evaluation is allowed to be shown in the Display Area."""
        if not hasattr(self, "visible"):
            self.visible = False
        return self.visible

    def setAnonymous(self, anonymous):
        """if True, following submission are anonymous for the surveyor."""
        self.anonymous = utils._bool(anonymous)
    def isAnonymous(self):
        """returns if the following submissions are anonymous for the surveyor."""
        if not hasattr(self, "anonymous"):
            self.anonymous = True
        return self.anonymous

    def setConference(self, conf):
        self._conf = conf
    def getConference(self):
        if not hasattr(self, "_conf"):
            self._conf = None
        return self._conf

    def setId(self, id):
        self._id = str(id)
    def getId(self):
        if not hasattr(self, "_id"):
            self._id = str( conf._getEvaluationCounter().newCount() )
        return self._id

    def setMandatoryParticipant(self, v=True):
        self.mandatoryParticipant = utils._bool(v)
    setMandatoryRegistrant = setMandatoryParticipant
    def isMandatoryParticipant(self):
        if not hasattr(self, "mandatoryParticipant"):
            self.mandatoryParticipant = False
        return self.mandatoryParticipant
    isMandatoryRegistrant = isMandatoryParticipant

    def setMandatoryAccount(self, v=True):
        self.mandatoryAccount = utils._bool(v)
    def isMandatoryAccount(self):
        if not hasattr(self, "mandatoryAccount"):
            self.mandatoryAccount = False
        return self.mandatoryAccount

    def setTitle( self, title ):
        self.title = utils.removeQuotes(title)
    def getTitle( self ):
        if not hasattr(self, "title") or self.title=="":
            conf = self.getConference()
            if conf!=None and conf.getTitle()!="":
                self.title = _("Evaluation for %s")%conf.getTitle()
            else:
                self.title = _("Evaluation")
        return self.title

    def setAnnouncement( self, announcement ):
        self.announcement = utils.removeQuotes(announcement)
    def getAnnouncement( self ):
        if not hasattr(self, "announcement"):
            self.announcement = ""
        return self.announcement

    def setSubmissionsLimit( self, submissionsLimit ):
        self.submissionsLimit = utils._positiveInt(submissionsLimit)
    def getSubmissionsLimit( self ):
        if not hasattr(self, "submissionsLimit"):
            self.submissionsLimit = 0
        return self.submissionsLimit

    def setStartDate( self, sd ):
        self.startDate = datetime(sd.year,sd.month,sd.day,0,0,0)
        for nid, notif in self.getNotifications().iteritems():
            if isinstance(notif, EvaluationAlarm):
                if notif.getStartOn() != sd:
                    notif.move(sd)

    def getStartDate( self ):
        if not hasattr(self, "startDate") or self.startDate==datetime(1,1,1,0,0,0):
            self.setStartDate(self._conf.getEndDate().date() + timedelta(days=1))
        return timezone(self.getTimezone()).localize(self.startDate)

    def setEndDate( self, ed ):
        self.endDate = datetime(ed.year,ed.month,ed.day,23,59,59)
    def getEndDate( self ):
        if not hasattr(self, "endDate") or self.endDate==datetime(1,1,1,23,59,59):
            self.setEndDate(self._conf.getEndDate() + timedelta(days=8))
        return timezone(self.getTimezone()).localize(self.endDate)

    def inEvaluationPeriod(self, date=None):
        if date is None:
            date = nowutc()
        return date >= self.getStartDate() and date <= self.getEndDate()

    def setContactInfo( self, contactInfo ):
        self.contactInfo = utils.removeQuotes(contactInfo)
    def getContactInfo( self ):
        if not hasattr(self, "contactInfo"):
            self.contactInfo = ""
        return self.contactInfo

    def insertQuestion(self, question, position=-1):
        """ Insert a question in this evaluation at the given position (if given, otherwise at the end).
            It also sets questions's evaluation to be this evaluation.
            Note: first position = 1.
        """
        position = utils._int(position)-1    #For list, first position = 0 !!!
        if question not in self.getQuestions():
            if position>=0:
                self.getQuestions().insert(position, question)
            else:
                self.getQuestions().append(question)
        question.setEvaluation(self)
        self.notifyModification()

    def getQuestions(self):
        """get the questions of this evaluation."""
        if not hasattr(self, "_questions"):
            self._questions = []
        return self._questions

    def getQuestionAt(self, position):
        """ get a question from this evalution given by its position.
            Note: first position = 1.
        """
        #check params
        position = utils._int(position)-1    #For list, first position = 0 !!!
        if position<0 or position>=self.getNbOfQuestions() : return None
        #getting...
        questions = self.getQuestions()
        return questions[position]

    def removeQuestion(self, position):
        """ remove and return the questions given by its position from this evaluation.
            Note: first position = 1.
        """
        #check params
        position = utils._int(position)-1    #For list, first position = 0 !!!
        if position<0 or position>=self.getNbOfQuestions() : return None
        #removing...
        q = self.getQuestions().pop(position)
        q.removeReferences()
        self.notifyModification()
        return q

    def removeAllQuestions(self):
        """ remove all the questions of this evaluation.
            Advice: the session variable 'selectedSubmissions_<ConfId>_<EvalId>' should be deleted.
        """
        #remove all submissions
        self.removeAllSubmissions()
        #remove references
        for question in self.getQuestions():
            #destroy links with other objects
            question.removeReferences()
        #reinit
        self._questions = []
        self.notifyModification()

    def getNbOfQuestions(self):
        """get the number of questions contained in this evaluation."""
        return len(self.getQuestions())

    def _getSubmissionCounter(self):
        """returning counter for submitters, useful to give them a unique id."""
        if not hasattr(self, "_submissionCounter"):
            self._submissionCounter = Counter()
        return self._submissionCounter

    def insertSubmission(self, submission):
        """ Insert a submission for this evaluation.
            Params:
                submission -- of type Submission
        """
        if submission not in self.getSubmissions():
            self.getSubmissions().append(submission)
        self.notifyModification()

    def setSubmissions(self, submissions):
        """set the submissions of this evaluation."""
        self._submissions = submissions
    def getSubmissions(self, ids=None):
        """get the submissions of this evaluation."""
        if not hasattr(self, "_submissions"):
            self._submissions = []
        if ids is not None:
            return [s for s in self._submissions if s.getId() in ids]
        return self._submissions

    def getUserSubmission(self, user):
        """ return the submission of the given user, or None if nothing found.
            Params:
                user -- an object generally of type Avatar.
        """
        for submission in self.getSubmissions():
            if submission.getSubmitter()==user :
                return submission
        return None

    def removeSubmission(self, submission):
        """remove the given submission from the submissions list."""
        submissions = self.getSubmissions()
        if submissions.count(submission)>0:
            submissions.remove(submission)
            self.notifyModification()
        submission.removeReferences()

    def removeAllSubmissions(self):
        """ remove all the submissions of this evaluation.
            Advice: the session variable 'selectedSubmissions_<ConfId>_<EvalId>' should be deleted.
        """
        #remove references
        for submission in self.getSubmissions():
            #destroy links with other objects
            submission.removeReferences()
        self._submissions = []
        self.notifyModification()

    def getNbOfSubmissions(self):
        """get the number of submissions contained in this evaluation."""
        return len(self.getSubmissions())

    def isFull(self):
        """If the number of submissions has reached the number of submissions limit, return True. False otherwise."""
        return self.getNbOfSubmissions() >= self.getSubmissionsLimit() and self.getSubmissionsLimit()!=0

    def setNotification( self, notificationKey, notification=None ):
        """ Set a Notification with given notification key and optional Notification instance.
            Do nothing if the notification key is unknown (cf _ALL_NOTIFICATIONS).
            Params:
                notificationKey -- key of the Notification you want to set (cf _ALL_NOTIFICATIONS).
                notification -- optional Notification instance.
        """
        if notificationKey in self._ALL_NOTIFICATIONS :
            self.getNotifications()[notificationKey] = notification or Notification()
            self.notifyModification()
            self.setAlarm(notificationKey)

    def removeNotification(self, notificationKey):
        """remove corresponding Notification with given notification key."""
        notifications = self.getNotifications()
        if notifications.has_key(notificationKey) :
            notifications.pop(notificationKey, None)
            self.notifyModification()
            self.removeAlarm(self.getAlarm(notificationKey))

    def removeAllNotifications(self):
        """remove all notifications."""
        self.notifications = {}
        self.notifyModification()

    def getNotifications(self):
        """get the dictionnary with pairs like this ([int]notificationKey: [Notification]notification)."""
        if not hasattr(self, "notifications"):
            self.notifications = {}
        return self.notifications

    def getNotification(self, notificationKey):
        """For given notification key gets the corresponding Notification or None if not found."""
        return self.getNotifications().get(notificationKey, None)

    def setAlarm(self, notificationKey):
        """Set the id of an Alarm with given notification key (cf _ALL_NOTIFICATIONS)."""
        if self.getStartDate() < nowutc():
            self.removeAlarm(self.getAlarm(notificationKey))
        elif notificationKey == self._NEW_SUBMISSION :
            pass #no need of an alarm for this kind of notification
        elif notificationKey == self._EVALUATION_START :
            notification = self.getNotification(notificationKey)
            if notification != None:
                from MaKaC.webinterface import urlHandlers
                alarm = self.getAlarm(notificationKey)
                if alarm == None :
                    alarm = EvaluationAlarm(self, notificationKey)
                    self.getConference().addAlarm(alarm)
                    self.getAlarms()[notificationKey] = alarm

                    self.notifyModification()
                else:
                    if self.getStartDate() != alarm.getStartOn():
                        alarm.move(self.getStartDate())

                alarm.setFromAddr( Config.getInstance().getSupportEmail() )
                alarm.setToAddrList(notification.getToList())
                alarm.setCcAddrList(notification.getCCList())
                alarm.setSubject( self.getTitle() )
                url = urlHandlers.UHConfEvaluationDisplay.getURL(self.getConference())
                alarm.setText( _("Hello,\n\nPlease answer this survey :\n%s\n\nBest Regards")%url)

    def removeAlarm(self, alarm):
        """Remove given Alarm."""
        if alarm is not None:
            if self.getConference().getAlarmById(alarm.getConfRelativeId()) is not None:
                self.getConference().removeAlarm(alarm)
            self.getAlarms().pop(alarm.getNotificationKey(), None)
            self.notifyModification()

    def removeAllAlarms(self):
        """remove all alarms."""
        alarms = self.getAlarms()

        for alarm in alarms.values() :
            self.getConference().removeAlarm(alarm)
        self.alarms = {}
        self.notifyModification()

    def getAlarms(self):
        """get the dictionnary with pairs like this ([int]notificationKey: [Alarm]alarm)."""
        if not hasattr(self, "alarms"):
            self.alarms = {}
        return self.alarms

    def getAlarm(self, notificationKey):
        """For given notification key gets the corresponding Alarm or None if not found."""
        alarm = self.getAlarms().get(notificationKey, None)
        #Integrity check
        if alarm!=None and self.getConference().getAlarmById(alarm.getId())==None :
            self.removeAlarm(alarm)
            return None
        return alarm


class EvaluationAlarm(AlarmTask):
    """Suited alarm for an evaluation."""

    def __init__(self, evaluation, notificationKey):
        self._evaluation = evaluation
        self.notificationKey = notificationKey  #cf Evaluation._ALL_NOTIFICATIONS
        super(EvaluationAlarm, self).__init__(evaluation.getConference(),
                                              'Eval_%s' % notificationKey,
                                              evaluation.getStartDate())

    def setEvaluation(self, evaluation):
        self._evaluation = evaluation

    def getEvaluation(self):
        if not hasattr(self, "_evaluation"):
            self._evaluation = None
        return self._evaluation

    def setNotificationKey(self, notificationKey):
        self.notificationKey = notificationKey

    def getNotificationKey(self):
        if not hasattr(self, "notificationKey"):
            self.notificationKey = None
        return self.notificationKey

    def move(self, newDate):
        c = Client()
        c.moveTask(self, newDate)

    def delete(self):
        evaluation = self.getEvaluation()
        if evaluation is not None:
            evaluation.removeAlarm(self)
        self.setEvaluation(None)

    def _prepare(self, check=True):

        # date checking...
        from MaKaC.conference import ConferenceHolder
        evaluation = self.getEvaluation()
        notificationKey = self.getNotificationKey()
        evalEndDate = evaluation.getEndDate().date()
        today = nowutc().date()
        if not ConferenceHolder().hasKey(self.conf.getId()) or \
                evaluation.getNbOfQuestions() < 1 or \
                not evaluation.isVisible() or \
                (notificationKey == Evaluation._EVALUATION_START and \
                evalEndDate < today and check):
            self.conf.removeAlarm(self)
            self.suicide()
            return False  # email aborted
        return True  # email ok


class Question(Persistent):
    """Question class : a question belongs to an evaluation."""

    ###########
    #Constants#
    ###########
    #Modes:
    _ADD      = "add"
    _EDIT     = "edit"
    _REMOVE   = "remove"
    #question type names: subclasses
    _TEXTBOX  = "TextBox"
    _TEXTAREA = "TextArea"
    _PASSWORD = "PasswordBox"
    _SELECT   = "Select"
    _RADIO    = "RadioButton"
    _CHECKBOX = "CheckBox"
    #question type names: superclasses
    _BOX               = "Box"
    _CHOICE            = "Choice"
    _BOX_SUBTYPES      = [_TEXTBOX, _TEXTAREA, _PASSWORD]
    _CHOICE_SUBTYPES   = [_CHECKBOX, _RADIO, _SELECT]
    #question type names: topclasses
    _QUESTION          = "Question"
    _QUESTION_SUBTYPES = _BOX_SUBTYPES + _CHOICE_SUBTYPES

    def __init__(self):
        self._evaluation = None
        self._answers = []
        self.questionValue = "" #The question itself (text)
        self.keyword = ""
        self.required = False
        self.description = ""
        self.help = ""
#        self.level = 1

    def removeReferences(self):
        """remove all pointers to other objects."""
        self._evaluation = None
        self.removeAllAnswers()

    def clone(self):
        """returns a new Question which is a copy of the current one (self)."""
        q = self.getClass()() #e.g. if self is Textbox, it's the same as "q = Textbox()"
        q.setQuestionValue(self.getQuestionValue())
        q.setKeyword(self.getKeyword())
        q.setRequired(self.isRequired())
        q.setDescription(self.getDescription())
        q.setHelp(self.getHelp())
#        q.setLevel(self.getLevel())
        return q

    def _exportCommonAttributesXml(self, xmlGen):
        """Write xml tags about common question attributes in the given xml generator of type XMLGen."""
        xmlGen.writeTag("questionValue", self.getQuestionValue())
        xmlGen.writeTag("keyword", self.getKeyword())
        xmlGen.writeTag("required", self.isRequired())
        xmlGen.writeTag("description", self.getDescription())
        xmlGen.writeTag("help", self.getHelp())

    def removeAnswer(self, answer):
        """remove the given answer from its answers."""
        answers = self.getAnswers()
        if answers.count(answer)>0:
            answers.remove(answer)
            self.notifyModification()
        answer.removeReferences()

    def removeAllAnswers(self):
        """remove all the answers of this question."""
        #remove all answers and links to them
        for answer in self.getAnswers():
            submission = answer.getSubmission()
            submission.removeAnswer(answer)
            #delete the submission if it contains no more question
            if submission.getNbOfAnswers()<1:
                submission.removeReferences()
        #reinit
        self._answers = []
        self.notifyModification()

    def notifyModification(self):
        """indicates to the database that current object attributes have changed."""
        self._p_changed=1

    def setEvaluation(self, evaluation):
        """Sets the evaluation to which this question belongs."""
        self._evaluation = evaluation
    def getEvaluation(self):
        """gets the evaluation to which this question belongs."""
        if not hasattr(self, "_evaluation"):
            self._evaluation = None
        return self._evaluation

    def getTypeName(self):
        """gets type name of this question."""
        return self._QUESTION

    def getClass(self):
        """gets the class of this object."""
        return self.__class__

    def getClassName(self):
        """gets the class name of this object."""
        return self.getClass().__name__

    def setQuestionValue(self, questionValue):
        """sets the question itself (i.e. the text), not a Question object."""
        self.questionValue = utils.removeQuotes(questionValue)
    def getQuestionValue(self):
        """returns the question itself (i.e. the text), not a Question object."""
        if not hasattr(self, "questionValue"):
            self.questionValue = ""
        return self.questionValue

    def setKeyword(self, keyword):
        """Set the keyword. A keyword is the question summarised in one word."""
        self.keyword = utils.removeQuotes(keyword)
    def getKeyword(self):
        """Get the keyword. A keyword is the question summarised in one word."""
        if not hasattr(self, "keyword"):
            self.keyword = ""
        return self.keyword

    def setRequired(self, required):
        """Set if an answer for the question is required."""
        self.required = utils._bool(required)
    def isRequired(self):
        """Get if an answer for the question is required."""
        if not hasattr(self, "required"):
            self.required = False
        return self.required

    def setDescription(self, description):
        self.description = utils.removeQuotes(description)
    def getDescription(self):
        if not hasattr(self, "description"):
            self.description = ""
        return self.description

    def setHelp(self, help):
        """sets help message."""
        self.help = utils.removeQuotes(help)
    def getHelp(self):
        """gets help message."""
        if not hasattr(self, "help"):
            self.help = ""
        return self.help

    def setPosition(self, position):
        """ sets position of a question within a form.
            Note: first position = 1.
        """
        position = utils._positiveInt(position)
        if position != self.getPosition():
            questionsList = self.getEvaluation().getQuestions()
            q = questionsList.pop(self.getPosition()-1) #For list, first position = 0 !
            self.getEvaluation().insertQuestion(q, position)
    def getPosition(self):
        """ gets position of a question within a form.
            Note: first position = 1.
        """
        return self.getEvaluation().getQuestions().index(self)+1

#    def setLevel(self, level):
#        """ sets level of a question, used for multipart questions. (e.g. 1.1,1.1a, 1.1b,...)
#            The lower the level, the higher its importance.
#        """
#        self.level = utils._positiveInt(level)
#    def getLevel(self):
#        """ gets level of a question, used for multipart questions. (e.g. 1.1,1.1a, 1.1b,...)
#            The lower the level, the higher its importance.
#        """
#        if not hasattr(self, "level"):
#            self.level = 1
#        return self.level

    def insertAnswer(self, answer):
        """Insert an answer for this question. It also sets answer's question to be this question."""
        if answer not in self.getAnswers():
            self.getAnswers().append(answer)
        answer.setQuestion(self)
        self.notifyModification()

    def getAnswers(self, selectedSubmissions=None):
        """ get the answers for this question.
            This function is a shortcut for getting answers easily from this question.
            In fact, answers and questions are not directly bound.
            Params:
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        #check
        if not hasattr(self, "_answers"):
            self._answers = []
        if selectedSubmissions is None:
            return self._answers
        #do all the gestion for the answers of a question !
        tempAnswers = []
        for answer in self._answers:
            if answer.getSubmission().getId() in selectedSubmissions:
                tempAnswers.append(answer)
        return tempAnswers

    def getNbOfAnswers(self, selectedSubmissions=None):
        """ get the number of answers for this question.
            Params:
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        return len(self.getAnswers(selectedSubmissions))

    def getNbOfFilledAnswers(self, selectedSubmissions=None):
        """ returns the number of not empty answers.
            Params:
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        nb = 0
        for answer in self.getAnswers(selectedSubmissions):
            if answer.hasAnswerValue():
                nb += 1
        return nb

    def areAllAnswersFilled(self, selectedSubmissions=None):
        """ returns True if all the answers are filled, False otherwise.
            Params:
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        return self.getNbOfFilledAnswers(selectedSubmissions) == self.getNbOfAnswers(selectedSubmissions)

    def printAreAllAnswersFilled(self, selectedSubmissions=None):
        return "%s %s"%(self.getNbOfFilledAnswers(selectedSubmissions), self.getNbOfAnswers(selectedSubmissions))

    def getUserAnswer(self, user):
        """ return the answer (of type Answer) of the given user, or None if nothing found.
            Params:
                user -- an object generally of type Avatar.
        """
        for answer in self.getAnswers():
            if answer.getSubmission().getSubmitter()==user :
                return answer
        return None

    def getUserAnswerValue(self, user):
        """ return the answer value (of type str) of the given user, or None if nothing found.
            Params:
                user -- an object generally of type Avatar.
        """
        answer = self.getUserAnswer(user)
        if answer==None:
            return None
        else:
            return answer.getAnswerValue()


class Box(Question):
    """A Box is a question to which you answer with the help of a box (e.g. Textbox, TextArea, PasswordBox)."""

    def __init__(self):
        Question.__init__(self)
        self.defaultAnswer = ""

    def clone(self):
        """returns a new Question which is a copy of the current one (self).
        """
        q = Question.clone(self)
        q.setDefaultAnswer(self.getDefaultAnswer())
        return q

    def exportXml(self, xmlGen):
        """Write xml tags about this object in the given xml generator of type XMLGen."""
        xmlGen.openTag(self.getClassName())
        self._exportCommonAttributesXml(xmlGen)
        xmlGen.writeTag("defaultAnswer", self.getDefaultAnswer())
        xmlGen.closeTag(self.getClassName())

    def setDefaultAnswer(self, defaultAnswer):
        """sets the default answer of the question."""
        self.defaultAnswer = utils.removeQuotes(defaultAnswer)
    def getDefaultAnswer(self):
        """gets the default answer of the question."""
        if not hasattr(self, "defaultAnswer"):
            self.defaultAnswer = ""
        return self.defaultAnswer

    def getTypeName(self):
        """gets type name of this question."""
        return self._BOX


class Choice(Question):
    """A Choice is a question to which you answer with the help of a multiple choices (e.g. Radio buttons, Checkboxes, ...)."""

    def __init__(self):
        Question.__init__(self)
        self.choiceItems = {};
        self.choiceItemsOrderedKeys = [] #I want to keep the order the user inserted them.

    def clone(self):
        """returns a new Question which is a copy of the current one (self).
        """
        q = Question.clone(self)
        for key in self.getChoiceItemsOrderedKeys():
            q.insertChoiceItem(key, self.getChoiceItemsCorrespondingValue(key))
        return q

    def exportXml(self, xmlGen):
        """Write xml tags about this object in the given xml generator of type XMLGen."""
        xmlGen.openTag(self.getClassName())
        self._exportCommonAttributesXml(xmlGen)
        xmlGen.openTag("choiceItems")
        for itemText in self.getChoiceItemsOrderedKeys() :
            xmlGen.openTag("choiceItem")
            xmlGen.writeTag("itemText", itemText)
            xmlGen.writeTag("isSelected", self.getChoiceItemsCorrespondingValue(itemText))
            xmlGen.closeTag("choiceItem")
        xmlGen.closeTag("choiceItems")
        xmlGen.closeTag(self.getClassName())

    def insertChoiceItem(self, itemText, isSelected):
        """ Insert a new choice item in the dictionnary.
            A choiceItem is a pair like this : (itemText,isSelected).

            Params:
                itemText -- [str] text of the choiceItem.
                isSelected -- [bool] if the choiceItem is selected.
        """
        #check params
        itemText = utils.removeQuotes(itemText)
        isSelected = utils._bool(isSelected)
        #adding new item...
        if itemText!=None and itemText!="" and itemText not in self.getChoiceItemsOrderedKeys():
            self.getChoiceItems()[itemText] = isSelected
            self.getChoiceItemsOrderedKeys().append(itemText)
        #notify
        self.notifyModification()

    def getChoiceItems(self):
        """Gets the dictionary of choice items. Its elements are pairs like this (itemText:isSelected)."""
        if not hasattr(self, "choiceItems"):
            self.choiceItems = {};
        return self.choiceItems

    def getChoiceItemsOrderedKeys(self):
        """ Gets the list of ordered keys (itemText of type str) for choice items.
            The keys are ordered in the same order as the user inserted them.
        """
        if not hasattr(self, "choiceItemsOrderedKeys"):
            self.choiceItemsOrderedKeys = []
        return self.choiceItemsOrderedKeys

    def getChoiceItemsKeyAt(self, position):
        """ Gets the key (itemText) at the given position.
            Note: first position = 1.
        """
        #check params
        position = utils._int(position)-1    #For list, first position = 0 !!!
        keys = self.getChoiceItemsOrderedKeys()
        if position<0 or position>=len(keys) : return ""
        return keys[position]

    def getChoiceItemsCorrespondingValue(self, itemText):
        """ Given the key (itemText) returns the corresponding value (isSelected). """
        return self.getChoiceItems().get(itemText, False)

    def getNbOfChoiceItems(self):
        """Gets the number of choice items."""
        choiceItemsNb = len(self.getChoiceItems())
        choiceItemsOrderedKeysNb = len(self.getChoiceItemsOrderedKeys())
        #both should always be the same, but... we never know!
        return min([choiceItemsNb , choiceItemsOrderedKeysNb])

    def removeAllChoiceItems(self):
        """remove all the choice items for this question."""
        self.choiceItems = {}
        self.choiceItemsOrderedKeys = []
        self.notifyModification()

    def getDefaultAnswers(self):
        """gets the default answers (list of strings) of the question."""
        keys = self.getChoiceItems().keys()
        vals = self.getChoiceItems().values()
        index=0
        defaultAnswers=[]
        for val in vals:
            if val :
                defaultAnswers.append(keys[index])
            index+=1
        return defaultAnswers

    def getTypeName(self):
        """gets type name of this question."""
        return self._CHOICE


class Textbox(Box):

    def __init__(self):
        Box.__init__(self)

    def getTypeName(self):
        """gets type name of this question."""
        return self._TEXTBOX

    def getAnswerClass(self):
        """gets the class of the corresponding answer(s) for this question."""
        return TextAnswer

    def displayHtml(self, **attributes):
        """ Display the question in HTML.
            Params:
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        attributes["type"] = "text"
        attributes["class"] = "textType"
        attributes["value"] = self.getDefaultAnswer()
        return WUtils.createInput(**attributes)

    def displayHtmlWithUserAnswer(self, user, **attributes):
        """ Display the question in HTML with the answer of given user.
            Params:
                user -- object generally of type Avatar.
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        attributes["type"] = "text"
        attributes["class"] = "textType"
        attributes["value"] = self.getUserAnswerValue(user)
        return WUtils.createInput(**attributes)


class Textarea(Box):

    def __init__(self):
        Box.__init__(self)

    def getTypeName(self):
        """gets type name of this question."""
        return self._TEXTAREA

    def getAnswerClass(self):
        """gets the class of the corresponding answer(s) for this question."""
        return TextAnswer

    def displayHtml(self, **attributes):
        """ Display the question in HTML.
            Params:
                attributes -- dictionary of attributes for <textarea>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        return WUtils.createTextarea(self.getDefaultAnswer(), **attributes)

    def displayHtmlWithUserAnswer(self, user, **attributes):
        """ Display the question in HTML with the answer of given user.
            Params:
                user -- object generally of type Avatar.
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        return WUtils.createTextarea(self.getUserAnswerValue(user), **attributes)


class Password(Box):

    def __init__(self):
        Box.__init__(self)

    def getTypeName(self):
        """gets type name of this question."""
        return self._PASSWORD

    def getAnswerClass(self):
        """gets the class of the corresponding answer(s) for this question."""
        return TextAnswer

    def displayHtml(self, **attributes):
        """ Display the question in HTML.
            Params:
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        attributes["type"] = "password"
        attributes["class"] = "passwordType"
        attributes["value"] = self.getDefaultAnswer()
        return WUtils.createInput(**attributes)

    def displayHtmlWithUserAnswer(self, user, **attributes):
        """ Display the question in HTML with the answer of given user.
            Params:
                user -- object generally of type Avatar.
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        attributes["type"] = "password"
        attributes["class"] = "passwordType"
        attributes["value"] = self.getUserAnswerValue(user)
        return WUtils.createInput(**attributes)


class Select(Choice):

    def __init__(self):
        Choice.__init__(self)

    def getDefaultAnswer(self):
        """gets the default answer (string) of the question."""
        defaultAnswers = self.getDefaultAnswers()
        if len(defaultAnswers)>0:
            return defaultAnswers.pop()
        else:
            return ""

    def getTypeName(self):
        """gets type name of this question."""
        return self._SELECT

    def getAnswerClass(self):
        """gets the class of the corresponding answer(s) for this question."""
        return TextAnswer

    def displayHtml(self, **attributes):
        """ Display the question in HTML.
            Params:
                attributes -- dictionary of attributes for <select>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        options  = self.getChoiceItemsOrderedKeys()
        selected = self.getDefaultAnswer()
        return WUtils.createSelect(True, options, selected, **attributes)

    def displayHtmlWithUserAnswer(self, user, **attributes):
        """ Display the question in HTML with the answer of given user.
            Params:
                user -- object generally of type Avatar.
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        options  = self.getChoiceItemsOrderedKeys()
        selected = self.getUserAnswerValue(user)
        return WUtils.createSelect(True, options, selected, **attributes)

    def getNbOfAnswersLike(self, answerValue, selectedSubmissions=None):
        """ [Statistics] Give the number of answers which are the same as the given answer value.
            Params:
                answerValue -- given answer value of type string.
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        try:
            nb = 0
            for answer in self.getAnswers(selectedSubmissions):
                if answer.getAnswerValue()==str(answerValue):
                    nb += 1
            return nb
        except:
            return 0

    def getPercentageAnswersLike(self, answerValue, selectedSubmissions=None):
        """ [Statistics] Give the percentage of answers like given answer value.
            Params:
                answerValue -- given answer value of type string.
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        try:
            percent = float(self.getNbOfAnswersLike(answerValue,selectedSubmissions))*100/self.getNbOfAnswers(selectedSubmissions)
            return utils._positiveInt(round(percent))
        except:
            return 0


class Radio(Choice):

    def __init__(self):
        Choice.__init__(self)

    def getDefaultAnswer(self):
        """gets the default answer (text) of the question."""
        defaultAnswers = self.getDefaultAnswers()
        if len(defaultAnswers)>0:
            return defaultAnswers.pop()
        else:
            return ""

    def getTypeName(self):
        """gets type name of this question."""
        return self._RADIO

    def getAnswerClass(self):
        """gets the class of the corresponding answer(s) for this question."""
        return TextAnswer

    def displayHtml(self, **attributes):
        """ Display the question in HTML.
            Params:
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        attributes["type"] = "radio"
        choiceItemsHTML = ""
        for itemText in self.getChoiceItemsOrderedKeys():
            attributes["value"] = itemText
            isSelected = self.getChoiceItemsCorrespondingValue(itemText)
            if isSelected :
                attributes["checked"]="checked"
            else:
                attributes.pop("checked", None)
            choiceItemsHTML += WUtils.appendNewLine(WUtils.createInput(itemText, **attributes))
        return choiceItemsHTML

    def displayHtmlWithUserAnswer(self, user, **attributes):
        """ Display the question in HTML with the answer of given user.
            Params:
                user -- object generally of type Avatar.
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        attributes["type"] = "radio"
        choiceItemsHTML = ""
        for itemText in self.getChoiceItemsOrderedKeys():
            attributes["value"] = itemText
            if itemText==self.getUserAnswerValue(user) :
                attributes["checked"]="checked"
            else:
                attributes.pop("checked", None)
            choiceItemsHTML += WUtils.appendNewLine(WUtils.createInput(itemText, **attributes))
        return choiceItemsHTML

    def getNbOfAnswersLike(self, answerValue, selectedSubmissions=None):
        """ [Statistics] Give the number of answers which are the same as the given answer value.
            Params:
                answerValue -- given answer value of type string.
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        try:
            nb = 0
            for answer in self.getAnswers(selectedSubmissions):
                if answer.getAnswerValue()==str(answerValue):
                    nb += 1
            return nb
        except:
            return 0

    def getPercentageAnswersLike(self, answerValue, selectedSubmissions=None):
        """ [Statistics] Give the percentage of answers like given answer value.
            Params:
                answerValue -- given answer value of type string.
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        try:
            percent = float(self.getNbOfAnswersLike(answerValue,selectedSubmissions))*100/self.getNbOfAnswers(selectedSubmissions)
            return utils._positiveInt(round(percent))
        except:
            return 0


class Checkbox(Choice):

    def __init__(self):
        Choice.__init__(self)

    def getTypeName(self):
        """gets type name of this question."""
        return self._CHECKBOX

    def getAnswerClass(self):
        """gets the class of the corresponding answer(s) for this question."""
        return MultipleChoicesAnswer

    def displayHtml(self, **attributes):
        """ Display the question in HTML.
            Params:
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        attributes["type"] = "checkbox"
        choiceItemsHTML = ""
        for itemText in self.getChoiceItemsOrderedKeys():
            attributes["value"] = itemText
            isSelected = self.getChoiceItemsCorrespondingValue(itemText)
            if isSelected :
                attributes["checked"]="checked"
            else:
                attributes.pop("checked", None)
            choiceItemsHTML += WUtils.appendNewLine(WUtils.createInput(itemText, **attributes))
        return choiceItemsHTML

    def displayHtmlWithUserAnswer(self, user, **attributes):
        """ Display the question in HTML with the answer of given user.
            Params:
                user -- object generally of type Avatar.
                attributes -- dictionary of attributes for <input>.
        """
        from MaKaC.webinterface.wcomponents import WUtils
        attributes["type"] = "checkbox"
        choiceItemsHTML = ""
        choiceItemsOrderedKeys = self.getChoiceItemsOrderedKeys()
        userAnswerValue = self.getUserAnswerValue(user)
        if userAnswerValue==None:
            userAnswerValue=[]
        for itemText in choiceItemsOrderedKeys:
            attributes["value"] = itemText
            if itemText in userAnswerValue:
                attributes["checked"]="checked"
            else:
                attributes.pop("checked", None)
            choiceItemsHTML += WUtils.appendNewLine(WUtils.createInput(itemText, **attributes))
        return choiceItemsHTML

    def getNbOfAnswersLike(self, answerValue, selectedSubmissions=None):
        """ [Statistics] Give the number of answers which are the same as the given answer value.
            Params:
                answerValue -- given answer value of type string.
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        nb = 0
        for answer in self.getAnswers(selectedSubmissions):
            for selectedChoiceItem in answer.getSelectedChoiceItems():
                if str(selectedChoiceItem)==str(answerValue):
                    nb += 1
        return nb

    def getNbOfAllSelectedChoiceItems(self, selectedSubmissions=None):
        """ [Statistics] Returns the number of all selected choice items for all answers for this question.
            Params:
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        try:
            nb = 0
            for answer in self.getAnswers(selectedSubmissions):
                nb += answer.getNbOfSelectedChoiceItems()
            return nb
        except:
            return 0

    def getPercentageAnswersLike(self, answerValue, selectedSubmissions=None):
        """ [Statistics] Give the percentage of answers like given answer value.
            Params:
                answerValue -- given answer value of type string.
                selectedSubmissions -- [list of Submission] Only answers whose submission belongs in this list are treated.
                                       If the list is empty, we treat all the answers.
        """
        try:
            percent = float(self.getNbOfAnswersLike(answerValue,selectedSubmissions))*100/self.getNbOfAllSelectedChoiceItems(selectedSubmissions)
            return utils._positiveInt(round(percent))
        except:
            return 0



class Answer(Persistent):
    """Answer for a corresponding question..."""

    def __init__(self):
        self._question = None
        self._submission = None

    def removeReferences(self):
        """remove all pointers to other objects."""
        self._question = None
        self._submission = None

    def setQuestion(self, q):
        """Set the corresponding Question of this Answer."""
        self._question = q
    def getQuestion(self):
        """Get the corresponding Question of this Answer."""
        if not hasattr(self, "_question"):
            self._question = None
        return self._question

    def setSubmission(self, s):
        """Set the submission to which this answer belongs."""
        self._submission = s
    def getSubmission(self):
        """ Get submission to which this answer belongs.
            If the event is a conference: he is a Participant.
            Otherwise (lecture, meeting): he is a Registrant.
        """
        if not hasattr(self, "_submission"):
            self._submission = None
        return self._submission


class TextAnswer(Answer):
    """Answer which is just a text. (e.g. for Textbox, Textarea, Passwordbox, RadioButtons, Select)"""

    def __init__(self):
        Answer.__init__(self)
        self._answerValue = ""

    def setAnswerValue(self, a):
        """Set the answer value (str) of this object Answer."""
        if a==[] or a==None: a=""
        self._answerValue = utils.removeQuotes(a)

    def getAnswerValue(self):
        """Get the answer value (str) of this object Answer."""
        if not hasattr(self, "_answerValue"):
            self._answerValue = ""
        return self._answerValue

    def hasAnswerValue(self):
        """Returns False if the answer value is empty, True otherwise."""
        return self.getAnswerValue()!=""


class MultipleChoicesAnswer(Answer):
    """Answer (list of selected items) for a question with multiple choices (i.e. Checkbox)."""

    def __init__(self):
        Answer.__init__(self)
        self._selectedChoiceItems = [] #list of str

    def setSelectedChoiceItems(self, selectedAnswers):
        """ Sets the list of selected choice items.

            Params:
                selectedAnswers -- [str or list-of-str] selected answers for the question.
        """
        if selectedAnswers=="" or selectedAnswers==None:
            self._selectedChoiceItems = []
        elif isinstance(selectedAnswers, str):
            self._selectedChoiceItems = [utils.removeQuotes(selectedAnswers)]
        elif isinstance(selectedAnswers, list):
            self._selectedChoiceItems = [utils.removeQuotes(ci) for ci in selectedAnswers]
        self.notifyModification()
    setAnswerValue = setSelectedChoiceItems

    def getSelectedChoiceItems(self):
        """ Gets the list of selected choice items (str).
        """
        if not hasattr(self, "_selectedChoiceItems"):
            self._selectedChoiceItems = []
        return self._selectedChoiceItems
    getAnswerValue = getSelectedChoiceItems

    def hasSelectedChoiceItems(self):
        """Returns False if the answer value is empty, True otherwise."""
        return self.getNbOfSelectedChoiceItems()>0
    hasAnswerValue = hasSelectedChoiceItems

    def getNbOfSelectedChoiceItems(self):
        """ Gets the number of selected choice items. """
        return len(self.getSelectedChoiceItems())

    def removeAllSelectedChoiceItems(self):
        """remove all the selected choice items for this question."""
        self._selectedChoiceItems = []
        self.notifyModification()

    def notifyModification(self):
        """indicates to the database that current object attributes have changed."""
        self._p_changed=1


class Submission(Persistent):
    """When you submit an evaluation, you create a Submission instance."""

    def __init__(self, evaluation, submitter):
        """ Initiation + insert this submission in evaluation's submissions.
            Params:
                evaluation -- [Evaluation] evaluation to which this submission belongs.
                submitter -- [Avatar/None] submitter who submitted this submission.
        """
        self._evaluation = evaluation
        self.setSubmitter(submitter)
        self._id = str( evaluation._getSubmissionCounter().newCount() )
        self._answers = []
        self.submissionDate = nowutc()
        self.modificationDate = None
        self.anonymous = evaluation.isAnonymous()
        self._evaluation.insertSubmission(self)

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        if self.getConference() == other.getConference():
            return cmp(self.getId(), other.getId())
        return cmp(self.getConference(), other.getConference())

    def removeReferences(self):
        """remove all pointers to other objects."""
        self._evaluation = None
        self.removeSubmitter()
        self.removeAllAnswers()

    def setId(self, id):
        self._id = str(id)

    def getId(self):
        if not hasattr(self, "_id"):
            self._id = str( self._evaluation._getSubmissionCounter().newCount() )
        return self._id

    def notifyModification(self):
        """indicates to the database that current object attributes have changed."""
        self._p_changed=1

    def setEvaluation(self, evaluation):
        """Sets the evaluation to which this submission is bound."""
        self._evaluation = evaluation
    def getEvaluation(self):
        """gets the evaluation to which this submission is bound."""
        if not hasattr(self, "_evaluation"):
            self._evaluation = None
        return self._evaluation

    def getConference(self):
        """gets the conference to which this submission's evaluation is bound."""
        evaluation = self.getEvaluation()
        if evaluation:
            return evaluation.getConference()

    def setAnonymous(self, anonymous):
        """if True, submission is anonymous."""
        self.anonymous = utils._bool(anonymous)
    def isAnonymous(self):
        """returns if the submission is anonymous."""
        if not hasattr(self, "anonymous"):
            self.anonymous = True
        return self.anonymous

    def setSubmitter(self, submitter):
        """Set the submitter. He is of type None when anonymous, Avatar otherwise."""
        if isinstance(submitter, Avatar) :
            submitter.linkTo(self, "submitter")
        self._submitter = submitter
    def getSubmitter(self):
        """ Get the submitter. He is of type None when anonymous, Avatar otherwise."""
        if not hasattr(self, "_submitter"):
            self._submitter = None
        return self._submitter
    def removeSubmitter(self):
        """remove the submitter, i.e. he is set to None."""
        submitter = self.getSubmitter()
        if isinstance(submitter, Avatar) :
            submitter.unlinkTo(self, "submitter")
        self._submitter = None

    def getSubmitterName(self):
        """returns name of submitter"""
        submitter = self.getSubmitter()
        if not self.isAnonymous() and isinstance(submitter, Avatar) :
            return submitter.getFullName()
        else :
            return "Anonymous (%s)"%self.getId()

    def notifyByEmail(self, message=""):
        """Notifies concerned people (given by To and Cc) by email about the given message [str]."""
        try:
            evaluation = self.getEvaluation()
            newSubmissionNotify = evaluation.getNotification(Evaluation._NEW_SUBMISSION)
            if newSubmissionNotify != None :
                toList = newSubmissionNotify.getToList()
                ccList = newSubmissionNotify.getCCList()
                if len(toList+ccList) > 0 :
                    subject = "Notification for evaluation '%s'"%evaluation.getTitle()
                    conf = evaluation.getConference()
                    supportEmail = conf.getSupportInfo().getEmail(returnNoReply=True, caption=True)

                    notification = GenericNotification({'fromAddr': supportEmail,
                                                        'toList': toList,
                                                        'ccList': ccList,
                                                        'subject': subject,
                                                        'body': message})

                    GenericMailer.send(notification)
        except Exception, e:
            if HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive():
                raise Exception(e)

    def notifySubmissionSubmitted(self):
        """notification when a new submission arrive."""
        evaluation = self.getEvaluation()
        self.notifyByEmail( _("""New submission from *%s* for \nevaluation *%s*.
                            """)%(self.getSubmitterName(), evaluation.getTitle()) )

    def notifySubmissionModified(self):
        """notification when a submission is modified."""
        evaluation = self.getEvaluation()
        self.notifyByEmail( _("""*%s* modified his submission for \nevaluation *%s*.
                            """)%(self.getSubmitterName(), evaluation.getTitle()) )

    def addNewAnswer(self, question, answerValue):
        """ Add a new answer for this submission.
            Params:
                question -- of type Question
                answerValue -- of type str / list of str
        """
        answer = question.getAnswerClass()() #instantiate a new corresponding Answer()
        answer.setSubmission(self)
        question.insertAnswer(answer)
        answer.setAnswerValue(answerValue) #answer's question must be set!!! (done through question.insertAnswer)
        self.getAnswers().append(answer)
        self.notifyModification()

    def getAnswers(self):
        """get the answers of this submission."""
        if not hasattr(self, "_answers"):
            self._answers = []
        return self._answers

    def getNbOfAnswers(self):
        """get the number of answers for this question."""
        return len(self.getAnswers())

    def removeAnswer(self, answer):
        """remove the given answer from its answers."""
        answers = self.getAnswers()
        if answers.count(answer)>0:
            answers.remove(answer)
            self.notifyModification()
        answer.removeReferences()

    def removeAllAnswers(self):
        """remove all the answers of this submission."""
        #remove all answers and links to them
        for answer in self.getAnswers():
            answer.getQuestion().removeAnswer(answer)
        #reinit
        self._answers = []
        self.notifyModification()

    def getDictQuestionsAnswers(self):
        """ Returns a dictionnary like this {Question : Answer},
            with a Question as key and its corresponding Answer as value.
            Helpful because submission.getAnswers() order doesn't
            correspond necessarily to evaluation.getQuestions() order.
            Note: A question without answers doesn't appear in the dictionary.
        """
        dictQuestionsAnswers = {}
        for answer in self.getAnswers() :
            dictQuestionsAnswers[answer.getQuestion()] = answer
        return dictQuestionsAnswers

    def getSubmissionDate(self, format=datetime):
        """ Get the submission date.
            Params:
                format -- output format (datetime or str)
        """
        if not hasattr(self, "submissionDate"):
            self.submissionDate = nowutc()
        if format==str :
            return self.submissionDate.strftime("%x %H:%M")
        else:
            return self.submissionDate

    def setModificationDate(self):
        """Update the modification date (of type 'datetime') to now."""
        self.modificationDate = nowutc()
    def getModificationDate(self, format=datetime):
        """ If the format is str:
                get the modification date (of type 'str'), or "" if there is no modification.
            Else:
                get the modification date (of type 'datetime'), or None if there is no modification.

            Params:
                format -- output format (datetime or str)
        """
        if not hasattr(self, "modificationDate"):
            self.modificationDate = None
        if format==str :
            if self.modificationDate==None :
                return ""
            else :
                return self.modificationDate.strftime("%x %H:%M")
        else :
            return self.modificationDate
