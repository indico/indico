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

from flask import redirect, url_for, request
from werkzeug.exceptions import NotFound

from MaKaC.common import DBMgr
from MaKaC.webinterface.urlHandlers import UHConferenceDisplay
from MaKaC.webinterface.rh import categoryDisplay, conferenceDisplay, contribDisplay, CFADisplay, authorDisplay, \
    paperReviewingDisplay, collaboration, evaluationDisplay, registrantsDisplay, registrationFormDisplay, sessionDisplay
from indico.web.flask.util import rh_as_view
from indico.web.flask.wrappers import IndicoBlueprint


def _redirect_simple_event(**kwargs):
    # simple_event is confusing so we always use "lecture" in the URL
    return redirect(url_for('.conferenceCreation', event_type='lecture', **kwargs))


def _event_or_shorturl(confId, shorturl_namespace=False, ovw=False):
    from MaKaC.conference import ConferenceHolder
    from MaKaC.common.url import ShortURLMapper

    with DBMgr.getInstance().global_connection():
        ch = ConferenceHolder()
        su = ShortURLMapper()
        if ch.hasKey(confId):
            # https://github.com/mitsuhiko/werkzeug/issues/397
            # It only causes problems when someone tries to POST to an URL that is not supposed to accept POST
            # requests but getting a proper 405 error in that case is very nice. When the problem in werkzeug is
            # fixed this workaround can be removed and strict_slashes re-enabled for the /<path:confId>/ rule.
            no_trailing_slash = request.base_url[-1] != '/'
            if shorturl_namespace or (no_trailing_slash and not ovw):
                url = UHConferenceDisplay.getURL(ch.getById(confId))
                func = lambda: redirect(url, 301 if no_trailing_slash else 302)
            else:
                params = request.args.to_dict()
                params['confId'] = confId
                if ovw:
                    params['ovw'] = 'True'
                func = lambda: conferenceDisplay.RHConferenceDisplay(None).process(params)
        elif su.hasKey(confId):
            url = UHConferenceDisplay.getURL(su.getById(confId))
            func = lambda: redirect(url)
        else:
            if '/' in confId and not shorturl_namespace:
                # Most likely NOT an attempt to retrieve an event with an invalid short url
                raise NotFound()
            raise NotFound(
                _("The specified event with id or tag \"%s\" does not exist or has been deleted") % confId)

    return func()


event = IndicoBlueprint('event', __name__, url_prefix='/event')
event_shorturl = IndicoBlueprint('event_shorturl', __name__)


# Short URLs
event_shorturl.add_url_rule('/e/<path:confId>', view_func=_event_or_shorturl, strict_slashes=False,
                            defaults={'shorturl_namespace': True})


# conferenceCreation.py
event.add_url_rule('/create/simple_event', view_func=_redirect_simple_event)
event.add_url_rule('/create/simple_event/<categId>', view_func=_redirect_simple_event)
event.add_url_rule('/create/<any(lecture,meeting,conference):event_type>', 'conferenceCreation',
                   rh_as_view(categoryDisplay.RHConferenceCreation))
event.add_url_rule('/create/<any(lecture,meeting,conference):event_type>/<categId>', 'conferenceCreation',
                   rh_as_view(categoryDisplay.RHConferenceCreation))
event.add_url_rule('/create/save', 'conferenceCreation-createConference',
                   rh_as_view(categoryDisplay.RHConferencePerformCreation), methods=('POST',))


# conferenceDisplay.py
event.add_url_rule('/<path:confId>/', 'conferenceDisplay', _event_or_shorturl, strict_slashes=False)
event.add_url_rule('/<confId>/overview', 'conferenceDisplay-overview', _event_or_shorturl, defaults={'ovw': True})
event.add_url_rule('/<confId>/next', 'conferenceDisplay-next', rh_as_view(conferenceDisplay.RHRelativeEvent),
                   defaults={'which': 'next'})
event.add_url_rule('/<confId>/prev', 'conferenceDisplay-prev', rh_as_view(conferenceDisplay.RHRelativeEvent),
                   defaults={'which': 'prev'})
event.add_url_rule('/<confId>/accesskey', 'conferenceDisplay-accessKey',
                   rh_as_view(conferenceDisplay.RHConferenceAccessKey), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/abstract-book.pdf', 'conferenceDisplay-abstractBook',
                   rh_as_view(conferenceDisplay.RHAbstractBook))
event.add_url_rule('/<confId>/abstract-book-latex.zip', 'conferenceDisplay-abstractBookLatex',
                   rh_as_view(conferenceDisplay.RHConferenceLatexPackage))
event.add_url_rule('/<confId>/material/download', 'conferenceDisplay-matPkg',
                   rh_as_view(conferenceDisplay.RHFullMaterialPackage))
