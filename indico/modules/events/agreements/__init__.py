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

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.agreements.base import AgreementPersonInfo, AgreementDefinitionBase, EmailPlaceholderBase
from indico.modules.events.agreements.util import get_agreement_definitions


__all__ = ('AgreementPersonInfo', 'AgreementDefinitionBase', 'EmailPlaceholderBase')

logger = Logger.get('agreements')


@signals.app_created.connect
def _check_agreement_definitions(app, **kwargs):
    # This will raise RuntimeError if the agreement definition types are not unique
    get_agreement_definitions()
