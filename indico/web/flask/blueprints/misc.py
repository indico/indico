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

from flask import Blueprint

from MaKaC.webinterface.rh import welcome, helpDisplay, newsDisplay, payment, lang, resetTimezone, about, contact, \
    JSContent, errors, materialDisplay
from indico.web.flask.util import rh_as_view


misc = Blueprint('misc', __name__)

misc.add_url_rule('/', 'index', rh_as_view(welcome.RHWelcome))
misc.add_url_rule('/help', 'help', rh_as_view(helpDisplay.RHHelp))
misc.add_url_rule('/news', 'news', rh_as_view(newsDisplay.RHNews))
misc.add_url_rule('/payment', 'payment', rh_as_view(payment.RHPaymentModule), methods=('GET', 'POST'))
misc.add_url_rule('/change-language', 'changeLang', rh_as_view(lang.RHChangeLang), methods=('GET', 'POST'))
misc.add_url_rule('/change-timezone', 'resetSessionTZ', rh_as_view(resetTimezone.RHResetTZ), methods=('GET', 'POST'))
misc.add_url_rule('/about', 'about', rh_as_view(about.RHAbout))
misc.add_url_rule('/contact', 'contact', rh_as_view(contact.RHContact))
misc.add_url_rule('/vars.js', 'JSContent-getVars', rh_as_view(JSContent.RHGetVarsJs))
misc.add_url_rule('/report-error', 'errors', rh_as_view(errors.RHErrorReporting), methods=('GET', 'POST'))
misc.add_url_rule('/conversion-finished', 'getConvertedFile', rh_as_view(materialDisplay.RHMaterialAddConvertedFile),
                  methods=('POST',))
