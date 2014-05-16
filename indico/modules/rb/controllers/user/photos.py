# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.


import posixpath
from io import BytesIO
from flask import request

from indico.core.config import Config
from indico.web.flask.util import send_file
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.photos import Photo


class RHRoomPhoto(RHRoomBookingBase):
    def _checkParams(self):
        self._size = request.view_args['size']
        self._photo = Photo.find_first(Room.id == request.view_args['roomID'], _join=Photo.room)

    def _process(self):
        if self._photo is None:
            self._redirect(posixpath.join(Config.getInstance().getImagesBaseURL(),
                                          'rooms/{}_photos/NoPhoto.jpg'.format(self._size)))
            return
        io = BytesIO(getattr(self._photo, '{}_content'.format(self._size)))
        return send_file('photo-{}.jpg'.format(self._size), io, 'image/jpeg', no_cache=False)
