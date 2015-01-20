# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

import MaKaC.plugins.Collaboration.handlers as handlers
from MaKaC.plugins.Collaboration.urlHandlers import RHCollaborationHtdocs
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint


blueprint = IndicoBlueprint('collaboration', __name__)

# Speaker Agreement
blueprint.add_url_rule('/event/<confId>/manage/collaboration/elecAgree/', 'elecAgree',
                       handlers.RHElectronicAgreement)
blueprint.add_url_rule('/event/<confId>/manage/collaboration/elecAgree/upload', 'uploadElecAgree',
                       handlers.RHUploadElectronicAgreement, methods=('POST',))
blueprint.add_url_rule('/event/<confId>/manage/collaboration/elecAgree/download/<spkId>', 'getPaperAgree',
                       handlers.RHElectronicAgreementGetFile)
blueprint.add_url_rule('/event/<confId>/collaboration/agreement', 'elecAgreeForm',
                       handlers.RHElectronicAgreementForm)

# Manage event
blueprint.add_url_rule('/event/<confId>/manage/collaboration/', 'confModifCollaboration',
                       handlers.RHConfModifCSBookings, methods=('GET', 'POST'))
blueprint.add_url_rule('/event/<confId>/manage/collaboration/<tab>/', 'confModifCollaboration',
                       handlers.RHConfModifCSBookings, methods=('GET', 'POST'))
blueprint.add_url_rule('/event/<confId>/manage/collaboration/managers', 'confModifCollaboration-managers',
                       handlers.RHConfModifCSProtection)

# Display event
blueprint.add_url_rule('/event/<confId>/collaboration', 'collaborationDisplay',
                       handlers.RHCollaborationDisplay)

# Collaboration admin
blueprint.add_url_rule('/admin/collaboration', 'adminCollaboration', handlers.RHAdminCollaboration)

# htdocs
blueprint.add_url_rule('/Collaboration/<plugin>/<path:filepath>', 'htdocs', RHCollaborationHtdocs)
blueprint.add_url_rule('/Collaboration/<path:filepath>', 'htdocs', RHCollaborationHtdocs)

# we can't use make_compat_blueprint here because the old url doesn't end in .py
compat = IndicoBlueprint('compat_collaboration', __name__)
compat.add_url_rule('/collaborationDisplay.py', 'collaborationDisplay',
                    make_compat_redirect_func(blueprint, 'collaborationDisplay'))
compat.add_url_rule('/Collaboration/elecAgree', 'elecAgree',
                    make_compat_redirect_func(blueprint, 'elecAgree'))
compat.add_url_rule('/Collaboration/elecAgreeForm', 'elecAgreeForm',
                    make_compat_redirect_func(blueprint, 'elecAgreeForm'))
