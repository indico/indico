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

from MaKaC.webinterface.rh import conferenceDisplay, CFADisplay
from indico.web.flask.blueprints.event.display import event


# Call for abstracts
event.add_url_rule('/call-for-abstracts/', 'conferenceCFA', CFADisplay.RHConferenceCFA)
event.add_url_rule('/call-for-abstracts/my-abstracts', 'userAbstracts', CFADisplay.RHUserAbstracts)
event.add_url_rule('/call-for-abstracts/my-abstracts.pdf', 'userAbstracts-pdf', CFADisplay.RHUserAbstractsPDF)

# Abstract submission
event.add_url_rule('/call-for-abstracts/submit', 'abstractSubmission', CFADisplay.RHAbstractSubmission,
                   methods=('GET', 'POST'))
event.add_url_rule('/call-for-abstracts/<abstractId>/submitted', 'abstractSubmission-confirmation',
                   CFADisplay.RHAbstractSubmissionConfirmation)
event.add_url_rule('/call-for-abstracts/<abstractId>/modify', 'abstractModify', CFADisplay.RHAbstractModify,
                   methods=('GET', 'POST'))
event.add_url_rule('/call-for-abstracts/<abstractId>/withdraw', 'abstractWithdraw', CFADisplay.RHAbstractWithdraw,
                   methods=('GET', 'POST'))
event.add_url_rule('/call-for-abstracts/<abstractId>/recover', 'abstractWithdraw-recover',
                   CFADisplay.RHAbstractRecovery, methods=('GET', 'POST'))

# View abstract
event.add_url_rule('/call-for-abstracts/<abstractId>/', 'abstractDisplay', CFADisplay.RHAbstractDisplay)
event.add_url_rule('/call-for-abstracts/<abstractId>/file/<resId>.<fileExt>', 'abstractDisplay-getAttachedFile',
                   CFADisplay.RHGetAttachedFile)
event.add_url_rule('/call-for-abstracts/<abstractId>/file/<resId>', 'abstractDisplay-getAttachedFile',
                   CFADisplay.RHGetAttachedFile)
event.add_url_rule('/call-for-abstracts/<abstractId>/Abstract.pdf', 'abstractDisplay-pdf',
                   CFADisplay.RHAbstractDisplayPDF)

# Abstract book
event.add_url_rule('/abstract-book.pdf', 'confAbstractBook', conferenceDisplay.RHAbstractBook)
event.add_url_rule('/abstract-book.pdf', 'conferenceDisplay-abstractBook', conferenceDisplay.RHAbstractBook)
event.add_url_rule('/abstract-book-latex.zip', 'conferenceDisplay-abstractBookLatex',
                   conferenceDisplay.RHConferenceLatexPackage)
