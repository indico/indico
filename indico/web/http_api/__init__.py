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

# isort:skip_file

from indico.web.http_api.exceptions import LimitExceededException
from indico.web.http_api.hooks.base import DataFetcher, HTTPAPIHook
from indico.web.http_api.hooks.file import FileHook

# The following imports are NOT unused - without them these modules would never
# be imported and thus their api hooks wouldn't be registered at all
# They also need to stay below the other imports.
import indico.modules.attachments.api.hooks
import indico.modules.events.agreements.api
import indico.modules.events.api
import indico.modules.events.notes.api
import indico.modules.events.registration.api
import indico.modules.rb.api
import indico.modules.users.api
