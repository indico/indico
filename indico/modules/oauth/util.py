# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.modules.users import user_management_settings


def can_manage_personal_tokens():
    """Check whether the current user can manage personal tokens."""
    return session.user.is_admin or user_management_settings.get('allow_personal_tokens')
