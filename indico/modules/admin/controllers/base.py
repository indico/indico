# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session
from werkzeug.exceptions import Forbidden

from indico.util.i18n import _
from indico.web.rh import RHProtected


class RHAdminBase(RHProtected):
    """Base class for all admin-only RHs."""

    DENY_FRAMES = True

    def _check_access(self):
        RHProtected._check_access(self)
        if not session.user.is_admin:
            raise Forbidden(_("Only Indico administrators may access this page."))
