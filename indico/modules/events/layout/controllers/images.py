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
from mimetypes import guess_type

from flask import flash, render_template, request, session
from PIL import Image
from pyPdf import PdfFileReader

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.layout import logger
from indico.modules.events.layout.forms import AddImagesForm
from indico.modules.events.layout.models.images import ImageFile
from indico.modules.events.layout.views import WPImages
from indico.modules.events.management.controllers import RHManageEventBase
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.web.util import jsonify_data


def _render_image_list(event):
    images = ImageFile.query.with_parent(event).all()
    return render_template('events/layout/image_list.html', images=images)


class RHManageImagesBase(RHManageEventBase):
    EVENT_FEATURE = 'images'


class RHImages(RHManageImagesBase):
    def _process(self):
        form = AddImagesForm()
        images = ImageFile.query.with_parent(self.event).all()
        return WPImages.render_template('images.html', self.event, images=images, form=form)


class RHImageUpload(RHManageImagesBase):
    def _process(self):
        files = request.files.getlist('image')
        num = 0
        for f in files:

            filename = secure_filename(f.filename, 'image')
            mtype = guess_type(filename)[0]
            if mtype not in config.ALLOWED_IMAGE_MIME_TYPES:
                continue
            data = BytesIO()
            shutil.copyfileobj(f, data)
            data.seek(0)
            if mtype == 'application/pdf':
                try:
                    _pdf = PdfFileReader(data)
                    image_type = 'pdf'
                    content_type = mtype
                except Exception:
                    continue
            else:
                try:
                    image_type = Image.open(data).format.lower()
                    # XXX: mpo is basically JPEG and JPEGs from some cameras are (wrongfully) detected as mpo
                    if image_type == 'mpo':
                       image_type = 'jpeg'
                       content_type = 'image/' + image_type
                except IOError:
                    # Invalid image data
                    continue
            data.seek(0)
            if image_type not in config.ALLOWED_IMAGE_TYPES:
                flash(_("The image '{name}' has an invalid type ({type})."  )
                      .format(name=f.filename, type=image_type), 'error')
                continue
            image = ImageFile(event=self.event, filename=filename, content_type=content_type)
            image.save(data)
            num += 1
            db.session.flush()
            logger.info('Image %s uploaded by %s', image, session.user)
            signals.event_management.image_created.send(image, user=session.user)
        flash(ngettext("The image has been uploaded", "{count} images have been uploaded", num)
              .format(count=len(files)), 'success')
        return jsonify_data(image_list=_render_image_list(self.event))


class RHImageDelete(RHManageImagesBase):
    def _process_args(self):
        RHManageImagesBase._process_args(self)
        self.image = (ImageFile.query.with_parent(self.event)
                      .filter_by(id=request.view_args['image_id'])
                      .first_or_404())

    def _process(self):
        signals.event_management.image_deleted.send(self.image, user=session.user)
        db.session.delete(self.image)
        flash(_("The image '{}' has been deleted").format(self.image.filename), 'success')
        return jsonify_data(image_list=_render_image_list(self.event))


class RHImageDisplay(RHDisplayEventBase):
    EVENT_FEATURE = 'images'
    normalize_url_spec = {
        'locators': {
            lambda self: self.image
        }
    }

    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        image_id = request.view_args['image_id']
        self.image = ImageFile.get_one(image_id)

    def _process(self):
        return self.image.send()
