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

from flask import request

from indico.modules.events.abstracts.controllers.base import AbstractMixin
from indico.modules.events.abstracts.models.files import AbstractFile

from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHAbstractsReviewBase(AbstractMixin, RHConferenceBaseDisplay):
    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract
        }
    }

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        AbstractMixin._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        AbstractMixin._checkParams(self)


class RHAbstractsDownloadAttachment(RHAbstractsReviewBase):
    """Download an attachment file belonging to an abstract."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract_file
        }
    }

    def _checkParams(self, params):
        RHAbstractsReviewBase._checkParams(self, params)
        self.abstract_file = AbstractFile.get_one(request.view_args['file_id'])

    def _process(self):
        return self.abstract_file.send()
