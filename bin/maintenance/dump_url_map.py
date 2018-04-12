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

import hashlib
import json
import os
import subprocess

import click

from flask_url_map_serializer import dump_url_map


URL_MAP_FILE = 'url_map.json'


def get_map_version():
    # build a version identifier that is very likely to be different
    # whenever something changed
    h = hashlib.md5()
    h.update(os.getcwd())
    h.update(subprocess.check_output(['git', 'describe']))
    h.update(subprocess.check_output(['git', 'status']))
    h.update(subprocess.check_output(['git', 'diff']))
    return h.hexdigest()


def get_rules():
    from indico.web.flask.app import make_app
    app = make_app(set_path=True, testing=True, config_override={'BASE_URL': 'http://localhost/',
                                                                 'SECRET_KEY': '*' * 16})
    return dump_url_map(app.url_map)


@click.command()
@click.option('-f', '--force', is_flag=True, help='Force rebuilding the URL map')
def main(force):
    """
    Dumps the URL routing map to JSON for use by the `babel-flask-url` babel plugin.
    """
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
    try:
        with open(URL_MAP_FILE) as f:
            data = json.load(f)
    except IOError:
        data = {}
    version = get_map_version()
    if not force and data.get('version') == version:
        return
    rules = get_rules()
    data['version'] = version
    data['rules'] = rules
    with open(URL_MAP_FILE, 'w') as f:
        json.dump(data, f, sort_keys=True, indent=2)


if __name__ == '__main__':
    main()
