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
