# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# isort:skip_file

__all__ = ('HTTPAPIHook',)

from indico.web.http_api.hooks.base import HTTPAPIHook

# The following imports are NOT unused - without them these modules would never
# be imported and thus their api hooks wouldn't be registered at all
# They also need to stay below the other imports.
import indico.modules.attachments.api.hooks  # noqa: F401
import indico.modules.events.agreements.api  # noqa: F401
import indico.modules.events.api  # noqa: F401
import indico.modules.events.notes.api  # noqa: F401
import indico.modules.events.registration.api  # noqa: F401
import indico.modules.rb.api  # noqa: F401
import indico.modules.users.api  # noqa: F401
import indico.web.http_api.hooks.file  # noqa: F401
