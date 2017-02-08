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

from wtforms import BooleanField, StringField, TextAreaField, DateField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Optional, DataRequired

from indico.modules.categories.util import get_visibility_options
from indico.modules.events.fields import EventPersonLinkListField
from indico.modules.events.models.events import EventType
from indico.modules.events.sessions import COORDINATOR_PRIV_TITLES, COORDINATOR_PRIV_DESCS
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (AccessControlListField, IndicoProtectionField, PrincipalListField,
                                     IndicoPasswordField)
from indico.web.forms.fields import IndicoDateTimeField
from indico.web.forms.fields import IndicoEnumSelectField
from indico.web.forms.fields import IndicoLocationField
from indico.web.forms.fields import IndicoRadioField
from indico.web.forms.fields import IndicoTagListField
from indico.web.forms.fields import IndicoTimezoneSelectField
from indico.web.forms.validators import HiddenUnless
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


EventProtectionForm._create_coordinator_priv_fields()


class SupportInfoForm(IndicoForm):
    support_caption = StringField(_("Support Caption"))
    support_email = EmailField(_("Support Email"))
    support_phone = StringField(_("Support Telephone"))
    contact_info = TextAreaField(_("Additional info"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(SupportInfoForm, self).__init__(*args, **kwargs)
        support = self.event.as_legacy.getSupportInfo()
        self.support_caption.data = support.getCaption()
        self.support_email.data = support.getEmail()
        self.support_phone.data = support.getTelephone()
        self.contact_info.data = self.event.as_legacy.getContactInfo()
        print self.event.as_legacy.getOrgText()


def __init__(self, *args, **kwargs):
    self.event = kwargs.pop('event')
    super(GeneralSettingsForm, self).__init__(*args, **kwargs)
    self.visibility.choices = get_visibility_options(self.event)


class BasicSettingsForm(IndicoForm):
    title = StringField(_("Title"))
    description = TextAreaField(_("Description"))


class GeneralSettingsForm(IndicoForm):
    # _fieldsets = [(_('Screen dates'), ['screen_start_dt', 'screen_end_dt'])]

    title = StringField(_("Title"))
    description = TextAreaField(_("Description"))
    location_data = IndicoLocationField(_('Location'), allow_location_inheritance=False)
    timezone = IndicoTimezoneSelectField(_('Timezone'))
    start_dt = IndicoDateTimeField(_('Start Date'), allow_clear=False)
    end_dt = IndicoDateTimeField(_('End Date'), allow_clear=False)

    # if conference

    # endif

    # if lecture
    # organizers
    # endif

    # default_style = SelectField(_('Default Style'), choices=[
    #     ('submit', _('Submit')),
    #     ('accept', _('Accept'))
    # ])
    visibility = SelectField(_('Visibility'), [Optional()], coerce=lambda x: None if x == '' else int(x))
    type_ = IndicoEnumSelectField(_('Event type'), enum=EventType)
    keywords = IndicoTagListField(_('Keywords'))
    url_shortcut = StringField(_("Short display URL"),  filters=[lambda x: (x or None)])

    # if conference
    person_link_data = EventPersonLinkListField(_('Chairpersons'))
    different_start = BooleanField(_('Different screen start date'), [Optional()], widget=SwitchWidget(), default=False,
                                   description=_('Screen dates are the dates which will appear on the display page of your'
                                              ' event. You can define screen dates which are different from the '
                                              'timetable ones, for eg. if your conference officially starts on a day, '
                                              'but also includes a registration session the day before.'))
    screen_start_dt = IndicoDateTimeField(_('Screen start Date'), [HiddenUnless('different_start')])
    different_end = BooleanField(_('Different screen end date'), widget=SwitchWidget(), default=False)
    screen_end_dt = IndicoDateTimeField(_('Screen end Date'), [HiddenUnless('different_end')])
    # endif


    # if lecture
    # speakers = EventPersonLinkListField(_('Speakers'))
    # endif

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(GeneralSettingsForm, self).__init__(*args, **kwargs)
        self.visibility.choices = get_visibility_options(self.event)


    # visibility = SelectField(_('Visibility'))
    # event_type = SelectField(_('Event type'))
    # short_url = StringField(_("Short display URL"))
    # protection_mode = IndicoProtectionField(_('Protection mode'),
    #                                         protected_object=lambda form: form.protected_object,
    #                                         acl_message_url=lambda form: url_for('event_management.acl_message',
    #                                                                              form.protected_object))
    # acl = AccessControlListField(_('Access control list'), groups=True, allow_emails=True, allow_networks=True,
    #                              allow_external=True, default_text=_('Restrict access to this event'),
    #                              description=_('List of users allowed to access the event.'))
    # access_key = IndicoPasswordField(_('Access key'), toggle=True,
    #                                  description=_('It is more secure to use only the ACL and not set an access key. '
    #                                                '<strong>It will have no effect if the event is not '
    #                                                'protected</strong>'))
    # own_no_access_contact = StringField(_('No access contact'),
    #                                     description=_('Contact information shown when someone lacks access to the '
    #                                                   'event'))
    # managers = PrincipalListField(_('Managers'), groups=True, allow_emails=True, allow_external=True,
    #                               description=_('List of users allowed to modify the event'))
    # submitters = PrincipalListField(_('Submitters'), allow_emails=True, allow_external=True,
    #                                 description=_('List of users with submission rights'))