event.add_url_rule('/<confId>/material/download', 'conferenceDisplay-performMatPkg',
                   rh_as_view(conferenceDisplay.RHFullMaterialPackagePerform), methods=('POST',))
event.add_url_rule('/<confId>/style.css', 'conferenceDisplay-getCSS', rh_as_view(conferenceDisplay.RHConferenceGetCSS))
event.add_url_rule('/<confId>/logo', 'conferenceDisplay-getLogo',
                   rh_as_view(conferenceDisplay.RHConferenceGetLogo), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/picture/<picId>.<picExt>', 'conferenceDisplay-getPic',
                   rh_as_view(conferenceDisplay.RHConferenceGetPic))
event.add_url_rule('/<confId>/event.ics', 'conferenceDisplay-ical', rh_as_view(conferenceDisplay.RHConferenceToiCal))
event.add_url_rule('/<confId>/event.marc.xml', 'conferenceDisplay-marcxml',
                   rh_as_view(conferenceDisplay.RHConferenceToMarcXML))
event.add_url_rule('/<confId>/event.xml', 'conferenceDisplay-xml', rh_as_view(conferenceDisplay.RHConferenceToXML))

# conferenceProgram.py
event.add_url_rule('/<confId>/program', 'conferenceProgram', rh_as_view(conferenceDisplay.RHConferenceProgram))
event.add_url_rule('/<confId>/program.pdf', 'conferenceProgram-pdf',
                   rh_as_view(conferenceDisplay.RHConferenceProgramPDF))

# conferenceCFA.py
event.add_url_rule('/<confId>/call-for-abstracts/', 'conferenceCFA', rh_as_view(CFADisplay.RHConferenceCFA))

# userAbstracts.py
event.add_url_rule('/<confId>/call-for-abstracts/my-abstracts', 'userAbstracts', rh_as_view(CFADisplay.RHUserAbstracts))
event.add_url_rule('/<confId>/call-for-abstracts/my-abstracts.pdf', 'userAbstracts-pdf',
                   rh_as_view(CFADisplay.RHUserAbstractsPDF))

# abstractSubmission.py
event.add_url_rule('/<confId>/call-for-abstracts/submit', 'abstractSubmission',
                   rh_as_view(CFADisplay.RHAbstractSubmission), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/submitted', 'abstractSubmission-confirmation',
                   rh_as_view(CFADisplay.RHAbstractSubmissionConfirmation))

# abstractModify.py
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/modify', 'abstractModify',
                   rh_as_view(CFADisplay.RHAbstractModify), methods=('GET', 'POST'))

# abstractDisplay.py
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/', 'abstractDisplay',
                   rh_as_view(CFADisplay.RHAbstractDisplay))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/file/<resId>', 'abstractDisplay-getAttachedFile',
                   rh_as_view(CFADisplay.RHGetAttachedFile))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/Abstract.pdf', 'abstractDisplay-pdf',
                   rh_as_view(CFADisplay.RHAbstractDisplayPDF))

# abstractWithdraw.py
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/withdraw', 'abstractWithdraw',
                   rh_as_view(CFADisplay.RHAbstractWithdraw), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/recover', 'abstractWithdraw-recover',
                   rh_as_view(CFADisplay.RHAbstractRecovery), methods=('GET', 'POST'))

# conferenceTimeTable.py
event.add_url_rule('/<confId>/timetable/', 'conferenceTimeTable', rh_as_view(conferenceDisplay.RHConferenceTimeTable))
event.add_url_rule('/<confId>/timetable/pdf', 'conferenceTimeTable-customizePdf',
                   rh_as_view(conferenceDisplay.RHTimeTableCustomizePDF))
event.add_url_rule('/<confId>/timetable/timetable.pdf', 'conferenceTimeTable-pdf',
                   rh_as_view(conferenceDisplay.RHTimeTablePDF), methods=('GET', 'POST'))

# contributionListDisplay.py
event.add_url_rule('/<confId>/contributions', 'contributionListDisplay',
                   rh_as_view(conferenceDisplay.RHContributionList))
event.add_url_rule('/<confId>/contributions.pdf', 'contributionListDisplay-contributionsToPDF',
                   rh_as_view(conferenceDisplay.RHContributionListToPDF), methods=('POST',))

# contributionDisplay.py
event.add_url_rule('/<confId>/contribution/<contribId>', 'contributionDisplay',
                   rh_as_view(contribDisplay.RHContributionDisplay))
event.add_url_rule('/<confId>/contribution/<contribId>.ics', 'contributionDisplay-ical',
                   rh_as_view(contribDisplay.RHContributionToiCal))
