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

from __future__ import unicode_literals

from wtforms.fields.core import BooleanField, SelectField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import NumberRange

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget


# TODO: use enum
API_MODE_CHOICES = [
    (0, _("Key for authenticated requests only")),
    (1, _("Key for all requests")),
    (2, _("Key+signature for authenticated requests only")),
    (3, _("Key for all requests. Signature for authenticated requests")),
    (4, _("Key+signature for all requests"))
]


class AdminSettingsForm(IndicoForm):
    require_https = BooleanField(_('Require HTTPS'), widget=SwitchWidget(),
                                 description=_("Require HTTPS for all authenticated API requests."))
    allow_persistent = BooleanField(_('Persistent signatures'), widget=SwitchWidget(),
                                    description=_("Allow users to enable persistent signatures (without timestamp)."))
    security_mode = SelectField(_('Security mode'), choices=API_MODE_CHOICES, coerce=int,
                                description=_('Specify if/when people need to use an API key or a signed request.'))
    cache_ttl = IntegerField(_('Cache TTL'), [NumberRange(min=0)],
                             description=_('Time to cache API results (in seconds)'))
    signature_ttl = IntegerField(_('Signature TTL'), [NumberRange(min=1)],
                                 description=_('Time after which a request signature expires. This should not be too '
                                               'low to account for small clock differences between the client and the '
                                               'server.'))
