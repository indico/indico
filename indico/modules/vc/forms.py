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

from wtforms.fields.core import BooleanField, SelectField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError

from indico.modules.vc.models import VCRoom
from indico.modules.vc.util import full_block_id
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import PrincipalField, IndicoRadioField
from indico.web.forms.validators import UsedIf
from indico.web.forms.widgets import JinjaWidget, SwitchWidget

ROOM_NAME_RE = re.compile(r'[\w\-]+')


class LinkingWidget(JinjaWidget):
    """Renders a composite radio/select field"""

    def __init__(self, **context):
        super(LinkingWidget, self).__init__('linking_widget.html', plugin='vc_vidyo', **context)

    def __call__(self, field, **kwargs):
        form = field._form
        has_error = {subfield.data: (subfield.data in form.conditional_fields and form[subfield.data].errors)
                     for subfield in field}
        return super(LinkingWidget, self).__call__(field, form=form, has_error=has_error, **kwargs)


class VCPluginSettingsFormBase(IndicoForm):
    managers = PrincipalField(_('Managers'), description=_('Service managers'))
    acl = PrincipalField(_('ACL'), groups=True,
                         description=_('Users and Groups authorised to create video conference rooms'))
    notify_managers = BooleanField(_('Notify managers'),
                                   description=_('Send email notifications to managers'))


class VCRoomFormBase(IndicoForm):
    advanced_fields = {'show'}
    conditional_fields = {'contribution', 'block'}

    name = StringField(_('Name'), [DataRequired(), Length(min=3, max=60), Regexp(ROOM_NAME_RE)],
                       description=_('The name of the room'))
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
        self.vc_room = kwargs.pop('vc_room')
        self.event = kwargs.pop('event')
        super(VCRoomFormBase, self).__init__(*args, **kwargs)
        self.contribution.choices = ([('', _("Please select a contribution"))] +
                                     [(contrib.id, contrib.title) for contrib in self.event.getContributionList()])
        self.block.choices = (
            [('', _("Please select a session block"))] +
            [(full_block_id(block), block.getFullTitle()) for block in self.event.getSessionSlotList()])
        self.linking._form = self

    def validate_name(self, field):
        if field.data:
            room = VCRoom.find_first(name=field.data)

            if room and room != self.vc_room:
                raise ValidationError(_("There is already a room with this name"))
