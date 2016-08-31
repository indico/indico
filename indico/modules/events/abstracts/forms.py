# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from wtforms.fields import BooleanField, IntegerField
from wtforms.validators import NumberRange, Optional, DataRequired

from indico.modules.events.abstracts.settings import BOASortField, BOACorrespondingAuthorType
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoEnumSelectField, IndicoMarkdownField
from indico.web.forms.widgets import SwitchWidget


class AbstractContentSettingsForm(IndicoForm):
    """Configure the content field of abstracts"""

    is_active = BooleanField(_('Active'), widget=SwitchWidget(),
                             description=_("Whether the content field is available."))
    is_required = BooleanField(_('Required'), widget=SwitchWidget(),
                               description=_("Whether the user has to fill the content field."))
    max_length = IntegerField(_('Max length'), [Optional(), NumberRange(min=1)])
    max_words = IntegerField(_('Max words'), [Optional(), NumberRange(min=1)])


class BOASettingsForm(IndicoForm):
    """Settings form for the 'Book of Abstracts'"""

    extra_text = IndicoMarkdownField(_('Additional text'), editor=True, mathjax=True)
    sort_by = IndicoEnumSelectField(_('Sort by'), [DataRequired()], enum=BOASortField, sorted=True)
    corresponding_author = IndicoEnumSelectField(_('Corresponding author'), [DataRequired()],
                                                 enum=BOACorrespondingAuthorType, sorted=True)
    show_abstract_ids = BooleanField(_('Show abstract IDs'), widget=SwitchWidget(),
                                     description=_("Show abstract IDs in the table of contents."))
