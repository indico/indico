# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from operator import itemgetter

from wtforms import BooleanField, StringField, FloatField, SelectField
from wtforms.validators import InputRequired

from indico.modules.designer import PageSize
from indico.modules.designer.util import get_inherited_templates
from indico.modules.events.sessions import COORDINATOR_PRIV_TITLES, COORDINATOR_PRIV_DESCS
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (AccessControlListField, IndicoProtectionField, PrincipalListField,
                                     IndicoPasswordField, IndicoEnumSelectField)
from indico.web.forms.widgets import SwitchWidget


class EventProtectionForm(IndicoForm):
    protection_mode = IndicoProtectionField(_('Protection mode'),
                                            protected_object=lambda form: form.protected_object,
                                            acl_message_url=lambda form: url_for('event_management.acl_message',
                                                                                 form.protected_object))
    acl = AccessControlListField(_('Access control list'), groups=True, allow_emails=True, allow_networks=True,
                                 allow_external=True, default_text=_('Restrict access to this event'),
                                 description=_('List of users allowed to access the event.'))
    access_key = IndicoPasswordField(_('Access key'), toggle=True,
                                     description=_('It is more secure to use only the ACL and not set an access key. '
                                                   '<strong>It will have no effect if the event is not '
                                                   'protected</strong>'))
    own_no_access_contact = StringField(_('No access contact'),
                                        description=_('Contact information shown when someone lacks access to the '
                                                      'event'))
    managers = PrincipalListField(_('Managers'), groups=True, allow_emails=True, allow_external=True,
                                  description=_('List of users allowed to modify the event'))
    submitters = PrincipalListField(_('Submitters'), allow_emails=True, allow_external=True,
                                    description=_('List of users with submission rights'))
    priv_fields = set()

    def __init__(self, *args, **kwargs):
        self.protected_object = kwargs.pop('event')
        super(EventProtectionForm, self).__init__(*args, **kwargs)

    @classmethod
    def _create_coordinator_priv_fields(cls):
        for name, title in sorted(COORDINATOR_PRIV_TITLES.iteritems(), key=itemgetter(1)):
            setattr(cls, name, BooleanField(title, widget=SwitchWidget(), description=COORDINATOR_PRIV_DESCS[name]))
            cls.priv_fields.add(name)


class PosterPrintingForm(IndicoForm):
    template = SelectField(_('Template'))
    margin_horizontal = FloatField(_('Horizontal margins'), [InputRequired()], default=0)
    margin_vertical = FloatField(_('Vertical margins'), [InputRequired()], default=0)
    page_size = IndicoEnumSelectField(_('Page size'), enum=PageSize, default=PageSize.A4)

    def __init__(self, event, **kwargs):
        all_templates = set(event.designer_templates) | get_inherited_templates(event)
        poster_templates = [tpl for tpl in all_templates if tpl.type.name == 'poster']
        super(PosterPrintingForm, self).__init__(**kwargs)
        self.template.choices = sorted(((unicode(tpl.id), tpl.title) for tpl in poster_templates), key=itemgetter(1))


EventProtectionForm._create_coordinator_priv_fields()
