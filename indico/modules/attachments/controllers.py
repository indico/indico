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

from flask import request
from indico.modules.attachments.views import WPEventAttachments
from indico.modules.attachments.forms import AddAttachmentsForm, AddLinkForm
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


def _random_date():
    from datetime import datetime
    import random
    year = random.randint(1950, 2000)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return datetime(year, month, day)


class RHEventAttachments(RHConferenceModifBase):
    """Shows the attachments of an event"""

    def _process(self):
        root_folders = [
            {'title': 'images', 'content-type': 'text/directory', 'modified_dt': _random_date(), 'content': [
                {'title': 'img001.jpg', 'content-type': 'image/jpeg', 'modified_dt': _random_date()},
                {'title': 'img002.jpg', 'content-type': 'image/jpeg', 'modified_dt': _random_date()},
                {'title': 'img003.jpg', 'content-type': 'image/jpeg', 'modified_dt': _random_date()},
                {'title': 'here_is_an_image_in_a_nested_folder_with_an_extremely_long_name_and_a_weird_extension.jpag',
                 'content-type': 'audio/vorbis', 'modified_dt': _random_date()}
            ]},
            {'title': 'some folder', 'content-type': 'text/directory', 'modified_dt': _random_date(), 'content': []},
            {'title': 'Poster', 'content-type': 'text/directory', 'modified_dt': _random_date(), 'content': [
                {'title': 'poster_final.pdf', 'content-type': 'application/pdf', 'modified_dt': _random_date()}
            ]},

        ]
        root_files = [
            {'title': 'data1.ods', 'content-type': 'application/vnd.oasis.opendocument.spreadsheet',
             'modified_dt': _random_date()},
            {'title': 'raw_data1.ods', 'content-type': 'application/vnd.oasis.opendocument.spreadsheet',
             'modified_dt': _random_date()},
            {'title': 'final_report.pdf', 'content-type': 'application/pdf', 'modified_dt': _random_date()},
            {'title': 'Some link', 'content-type': 'text/vnd.indico.link', 'modified_dt': _random_date()},
            {'title': 'unknown_type.ogg', 'content-type': 'audio/vorbis', 'modified_dt': _random_date()},
            {'title': 'this_is_a_completely_random_file_whose_name_is_long_extremely_extremely_extremely_long.ogg',
             'content-type': 'audio/vorbis', 'modified_dt': _random_date()}
        ]
        attachments = sorted(root_folders + root_files,
                             key=lambda a: (a['content-type'] != 'text/directory', a['title'].lower()))
        return WPEventAttachments.render_template('attachments.html', self._conf, event=self._conf,
                                                  attachments=attachments)


class RHEventAttachmentsUpload(RHConferenceModifBase):
    """Upload files"""

    def _process(self):
        form = AddAttachmentsForm()
        if request.method == 'POST':
            # TODO: Handle files
            return
        return WPEventAttachments.render_template('upload.html', self._conf, event=self._conf, form=form)


class RHEventAttachmentsAddLink(RHConferenceModifBase):
    """Attach link"""

    def _process(self):
        form = AddLinkForm()
        if form.validate_on_submit():
            # TODO
            return
        return WPEventAttachments.render_template('add_link.html', self._conf, event=self._conf, form=form)
