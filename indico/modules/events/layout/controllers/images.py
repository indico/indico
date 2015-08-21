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

import mimetypes

from flask import flash, redirect, request, session, render_template
from werkzeug.exceptions import NotFound

from indico.core import signals
from indico.core.db import db
from indico.modules.events.layout import logger
from indico.modules.events.layout.forms import AddImagesForm
from indico.modules.events.layout.models.images import ImageFile
from indico.modules.events.layout.models.legacy_mapping import LegacyImageMapping
from indico.modules.events.layout.util import get_images_for_event
from indico.modules.events.layout.views import WPImages
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _render_image_list(event):
    return render_template('events/layout/image_list.html', images=get_images_for_event(event))


class RHManageImagesBase(RHConferenceModifBase):
    EVENT_FEATURE = 'images'
    CSRF_ENABLED = True


class RHImages(RHManageImagesBase):
    def _process(self):
        form = AddImagesForm()
        return WPImages.render_template('images.html', self._conf, images=get_images_for_event(self._conf),
                                        event=self._conf, form=form)


class RHImageUpload(RHManageImagesBase):
    def _process(self):
        files = request.files.getlist('file')

        for f in files:
            filename = secure_filename(f.filename, 'image')
            content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
            image = ImageFile(event_id=self._conf.id, filename=filename, content_type=content_type)
            image.save(f.file)
            db.session.add(image)
            db.session.flush()
            logger.info('Image {} uploaded by {}'.format(image, session.user))
            signals.event_management.image_created.send(image, user=session.user)
        flash(ngettext("The image has been uploaded", "{count} images have been uploaded", len(files))
              .format(count=len(files)), 'success')
        return jsonify_data(image_list=_render_image_list(self._conf))


class RHImageDelete(RHManageImagesBase):
    def _checkParams(self, params):
        RHManageImagesBase._checkParams(self, params)
        self.image = ImageFile.find_first(id=request.view_args['image_id'], event_id=self._conf.getId())
        if not self.image:
            raise NotFound

    def _process(self):
        signals.event_management.image_deleted.send(self.image, user=session.user)
        db.session.delete(self.image)
        flash(_("The image '{}' has been deleted").format(self.image.filename), 'success')
        return jsonify_data(image_list=_render_image_list(self._conf))


class RHImageDisplay(RHConferenceBaseDisplay):
    EVENT_FEATURE = 'images'
    normalize_url_spec = {
        'locators': {
            lambda self: self.image
        }
    }

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        image_id = request.view_args['image_id']
        self.image = ImageFile.get_one(image_id)

    def _process(self):
        return self.image.send()


class RHImageLegacyDisplay(RHConferenceBaseDisplay):
    EVENT_FEATURE = 'images'

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.pic_id = request.view_args['pic_id']

    def _process(self):
        legacy_image = LegacyImageMapping.find_first(event_id=self._conf.id, legacy_image_id=self.pic_id)
        if legacy_image:
            return redirect(url_for('event_images.image_display', legacy_image.image), 301)
        else:
            raise NotFound
