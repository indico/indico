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

from indico.core.db import db
from indico.core.logger import Logger
from indico.modules.events.layout.util import get_images_for_event
from indico.modules.events.features.util import is_feature_enabled
from indico.util.i18n import _

from MaKaC.conference import EventCloner


logger = Logger.get('events.images')


class ImageCloner(EventCloner):
    def _find_images(self):
        from indico.modules.events.layout.models.images import ImageFile
        return ImageFile.find(event_id=self.event.id)

    def get_options(self):
        if is_feature_enabled(self.event, 'images'):
            enabled = bool(self._find_images().count())
            return {'images': (_("Images"), enabled, False)}
        else:
            return {}

    def clone(self, new_event, options):
        from indico.modules.events.layout.models.images import ImageFile
        if 'images' not in options:
            return
        for old_image in get_images_for_event(self.event):
            new_image = ImageFile(event_id=new_event.id,
                                  filename=old_image.filename,
                                  content_type=old_image.content_type)
            with old_image.open() as fd:
                new_image.save(fd)
            db.session.add(new_image)
            db.session.flush()
            logger.info('Added image during event cloning: {}'.format(new_image))
