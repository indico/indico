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

import re
from operator import itemgetter

from markupsafe import escape
from wtforms.fields import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError

from indico.core.db import db
from indico.modules.oauth.models.applications import SCOPES, OAuthApplication
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoSelectMultipleCheckboxField, TextListField
from indico.web.forms.widgets import SwitchWidget


class RedirectURIField(TextListField):
    _re = re.compile(r'^https?://(?P<host>[^/:]+)(?P<port>:[0-9]+)?(?P<path>/[^?]*)?$')

    def _validate_item(self, line):
        msg = _('Invalid URI: {}.<br>It must use http or https and may not contain a query string.')
        if not self._re.match(line):
            raise ValueError(msg.format(escape(line)))


class ApplicationForm(IndicoForm):
    name = StringField(_("Name"), [DataRequired()])
    description = TextAreaField(_("Description"))
    redirect_uris = RedirectURIField(_("Allowed authorization callback URLs"), [DataRequired()],
                                     description=_("More than one URL can be specified adding new lines. The "
                                                   "redirect_uri sent by the OAuth client must use the same protocol "
                                                   "and host/port. If an entry contains a path, the redirect_uri's "
                                                   "path must start with this path."))
    default_scopes = IndicoSelectMultipleCheckboxField('Allowed scopes', [DataRequired()],
                                                       choices=sorted(SCOPES.items(), key=itemgetter(1)))
    is_enabled = BooleanField(_("Enabled"), widget=SwitchWidget(),
                              description=_("If an application is not enabled, its OAuth tokens cannot be used and "
                                            "user cannot be prompted to authorize the application."))
    is_trusted = BooleanField(_("Trusted"), widget=SwitchWidget(),
                              description=_("Trusted applications will be granted authorization automatically and "
                                            "no intermediate page will be displayed during the authorization process."))

    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super(ApplicationForm, self).__init__(*args, **kwargs)
        if self.application is not None:
            for field in self.application.system_app_type.enforced_data:
                # preserve existing value for disabled fields
                self[field].data = self[field].object_data

    def validate_name(self, field):
        query = OAuthApplication.find(name=field.data)
        if self.application:
            query = query.filter(db.func.lower(OAuthApplication.name) != self.application.name.lower())
        if query.count():
            raise ValidationError(_("There is already an application with this name"))
