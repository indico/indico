# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import os
import sys

from celery.bin.celery import CeleryCommand, command_classes

from indico.core.config import Config
from indico.core.celery import celery
from indico.modules.oauth.models.applications import OAuthApplication
from indico.util.console import cformat
from indico.web.flask.util import url_for


def celery_cmd(args):
    # remove the celery shell command
    next(funcs for group, funcs, _ in command_classes if group == 'Main').remove('shell')
    del CeleryCommand.commands['shell']

    if args and args[0] == 'flower':
        # Somehow flower hangs when executing it using CeleryCommand() so we simply exec it directly.
        # It doesn't really need the celery config anyway (besides the broker url)

        try:
            import flower
        except ImportError:
            print cformat('%{red!}Flower is not installed')
            sys.exit(1)

        client_id = Config.getInstance().getFlowerClientId()
        if client_id:
            app = OAuthApplication.find_first(client_id=client_id)
            if app is None:
                print cformat('%{red!}There is no OAuth application with the client id {}.').format(client_id)
                sys.exit(1)
            elif 'read:user' not in app.default_scopes:
                print cformat('%{red!}The {} application needs the read:user scope.').format(app.name)
                sys.exit(1)
            print cformat('%{green!}Only Indico admins will have access to flower.')
            print cformat('%{yellow}Note that revoking admin privileges will not revoke Flower access.')
            print cformat('%{yellow}To force re-authentication, restart Flower.')
            auth_args = ['--auth=^Indico Admin$', '--auth_provider=indico.core.celery.flower.FlowerAuthHandler']
            auth_env = {'INDICO_FLOWER_CLIENT_ID': app.client_id,
                        'INDICO_FLOWER_CLIENT_SECRET': app.client_secret,
                        'INDICO_FLOWER_AUTHORIZE_URL': url_for('oauth.oauth_authorize', _external=True),
                        'INDICO_FLOWER_TOKEN_URL': url_for('oauth.oauth_token', _external=True),
                        'INDICO_FLOWER_USER_URL': url_for('users.authenticated_user', _external=True)}
        else:
            print cformat('%{red!}WARNING: %{yellow!}Flower authentication is disabled.')
            print cformat('%{yellow!}Having access to Flower allows one to shutdown Celery workers.')
            print
            auth_args = []
            auth_env = {}
        args = ['celery', '-b', Config.getInstance().getCeleryBroker()] + args + auth_args
        env = dict(os.environ, **auth_env)
        os.execvpe('celery', args, env)
    elif args and args[0] == 'shell':
        print cformat('%{red!}Please use `indico shell`.')
        sys.exit(1)
    else:
        CeleryCommand(celery).execute_from_commandline(['indico celery'] + args)
