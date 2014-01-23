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

from MaKaC.webinterface.rh import welcome, helpDisplay, newsDisplay, payment, lang, resetTimezone, about, contact, \
    JSContent, errors, materialDisplay
from indico.web.flask.wrappers import IndicoBlueprint


misc = IndicoBlueprint('misc', __name__)

misc.add_url_rule('/', 'index', welcome.RHWelcome)
misc.add_url_rule('/help', 'help', helpDisplay.RHHelp)
misc.add_url_rule('/news', 'news', newsDisplay.RHNews)
misc.add_url_rule('/payment', 'payment', payment.RHPaymentModule, methods=('GET', 'POST'))
misc.add_url_rule('/change-language', 'changeLang', lang.RHChangeLang, methods=('GET', 'POST'))
misc.add_url_rule('/change-timezone', 'resetSessionTZ', resetTimezone.RHResetTZ, methods=('GET', 'POST'))
misc.add_url_rule('/about', 'about', about.RHAbout)
misc.add_url_rule('/contact', 'contact', contact.RHContact)
misc.add_url_rule('/vars.js', 'JSContent-getVars', JSContent.RHGetVarsJs)
misc.add_url_rule('/report-error', 'errors', errors.RHErrorReporting, methods=('GET', 'POST'))
misc.add_url_rule('/error-report/<report_id>/<filename>', 'error-report-download', errors.RHDownloadErrorReport)
misc.add_url_rule('/conversion-finished', 'getConvertedFile', materialDisplay.RHMaterialAddConvertedFile,
                  methods=('POST',))