event.add_url_rule('/<confId>/contribution/<contribId>.marc.xml', 'contributionDisplay-marcxml',
                   rh_as_view(contribDisplay.RHContributionToMarcXML))
event.add_url_rule('/<confId>/contribution/<contribId>.xml', 'contributionDisplay-xml',
                   rh_as_view(contribDisplay.RHContributionToXML))
event.add_url_rule('/<confId>/contribution/<contribId>.pdf', 'contributionDisplay-pdf',
                   rh_as_view(contribDisplay.RHContributionToPDF))

# contributionDisplay.py (within a session)
event.add_url_rule('/<confId>/session/<sessionId>/contribution/<contribId>', 'contributionDisplay',
                   rh_as_view(contribDisplay.RHContributionDisplay))
event.add_url_rule('/<confId>/session/<sessionId>/contribution/<contribId>.ics', 'contributionDisplay-ical',
                   rh_as_view(contribDisplay.RHContributionToiCal))
event.add_url_rule('/<confId>/session/<sessionId>/contribution/<contribId>.marc.xml', 'contributionDisplay-marcxml',
                   rh_as_view(contribDisplay.RHContributionToMarcXML))
event.add_url_rule('/<confId>/session/<sessionId>/contribution/<contribId>.xml', 'contributionDisplay-xml',
                   rh_as_view(contribDisplay.RHContributionToXML))
event.add_url_rule('/<confId>/session/<sessionId>/contribution/<contribId>.pdf', 'contributionDisplay-pdf',
                   rh_as_view(contribDisplay.RHContributionToPDF))

# sessionDisplay.py
event.add_url_rule('/<confId>/session/<sessionId>/', 'sessionDisplay', rh_as_view(sessionDisplay.RHSessionDisplay))
event.add_url_rule('/<confId>/session/<sessionId>/session.ics', 'sessionDisplay-ical',
                   rh_as_view(sessionDisplay.RHSessionToiCal))
event.add_url_rule('/<confId>/session/<showSessions>/timetable.pdf', 'conferenceTimeTable-pdf',
                   rh_as_view(conferenceDisplay.RHTimeTablePDF))


# confAuthorIndex.py
event.add_url_rule('/<confId>/authors', 'confAuthorIndex', rh_as_view(conferenceDisplay.RHAuthorIndex))

# contribAuthorDisplay.py
event.add_url_rule('/<confId>/contribution/<contribId>/author/<authorId>', 'contribAuthorDisplay',
                   rh_as_view(authorDisplay.RHAuthorDisplay))

# confSpeakerIndex.py
event.add_url_rule('/<confId>/speakers', 'confSpeakerIndex', rh_as_view(conferenceDisplay.RHSpeakerIndex))

# myconference.py
event.add_url_rule('/<confId>/my-conference/', 'myconference', rh_as_view(conferenceDisplay.RHMyStuff))
event.add_url_rule('/<confId>/my-conference/contributions', 'myconference-myContributions',
                   rh_as_view(conferenceDisplay.RHConfMyStuffMyContributions))
event.add_url_rule('/<confId>/my-conference/sessions', 'myconference-mySessions',
                   rh_as_view(conferenceDisplay.RHConfMyStuffMySessions))
event.add_url_rule('/<confId>/my-conference/tracks', 'myconference-myTracks',
                   rh_as_view(conferenceDisplay.RHConfMyStuffMyTracks))

# paperReviewingDisplay.py
event.add_url_rule('/<confId>/paper-reviewing/', 'paperReviewingDisplay',
                   rh_as_view(paperReviewingDisplay.RHPaperReviewingDisplay))
event.add_url_rule('/<confId>/paper-reviewing/templates/', 'paperReviewingDisplay-downloadTemplate',
                   rh_as_view(paperReviewingDisplay.RHDownloadPRTemplate))
event.add_url_rule('/<confId>/paper-reviewing/templates/<reviewingTemplateId>',
                   'paperReviewingDisplay-downloadTemplate', rh_as_view(paperReviewingDisplay.RHDownloadPRTemplate))
event.add_url_rule('/<confId>/paper-reviewing/upload', 'paperReviewingDisplay-uploadPaper',
                   rh_as_view(paperReviewingDisplay.RHUploadPaper))

# confAbstractBook.py
event.add_url_rule('/<confId>/abstract-book.pdf', 'confAbstractBook', rh_as_view(conferenceDisplay.RHAbstractBook))

# internalPage.py
event.add_url_rule('/<confId>/page/<pageId>', 'internalPage', rh_as_view(conferenceDisplay.RHInternalPageDisplay))

# collaborationDisplay.py
event.add_url_rule('/<confId>/collaboration', 'collaborationDisplay', rh_as_view(collaboration.RHCollaborationDisplay))

