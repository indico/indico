# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from markupsafe import Markup

from indico.util.i18n import _
from indico.util.placeholders import Placeholder
from indico.web.flask.util import url_for


class FirstNamePlaceholder(Placeholder):
    name = 'first_name'
    description = _("First name of the person")

    @classmethod
    def render(cls, invitation):
        return invitation.first_name


class LastNamePlaceholder(Placeholder):
    name = 'last_name'
    description = _("Last name of the person")

    @classmethod
    def render(cls, invitation):
        return invitation.last_name


class InvitationLinkPlaceholder(Placeholder):
    name = 'invitation_link'
    description = _("Link to accept/decline the invitation")
    required = True

    @classmethod
    def render(cls, invitation):
        url = url_for('.display_regform', invitation.locator.uuid, _external=True)
        return Markup('<a href="{0}">{0}</a>'.format(url))
