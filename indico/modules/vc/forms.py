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
import re

from datetime import date
from datetime import timedelta
from operator import methodcaller, attrgetter

from flask_pluginengine import current_plugin
from wtforms.ext.dateutil.fields import DateField
from wtforms.fields.core import BooleanField, SelectField
from wtforms.fields.html5 import IntegerField
from wtforms.fields.simple import StringField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp, ValidationError

from indico.modules.vc.models import VCRoom, VCRoomStatus
from indico.modules.vc.util import full_block_id
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import PrincipalField, IndicoRadioField, EmailListField
from indico.web.forms.validators import UsedIf, Exclusive
from indico.web.forms.widgets import JinjaWidget, SwitchWidget, SelectizeWidget

ROOM_NAME_RE = re.compile(r'[\w\-]+')


class VCRoomField(HiddenField):
    widget = SelectizeWidget()

    def _convert_principal(self, principal):
        if principal['_type'] == 'Avatar':
            return u'Avatar', principal['id']
        else:
            return u'Group', principal['id']

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0].isdigit():
            self.data = VCRoom.get(valuelist[0])

    def _value(self):
        return self.data.id if self.data is not None else None


class LinkingWidget(JinjaWidget):
    """Renders a composite radio/select field"""

    def __init__(self, **context):
        super(LinkingWidget, self).__init__('forms/linking_widget.html', **context)

    def __call__(self, field, **kwargs):
        form = field._form
        has_error = {subfield.data: (subfield.data in form.conditional_fields and form[subfield.data].errors)
                     for subfield in field}
        return super(LinkingWidget, self).__call__(field, form=form, has_error=has_error, **kwargs)


class VCPluginSettingsFormBase(IndicoForm):
    managers = PrincipalField(_('Managers'), groups=True, description=_('Service managers'))
    acl = PrincipalField(_('ACL'), groups=True,
                         description=_('Users and Groups authorised to create videoconference rooms'))
    notification_emails = EmailListField(_('Notification email addresses'),
                                         description=_('Notifications about videoconference rooms are sent to '
                                                       'these email addresses (one per line).'))


class VCRoomLinkFormBase(IndicoForm):
    conditional_fields = {'contribution', 'block'}

    linking = IndicoRadioField(_("Link to"), [DataRequired()],
                               choices=[('event', _("Event")),
                                        ('contribution', _("Contribution")),
                                        ('block', _("Session"))],
                               widget=LinkingWidget())
    contribution = SelectField(_("Contribution"),
                               [UsedIf(lambda form, field: form.linking.data == 'contribution'), DataRequired()])
    block = SelectField(_("Session block"),
                        [UsedIf(lambda form, field: form.linking.data == 'block'), DataRequired()])

    show = BooleanField(_('Show room'),
                        widget=SwitchWidget(),
                        description=_('Display this room on the event page'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(VCRoomLinkFormBase, self).__init__(*args, **kwargs)
        contrib_choices = [(contrib.id, contrib.title) for contrib in
                           sorted(self.event.getContributionList(), key=attrgetter('title'))]
        block_choices = [(full_block_id(block), block.getFullTitle()) for block in
                         sorted(self.event.getSessionSlotList(), key=methodcaller('getFullTitle'))]
        self.contribution.choices = [('', _("Please select a contribution"))] + contrib_choices
        self.block.choices = [('', _("Please select a session block"))] + block_choices
        self.linking._form = self


class VCRoomAttachFormBase(VCRoomLinkFormBase):
    room = VCRoomField(
        _("Room to link"), [DataRequired()],
        description=_("Please start writing the name of the room you would like to attach. "
                      "Indico will suggest existing rooms."))

    def __init__(self, *args, **kwargs):
        super(VCRoomAttachFormBase, self).__init__(*args, **kwargs)
        self.room.search_url = url_for('.manage_vc_rooms_search', self.event, service=kwargs.pop('service'))


class VCRoomFormBase(VCRoomLinkFormBase):
    advanced_fields = {'show'}
    skip_fields = advanced_fields | VCRoomLinkFormBase.conditional_fields

    name = StringField(_('Name'), [DataRequired(), Length(min=3, max=60), Regexp(ROOM_NAME_RE)],
                       description=_('The name of the room. It can contain only alphanumerical characters, underscores '
                                     'and dashes. No spaces allowed.'))

    def validate_name(self, field):
        if field.data:
            room = VCRoom.find_first(VCRoom.name == field.data, VCRoom.status != VCRoomStatus.deleted,
                                     VCRoom.type == self.service_name)
            if room and room != self.vc_room:
                raise ValidationError(_("There is already a room with this name"))

    def __init__(self, *args, **kwargs):
        super(VCRoomFormBase, self).__init__(*args, **kwargs)
        self.vc_room = kwargs.pop('vc_room')
        self.service_name = current_plugin.service_name


class VCRoomListFilterForm(IndicoForm):
    direction = SelectField(_('Sort direction'), [DataRequired()],
                            choices=[('asc', _('Ascending')), ('desc', _('Descending'))])
    abs_start_date = DateField(_('Start Date'), [Optional(), Exclusive('rel_start_date')],
                               parse_kwargs={'dayfirst': True})
    abs_end_date = DateField(_('End Date'), [Optional(), Exclusive('rel_end_date')],
                             parse_kwargs={'dayfirst': True})
    rel_start_date = IntegerField(_('Days in the past'), [Optional(), Exclusive('abs_start_date'), NumberRange(min=0)],
                                  default=0)
    rel_end_date = IntegerField(_('Days in the future'), [Optional(), Exclusive('abs_end_date'), NumberRange(min=0)],
                                default=7)

    @generated_data
    def start_date(self):
        if self.abs_start_date.data is None and self.rel_start_date.data is None:
            return None
        return self.abs_start_date.data or (date.today() - timedelta(days=self.rel_start_date.data))

    @generated_data
    def end_date(self):
        if self.abs_end_date.data is None and self.rel_end_date.data is None:
            return None
        return self.abs_end_date.data or (date.today() + timedelta(days=self.rel_end_date.data))
