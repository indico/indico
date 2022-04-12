# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from operator import itemgetter

from markupsafe import escape
from wtforms.fields import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError

from indico.core.db import db
from indico.core.oauth.models.applications import OAuthApplication
from indico.core.oauth.models.personal_tokens import PersonalToken
from indico.core.oauth.scopes import SCOPES
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
    name = StringField(_('Name'), [DataRequired()])
    description = TextAreaField(_('Description'))
    redirect_uris = RedirectURIField(_('Allowed authorization callback URLs'), [DataRequired()],
                                     description=_('More than one URL can be specified adding new lines. The '
                                                   'redirect_uri sent by the OAuth client must use the same protocol '
                                                   "and host/port. If an entry contains a path, the redirect_uri's "
                                                   'path must start with this path.'))
    allowed_scopes = IndicoSelectMultipleCheckboxField('Allowed scopes', [DataRequired()],
                                                       choices=sorted(SCOPES.items(), key=itemgetter(1)),
                                                       description=_('Only scopes from this list may be requested by '
                                                                     'the app.'))
    is_enabled = BooleanField(_('Enabled'), widget=SwitchWidget(),
                              description=_('If an application is not enabled, its OAuth tokens cannot be used and '
                                            'user cannot be prompted to authorize the application.'))
    allow_pkce_flow = BooleanField(_('Allow PKCE flow'), widget=SwitchWidget(),
                                   description=_('If enabled, the application can use the client-side PKCE flow which '
                                                 'does not require the use of the Client Secret to get a token.'))
    is_trusted = BooleanField(_('Trusted'), widget=SwitchWidget(),
                              description=_('Trusted applications will be granted authorization automatically and '
                                            'no intermediate page will be displayed during the authorization process.'))

    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
        if self.application is not None:
            for field in self.application.system_app_type.enforced_data:
                # preserve existing value for disabled fields
                self[field].data = self[field].object_data

    def validate_name(self, field):
        query = OAuthApplication.query.filter(db.func.lower(OAuthApplication.name) == field.data.lower())
        if self.application:
            query = query.filter(OAuthApplication.id != self.application.id)
        if query.has_rows():
            raise ValidationError(_('There is already an application with this name'))


class PersonalTokenForm(IndicoForm):
    name = StringField(_('Name'), [DataRequired()], description=_("What's this token used for?"))
    scopes = IndicoSelectMultipleCheckboxField('Scopes', [DataRequired()],
                                               choices=sorted(SCOPES.items(), key=itemgetter(1)),
                                               description=_('Scopes define what kind of access the token has.'))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.token = kwargs.pop('token', None)
        super().__init__(*args, **kwargs)

    def validate_name(self, field):
        query = (
            self.user.query_personal_tokens()
            .filter(db.func.lower(PersonalToken.name) == field.data.lower())
        )
        if self.token:
            query = query.filter(PersonalToken.id != self.token.id)
        if query.has_rows():
            raise ValidationError(_('There is already a token with this name'))
