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

from indico.modules.events.abstracts.controllers.management import (RHAbstracts, RHManageBOA, RHAbstractList,
                                                                    RHAbstractListCustomize, RHAbstractListStaticURL,
                                                                    RHCreateAbstract)
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('abstracts', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/abstracts')

# Management
_bp.add_url_rule('/manage/abstracts/', 'manage_abstracts', RHAbstracts)
_bp.add_url_rule('/manage/abstracts/boa', 'manage_boa', RHManageBOA, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/list/', 'manage_abstract_list', RHAbstractList)
_bp.add_url_rule('/manage/abstracts/list/customize', 'customize_abstract_list', RHAbstractListCustomize,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/create', 'manage_create_abstract', RHCreateAbstract, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/abstracts/list/static-url', 'generate_static_url', RHAbstractListStaticURL, methods=('POST',))
