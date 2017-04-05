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

import shutil
from io import BytesIO

from flask import flash, request, session, render_template
from PIL import Image

from indico.core import signals
from indico.core.db import db
from indico.modules.events.layout import logger
from indico.modules.events.layout.forms import AddImagesForm
from indico.modules.events.layout.models.images import ImageFile
from indico.modules.events.layout.views import WPImages
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.web.util import jsonify_data
from indico.legacy.webinterface.rh.conferenceModif import RHConferenceModifBase
from indico.legacy.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _render_image_list(event):
    images = ImageFile.query.with_parent(event).all()
    return render_template('events/layout/image_list.html', images=images)


class RHManageImagesBase(RHConferenceModifBase):
    EVENT_FEATURE = 'images'
    CSRF_ENABLED = True


class RHImages(RHManageImagesBase):
    def _process(self):
        form = AddImagesForm()
        images = ImageFile.query.with_parent(self.event_new).all()
        return WPImages.render_template('images.html', self._conf, images=images, event=self.event_new, form=form)


class RHImageUpload(RHManageImagesBase):
    def _process(self):
        files = request.files.getlist('image')
        num = 0
        for f in files:
            filename = secure_filename(f.filename, 'image')
            data = BytesIO()
            shutil.copyfileobj(f, data)
            data.seek(0)
            try:
                image_type = Image.open(data).format.lower()
            except IOError:
                # Invalid image data
                continue
            data.seek(0)
            # XXX: mpo is basically JPEG and JPEGs from some cameras are (wrongfully) detected as mpo
            if image_type == 'mpo':
                image_type = 'jpeg'
            elif image_type not in {'jpeg', 'gif', 'png'}:
                flash(_("The image '{name}' has an invalid type ({type}); only JPG, GIF and PNG are allowed.")
                      .format(name=f.filename, type=image_type), 'error')
                continue
            content_type = 'image/' + image_type
            image = ImageFile(event_new=self.event_new, filename=filename, content_type=content_type)
            image.save(data)
            num += 1
            db.session.flush()
            logger.info('Image %s uploaded by %s', image, session.user)
            signals.event_management.image_created.send(image, user=session.user)
        flash(ngettext("The image has been uploaded", "{count} images have been uploaded", num)
              .format(count=len(files)), 'success')
        return jsonify_data(image_list=_render_image_list(self.event_new))


class RHImageDelete(RHManageImagesBase):
    def _checkParams(self, params):
        RHManageImagesBase._checkParams(self, params)
        self.image = (ImageFile.query.with_parent(self.event_new)
                      .filter_by(id=request.view_args['image_id'])
                      .first_or_404())

    def _process(self):
        signals.event_management.image_deleted.send(self.image, user=session.user)
        db.session.delete(self.image)
        flash(_("The image '{}' has been deleted").format(self.image.filename), 'success')
        return jsonify_data(image_list=_render_image_list(self.event_new))


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
