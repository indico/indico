# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from indico.core import signals

from .logger import logger
from .oauth2 import require_oauth


__all__ = ['require_oauth']


@signals.app_created.connect
def _no_ssl_required_on_debug(app, **kwargs):
    if app.debug or app.testing:
        os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'


@signals.users.merged.connect
def _delete_merged_user_tokens(target, source, **kwargs):
    source.oauth_tokens.delete()
    logger.info('All tokens for the user %s were deleted.', source)
