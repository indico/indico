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

from wtforms.fields.core import BooleanField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import NumberRange

from indico.modules.api import APIMode
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoEnumSelectField
from indico.web.forms.widgets import SwitchWidget


security_mode_titles = {
    APIMode.KEY: _("Key for authenticated requests only"),
    APIMode.ONLYKEY: _("Key for all requests"),
    APIMode.SIGNED: _("Key+signature for authenticated requests only"),
    APIMode.ONLYKEY_SIGNED: _("Key for all requests. Signature for authenticated requests"),
    APIMode.ALL_SIGNED: _("Key+signature for all requests")
}


class AdminSettingsForm(IndicoForm):
    allow_persistent = BooleanField(_('Persistent signatures'), widget=SwitchWidget(),
                                    description=_("Allow users to enable persistent signatures (without timestamp)."))
    security_mode = IndicoEnumSelectField(_('Security mode'), enum=APIMode, titles=security_mode_titles,
                                          description=_('Specify if/when people need to use an API key or a '
                                                        'signed request.'))
    cache_ttl = IntegerField(_('Cache TTL'), [NumberRange(min=0)],
                             description=_('Time to cache API results (in seconds)'))
    signature_ttl = IntegerField(_('Signature TTL'), [NumberRange(min=1)],
                                 description=_('Time after which a request signature expires. This should not be too '
                                               'low to account for small clock differences between the client and the '
                                               'server.'))
