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

from indico.core.settings.converters import DatetimeConverter, EnumConverter
from indico.modules.events.settings import EventSettingsProxy
from indico.util.i18n import _
from indico.util.struct.enum import TitledEnum

abstracts_settings = EventSettingsProxy('abstracts', {
    'description_settings': {
        'is_active': True,
        'is_required': True,
        'max_length': None,
        'max_words': None
    },
    'start_dt': None,
    'end_dt': None,
    'modification_end_dt': None
}, converters={
    'start_dt': DatetimeConverter,
    'end_dt': DatetimeConverter,
    'modification_end_dt': DatetimeConverter
})


class BOASortField(TitledEnum):
    id = 'id'
    title = 'title'
    session_title = 'session_title'
    speaker = 'speaker'
    schedule = 'schedule'

    __titles__ = {
        id: _('ID'),
        title: _('Title'),
        session_title: _('Session title'),
        speaker: _('Presenter'),
        schedule: _('Schedule')
    }


class BOACorrespondingAuthorType(TitledEnum):
    none = 'none'
    submitter = 'submitter'
    speakers = 'speakers'

    __titles__ = {
        none: _('None'),
        submitter: _('Submitter'),
        speakers: _('Speakers')
    }


boa_settings = EventSettingsProxy('abstracts_book', {
    'extra_text': '',
    'sort_by': BOASortField.id,
    'corresponding_author': BOACorrespondingAuthorType.submitter,
    'show_abstract_ids': False
}, converters={
    'sort_by': EnumConverter(BOASortField),
    'corresponding_author': EnumConverter(BOACorrespondingAuthorType)
})
