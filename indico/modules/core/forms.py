# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from wtforms.fields import BooleanField, StringField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import IndicoRegexp
from indico.web.forms.widgets import SwitchWidget


class ReportErrorForm(IndicoForm):
    comment = TextAreaField(_('Details'), [DataRequired()], render_kw={'rows': 5},
                            description=_('Please let us know what you were doing when the error showed up.'))
    email = EmailField(_('Email address'),
                       description=_('If you enter your email address we can contact you to follow-up '
                                     'on your error report.'))


class SettingsForm(IndicoForm):
    # Core settings
    core_site_title = StringField(_('Title'), [DataRequired()], description=_("The global title of this Indico site."))
    core_site_organization = StringField(_('Organization'),
                                         description=_("The organization that runs this Indico site."))

    # Social settings
    social_enabled = BooleanField(_('Enabled'), widget=SwitchWidget())
    social_facebook_app_id = StringField('Facebook App ID', [IndicoRegexp(r'^\d*$')])

    @property
    def _fieldsets(self):
        return [
            (_('Site'), [x for x in self._fields if x.startswith('core_')]),
            (_('Social'), [x for x in self._fields if x.startswith('social_')]),
        ]
