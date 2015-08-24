# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import welcome, helpDisplay, newsDisplay, lang, resetTimezone, contact, errors
from indico.web.flask.wrappers import IndicoBlueprint
from indico.web.handlers import tracker


misc = IndicoBlueprint('misc', __name__)

misc.add_url_rule('/', 'index', welcome.RHWelcome)
misc.add_url_rule('/help', 'help', helpDisplay.RHHelp)
misc.add_url_rule('/news', 'news', newsDisplay.RHNews)
misc.add_url_rule('/change-language', 'changeLang', lang.RHChangeLang, methods=('POST',))
misc.add_url_rule('/change-timezone', 'resetSessionTZ', resetTimezone.RHResetTZ, methods=('GET', 'POST'))
misc.add_url_rule('/contact', 'contact', contact.RHContact)
misc.add_url_rule('/report-error', 'errors', errors.RHErrorReporting, methods=('GET', 'POST'))
misc.add_url_rule('/error-report/<report_id>/<filename>', 'error-report-download', errors.RHDownloadErrorReport)
misc.add_url_rule('/system-info', 'system-info', tracker.RHSystemInfo)
