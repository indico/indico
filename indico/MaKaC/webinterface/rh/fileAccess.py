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

from copy import copy

from werkzeug.exceptions import NotFound

from MaKaC.webinterface.rh.conferenceBase import RHFileBase
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.errors import NotFoundError, AccessError
from MaKaC.registration import Registrant
from MaKaC.conference import Reviewing, LocalFile
from MaKaC.webinterface.rh.contribMod import RCContributionPaperReviewingStaff
from MaKaC.i18n import _

from indico.web.flask.util import send_file


class RHFileAccess(RHFileBase, RHDisplayBaseProtected):
    def _checkParams( self, params ):
        try:
            RHFileBase._checkParams( self, params )
        except:
            raise NotFoundError("The file you tried to access does not exist.")

    def _checkProtection( self ):
        if isinstance(self._file.getOwner(), Reviewing):
            selfcopy = copy(self)
            selfcopy._target = self._file.getOwner().getContribution()
            if not (RCContributionPaperReviewingStaff.hasRights(selfcopy) or \
                selfcopy._target.canUserSubmit(self.getAW().getUser()) or \
                self._target.canModify( self.getAW() )):
                raise AccessError()
        elif isinstance(self._file.getOwner(), Registrant) and \
             not self._file.getOwner().canUserModify(self.getAW().getUser()):
            raise AccessError(_("Access to this resource is forbidden."))

        else:
            # superseded by attachments
            raise NotFound

    def _process(self):
        assert isinstance(self._file, LocalFile)
        return send_file(self._file.getFileName(), self._file.getFilePath(), self._file.getFileType(),
                         self._file.getCreationDate())
