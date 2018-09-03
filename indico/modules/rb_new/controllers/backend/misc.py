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

from io import BytesIO

from flask import jsonify, redirect, request, session

from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb_new.controllers.backend.common import _cache
from indico.modules.rb_new.schemas import rb_user_schema
from indico.modules.rb_new.util import build_rooms_spritesheet
from indico.util.i18n import get_all_locales
from indico.web.flask.util import send_file, url_for


class RHConfig(RHRoomBookingBase):
    def _process(self):
        return jsonify(rooms_sprite_token=unicode(_cache.get('rooms-sprite-token', '')),
                       languages=get_all_locales(),
                       tileserver_url=rb_settings.get('tileserver_url'))


class RHUserInfo(RHRoomBookingBase):
    def _process(self):
        data = rb_user_schema.dump(session.user).data
        data['language'] = session.lang
        return jsonify(data)


class RHRoomsSprite(RHRoomBookingBase):
    def _process(self):
        sprite_mapping = _cache.get('rooms-sprite-mapping')
        if sprite_mapping is None:
            build_rooms_spritesheet()
        if 'version' not in request.view_args:
            return redirect(url_for('.sprite', version=_cache.get('rooms-sprite-token')))
        photo_data = _cache.get('rooms-sprite')
        return send_file('rooms-sprite.jpg', BytesIO(photo_data), 'image/jpeg', no_cache=False, cache_timeout=365*86400)