# confDisplayEvaluation.py
event.add_url_rule('/<confId>/evaluation/', 'confDisplayEvaluation',
                   rh_as_view(evaluationDisplay.RHEvaluationMainInformation))
event.add_url_rule('/<confId>/evaluation/evaluate', 'confDisplayEvaluation-display',
                   rh_as_view(evaluationDisplay.RHEvaluationDisplay))
event.add_url_rule('/<confId>/evaluation/evaluate', 'confDisplayEvaluation-modif',
                   rh_as_view(evaluationDisplay.RHEvaluationDisplay))
event.add_url_rule('/<confId>/evaluation/signin', 'confDisplayEvaluation-signIn',
                   rh_as_view(evaluationDisplay.RHEvaluationSignIn))
event.add_url_rule('/<confId>/evaluation/evaluate', 'confDisplayEvaluation-submit',
                   rh_as_view(evaluationDisplay.RHEvaluationSubmit), methods=('POST',))
event.add_url_rule('/<confId>/evaluation/evaluate/success', 'confDisplayEvaluation-submitted',
                   rh_as_view(evaluationDisplay.RHEvaluationSubmitted))

# confRegistrantsDisplay.py
event.add_url_rule('/<confId>/registration/registrants', 'confRegistrantsDisplay-list',
                   rh_as_view(registrantsDisplay.RHRegistrantsList))

# confRegistrationFormDisplay.py
event.add_url_rule('/<confId>/registration/', 'confRegistrationFormDisplay',
                   rh_as_view(registrationFormDisplay.RHRegistrationForm))
event.add_url_rule('/<confId>/registration/conditions', 'confRegistrationFormDisplay-conditions',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormConditions))
event.add_url_rule('/<confId>/registration/confirm', 'confRegistrationFormDisplay-confirmBooking',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormconfirmBooking), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/registration/pay', 'confRegistrationFormDisplay-confirmBookingDone',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormconfirmBookingDone))
event.add_url_rule('/<confId>/registration/register', 'confRegistrationFormDisplay-creation',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormCreation), methods=('POST',))
event.add_url_rule('/<confId>/registration/register/success', 'confRegistrationFormDisplay-creationDone',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormCreationDone))
event.add_url_rule('/<confId>/registration/register', 'confRegistrationFormDisplay-display',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormDisplay))
event.add_url_rule('/<confId>/registration/modify', 'confRegistrationFormDisplay-modify',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormModify))
event.add_url_rule('/<confId>/registration/modify', 'confRegistrationFormDisplay-performModify',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormPerformModify), methods=('POST',))
event.add_url_rule('/<confId>/registration/signin', 'confRegistrationFormDisplay-signIn',
                   rh_as_view(registrationFormDisplay.RHRegistrationFormSignIn))

# conferenceOtherViews.py
event.add_url_rule('/<confId>/other-view', 'conferenceOtherViews', rh_as_view(conferenceDisplay.RHConferenceOtherViews))

# EMail.py
event.add_url_rule('/<confId>/email', 'EMail', rh_as_view(conferenceDisplay.RHConferenceEmail), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/email/send', 'EMail-send', rh_as_view(conferenceDisplay.RHConferenceSendEmail),
                   methods=('POST',))

# confLogin.py
event.add_url_rule('/<confId>/user/login', 'confLogin', rh_as_view(conferenceDisplay.RHConfSignIn),
                   methods=('GET', 'POST'))
event.add_url_rule('/<confId>/user/login/disabled', 'confLogin-disabledAccount',
                   rh_as_view(conferenceDisplay.RHConfDisabledAccount), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/user/login/not-activated', 'confLogin-unactivatedAccount',
                   rh_as_view(conferenceDisplay.RHConfUnactivatedAccount))
event.add_url_rule('/<confId>/user/send-password', 'confLogin-sendLogin', rh_as_view(conferenceDisplay.RHConfSendLogin),
                   methods=('POST',))
event.add_url_rule('/<confId>/user/register/activate', 'confLogin-active', rh_as_view(conferenceDisplay.RHConfActivate))
event.add_url_rule('/<confId>/user/register/send-activation', 'confLogin-sendActivation',
                   rh_as_view(conferenceDisplay.RHConfSendActivation), methods=('GET', 'POST'))

# confUser.py
event.add_url_rule('/<confId>/user/register', 'confUser', rh_as_view(conferenceDisplay.RHConfUserCreation),
                   methods=('GET', 'POST'))
event.add_url_rule('/<confId>/user/register/success', 'confUser-created',
                   rh_as_view(conferenceDisplay.RHConfUserCreated))
event.add_url_rule('/<confId>/user/register/exists', 'confUser-userExists',
                   rh_as_view(conferenceDisplay.RHConfUserExistWithIdentity), methods=('GET', 'POST'))
