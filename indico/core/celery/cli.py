# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import sys

import click
from celery.bin.celery import celery as celery_cmd

from indico.core.celery.util import unlock_task
from indico.core.config import config
from indico.core.oauth.models.applications import OAuthApplication, SystemAppType
from indico.util.console import cformat
from indico.web.flask.util import url_for


# remove the celery shell command
del celery_cmd.commands['shell']


# XXX: flower is broken with celery 5, just keeping this here in case they fix it
@celery_cmd.command(context_settings={'ignore_unknown_options': True})
@click.argument('flower_args', nargs=-1, type=click.UNPROCESSED)
def flower(flower_args):
    # Somehow flower hangs when executing it using CeleryCommand() so we simply exec it directly.
    # It doesn't really need the celery config anyway (besides the broker url)
    try:
        import flower  # noqa: F401
    except ImportError:
        print(cformat('%{red!}Flower is not installed'))
        sys.exit(1)

    app = OAuthApplication.query.filter_by(system_app_type=SystemAppType.flower).one()
    if not app.redirect_uris:
        print(cformat('%{yellow!}Authentication will fail unless you configure the redirect url for the {} OAuth '
                      'application in the administration area.').format(app.name))

    print(cformat('%{green!}Only Indico admins will have access to flower.'))
    print(cformat('%{yellow}Note that revoking admin privileges will not revoke Flower access.'))
    print(cformat('%{yellow}To force re-authentication, restart Flower.'))
    auth_args = ('--auth=^Indico Admin$', '--auth_provider=indico.core.celery.flower.FlowerAuthHandler')
    auth_env = {
        'INDICO_FLOWER_CLIENT_ID': app.client_id,
        'INDICO_FLOWER_CLIENT_SECRET': app.client_secret,
        'INDICO_FLOWER_AUTHORIZE_URL': url_for('oauth.oauth_authorize', _external=True),
        'INDICO_FLOWER_TOKEN_URL': url_for('oauth.oauth_token', _external=True),
        'INDICO_FLOWER_USER_URL': url_for('users.authenticated_user', _external=True)
    }
    if config.FLOWER_URL:
        auth_env['INDICO_FLOWER_URL'] = config.FLOWER_URL
    args = ('celery', '-b', config.CELERY_BROKER, 'flower', *flower_args, *auth_args)
    env = dict(os.environ, **auth_env)
    os.execvpe('celery', args, env)


@celery_cmd.command()
@click.argument('name')
def unlock(name):
    """Unlock a locked task.

    Use this if your celery worker was e.g. killed by your kernel's
    oom-killer and thus a task never got unlocked.

    Examples:

        indico celery unlock event_reminders
    """

    if unlock_task(name):
        print(cformat('%{green!}Task {} unlocked').format(name))
    else:
        print(cformat('%{yellow}Task {} is not locked').format(name))
