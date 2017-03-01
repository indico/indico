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

import posixpath
from io import BytesIO
from flask import redirect

from indico.core.config import Config
from indico.web.flask.util import send_file
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.photos import Photo
from indico.legacy.common.cache import GenericCache


_cache = GenericCache('Rooms')


def _redirect_no_photo(size):
    return redirect(posixpath.join(Config.getInstance().getImagesBaseURL(), 'rooms/{}_photos/NoPhoto.jpg'.format(size)))


def room_photo(roomID, size, **kw):
    cache_key = 'photo-{}-{}'.format(roomID, size)
    photo_data = _cache.get(cache_key)

    if photo_data == '*':
        return _redirect_no_photo(size)
    elif photo_data is None:
        photo = Photo.find_first(Room.id == roomID, _join=Photo.room)
        if photo is None:
            _cache.set(cache_key, '*')
            return _redirect_no_photo(size)
        photo_data = photo.thumbnail if size == 'small' else photo.data
        _cache.set(cache_key, photo_data)

    io = BytesIO(photo_data)
    return send_file('photo-{}.jpg'.format(size), io, 'image/jpeg', no_cache=False)
