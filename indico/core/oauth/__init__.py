# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from indico.core import signals
from indico.core.db import db

from .logger import logger
from .oauth2 import require_oauth


__all__ = ['require_oauth']


@signals.core.app_created.connect
def _no_ssl_required_on_debug(app, **kwargs):
    if app.debug or app.testing:
        os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'


@signals.users.merged.connect
def _delete_merged_user_tokens(target, source, **kwargs):
    target_app_links = {link.application: link for link in target.oauth_app_links}
    for source_link in source.oauth_app_links.all():
        try:
            target_link = target_app_links[source_link.application]
        except KeyError:
            logger.info('merge: reassigning %r to %r', source_link, target)
            source_link.user = target
        else:
            logger.info('merge: merging %r into %r', source_link, target_link)
            target_link.update_scopes(set(source_link.scopes))
            target_link.tokens.extend(source_link.tokens)
            db.session.delete(source_link)
