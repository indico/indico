# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import hashlib
import json
import os
import subprocess

import click

from flask_url_map_serializer import dump_url_map


def get_map_version():
    # build a version identifier that is very likely to be different
    # whenever something changed
    h = hashlib.md5()
    h.update(os.getcwd())
    h.update(subprocess.check_output(['git', 'describe', '--always']))
    h.update(subprocess.check_output(['git', 'status']))
    h.update(subprocess.check_output(['git', 'diff']))
    return h.hexdigest()


def get_rules(plugin):
    from indico.web.flask.app import make_app
    app = make_app(set_path=True, testing=True, config_override={'BASE_URL': 'http://localhost/',
                                                                 'SECRET_KEY': '*' * 16,
                                                                 'PLUGINS': {plugin} if plugin else set()})
    return dump_url_map(app.url_map)


@click.command()
@click.option('-f', '--force', is_flag=True, help='Force rebuilding the URL map')
@click.option('-o', '--output', default='url_map.json', help='Output file for the URL map')
@click.option('-p', '--plugin', help='Include URLs from the specified plugin')
def main(force, output, plugin=None):
    """
    Dumps the URL routing map to JSON for use by the `babel-flask-url` babel plugin.
    """
    try:
        with open(output) as f:
            data = json.load(f)
    except IOError:
        data = {}
    version = get_map_version()
    if not force and data.get('version') == version:
        return
    rules = get_rules(plugin)
    data['version'] = version
    data['rules'] = rules
    with open(output, 'w') as f:
        json.dump(data, f, sort_keys=True, indent=2)


if __name__ == '__main__':
    main()
