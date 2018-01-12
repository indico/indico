# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.core.settings.converters import DatetimeConverter, EnumConverter
from indico.modules.events.settings import EventSettingsProxy
from indico.util.i18n import _
from indico.util.struct.enum import RichEnum


class BOASortField(RichEnum):
    id = 'id'
    abstract_title = 'title'
    session_title = 'session_title'
    speaker = 'speaker'
    schedule = 'schedule'


class BOACorrespondingAuthorType(RichEnum):
    none = 'none'
    submitter = 'submitter'
    speakers = 'speakers'


BOASortField.__titles__ = {
    BOASortField.id: _('ID'),
    BOASortField.abstract_title: _('Abstract title'),
    BOASortField.session_title: _('Session title'),
    BOASortField.speaker: _('Presenter'),
    BOASortField.schedule: _('Schedule')
}


BOACorrespondingAuthorType.__titles__ = {
    BOACorrespondingAuthorType.none: _('None'),
    BOACorrespondingAuthorType.submitter: _('Submitter'),
    BOACorrespondingAuthorType.speakers: _('Speakers')
}


abstracts_settings = EventSettingsProxy('abstracts', {
    'description_settings': {
        'is_active': True,
        'is_required': True,
        'max_length': None,
        'max_words': None
    },
    'start_dt': None,
    'end_dt': None,
    'modification_end_dt': None,
    'announcement': '',
    'announcement_render_mode': RenderMode.markdown,
    'allow_multiple_tracks': True,
    'tracks_required': False,
    'allow_attachments': False,
    'allow_speakers': True,
    'speakers_required': True,
    'contrib_type_required': False,
    'submission_instructions': ''
}, acls={
    'authorized_submitters'
}, converters={
    'start_dt': DatetimeConverter,
    'end_dt': DatetimeConverter,
    'modification_end_dt': DatetimeConverter
})


abstracts_reviewing_settings = EventSettingsProxy('abstracts_reviewing', {
    'scale_lower': 0,
    'scale_upper': 5,
    'allow_comments': True,
    'allow_convener_judgment': False,  # whether track conveners can make a judgment (e.g. accept/reject)
    'allow_contributors_in_comments': False,
    'reviewing_instructions': '',
    'judgment_instructions': ''
})


boa_settings = EventSettingsProxy('abstracts_book', {
    'extra_text': '',
    'sort_by': BOASortField.id,
    'corresponding_author': BOACorrespondingAuthorType.submitter,
    'show_abstract_ids': False,
    'cache_path': None
}, converters={
    'sort_by': EnumConverter(BOASortField),
    'corresponding_author': EnumConverter(BOACorrespondingAuthorType),
    'announcement_render_mode': EnumConverter(RenderMode)
})
