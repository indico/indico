# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
