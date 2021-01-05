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


class PersonNamePlaceholder(Placeholder):
    name = 'person_name'
    description = _("Name of the person")

    @classmethod
    def render(cls, definition, agreement):
        return agreement.person_name


class AgreementLinkPlaceholder(Placeholder):
    name = 'agreement_link'
    description = _("Link to the agreement page")
    required = True

    @classmethod
    def render(cls, definition, agreement):
        return Markup('<a href="{0}">{0}</a>'.format(url_for('agreements.agreement_form', agreement,
                                                             uuid=agreement.uuid, _external=True)))
