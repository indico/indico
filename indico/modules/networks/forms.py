# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.core.db import db
from indico.modules.networks.fields import MultiIPNetworkField
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget


attachment_access_override_warning = _('Do you really want to grant everyone within the specified networks '
                                       'unauthenticated access to all attachments/materials in Indico?')


class IPNetworkGroupForm(IndicoForm):
    """Form to create or edit an IPNetworkGroup."""

    name = StringField(_("Name"), [DataRequired()])
    description = TextAreaField(_("Description"))
    networks = MultiIPNetworkField(_('Subnets'), description=_("IPv4 or IPv6 subnets in CIDR notation"))
    hidden = BooleanField(_('Hidden'), widget=SwitchWidget(),
                          description=_("Hidden IP networks cannot be added to ACLs by users"))
    attachment_access_override = BooleanField(_('Full attachment access'),
                                              widget=SwitchWidget(confirm_enable=attachment_access_override_warning),
                                              description=_("If enabled, these IPs have unrestricted access to all "
                                                            "attachments without having to be logged in."))

    def __init__(self, *args, **kwargs):
        self._network_group_id = kwargs['obj'].id if 'obj' in kwargs else None
        super(IPNetworkGroupForm, self).__init__(*args, **kwargs)

    def validate_name(self, field):
        query = IPNetworkGroup.find(db.func.lower(IPNetworkGroup.name) == field.data.lower())
        if self._network_group_id is not None:
            query = query.filter(IPNetworkGroup.id != self._network_group_id)
        if query.first():
            raise ValueError(_("An IP network with this name already exists."))
