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

from MaKaC.webinterface.rh import conferenceDisplay, CFADisplay
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.display import event


# Call for abstracts
event.add_url_rule('/<confId>/call-for-abstracts/', 'conferenceCFA', rh_as_view(CFADisplay.RHConferenceCFA))
event.add_url_rule('/<confId>/call-for-abstracts/my-abstracts', 'userAbstracts', rh_as_view(CFADisplay.RHUserAbstracts))
event.add_url_rule('/<confId>/call-for-abstracts/my-abstracts.pdf', 'userAbstracts-pdf',
                   rh_as_view(CFADisplay.RHUserAbstractsPDF))

# Abstract submission
event.add_url_rule('/<confId>/call-for-abstracts/submit', 'abstractSubmission',
                   rh_as_view(CFADisplay.RHAbstractSubmission), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/submitted', 'abstractSubmission-confirmation',
                   rh_as_view(CFADisplay.RHAbstractSubmissionConfirmation))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/modify', 'abstractModify',
                   rh_as_view(CFADisplay.RHAbstractModify), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/withdraw', 'abstractWithdraw',
                   rh_as_view(CFADisplay.RHAbstractWithdraw), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/recover', 'abstractWithdraw-recover',
                   rh_as_view(CFADisplay.RHAbstractRecovery), methods=('GET', 'POST'))

# View abstract
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/', 'abstractDisplay',
                   rh_as_view(CFADisplay.RHAbstractDisplay))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/file/<resId>', 'abstractDisplay-getAttachedFile',
                   rh_as_view(CFADisplay.RHGetAttachedFile))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/Abstract.pdf', 'abstractDisplay-pdf',
                   rh_as_view(CFADisplay.RHAbstractDisplayPDF))

# Abstract book
event.add_url_rule('/<confId>/abstract-book.pdf', 'confAbstractBook', rh_as_view(conferenceDisplay.RHAbstractBook))
event.add_url_rule('/<confId>/abstract-book.pdf', 'conferenceDisplay-abstractBook',
                   rh_as_view(conferenceDisplay.RHAbstractBook))
event.add_url_rule('/<confId>/abstract-book-latex.zip', 'conferenceDisplay-abstractBookLatex',
                   rh_as_view(conferenceDisplay.RHConferenceLatexPackage))
