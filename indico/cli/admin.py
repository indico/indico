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

from __future__ import unicode_literals, print_function

import click
from flask_multipass import IdentityInfo
from terminaltables import AsciiTable

from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.auth import Identity
from indico.modules.users import User
from indico.modules.users.operations import create_user
from indico.modules.users.util import search_users
from indico.util.console import cformat, prompt_email, prompt_pass
from indico.util.string import to_unicode

click.disable_unicode_literals_warning = True


@cli_group()
def cli():
    pass


def _print_user_info(user):
    print()
    print('User info:')
    print("  ID: {}".format(user.id))
    print("  First name: {}".format(user.first_name))
    print("  Family name: {}".format(user.last_name))
    print("  Email: {}".format(user.email))
    print("  Affiliation: {}".format(user.affiliation))
    print()


def _safe_lower(s):
    return (s or '').lower()


@cli.command()
@click.option('--substring', is_flag=True,
              help='Whether to require exact matches (default) or do substring matches (slower)')
@click.option('--include-deleted', '-D', is_flag=True,
              help='Include deleted users in the results')
@click.option('--include-pending', '-P', is_flag=True,
              help='Include pending users in the results')
@click.option('--include-external', '-X', is_flag=True,
              help='Also include external users (e.g. from LDAP). This is potentially very slow in substring mode')
@click.option('--include-system', '-S', is_flag=True,
              help='Also include the system user')
@click.option('--first-name', '-n', help='First name of the user')
@click.option('--last-name', '-s', help='Last name of the user')
@click.option('--email', '-e', help='Email address of the user')
@click.option('--affiliation', '-a', help='Affiliation of the user')
def user_search(substring, include_deleted, include_pending, include_external, include_system, **criteria):
    """Searches users matching some criteria"""
    assert set(criteria.viewkeys()) == {'first_name', 'last_name', 'email', 'affiliation'}
    criteria = {k: v for k, v in criteria.viewitems() if v is not None}
    res = search_users(exact=(not substring), include_deleted=include_deleted, include_pending=include_pending,
                       external=include_external, allow_system_user=include_system, **criteria)
    if not res:
        print(cformat('%{yellow}No results found'))
        return
    elif len(res) > 100:
        click.confirm('{} results found. Show them anyway?'.format(len(res)), abort=True)
    users = sorted((u for u in res if isinstance(u, User)), key=lambda x: (x.first_name.lower(), x.last_name.lower(),
                                                                           x.email))
    externals = sorted((ii for ii in res if isinstance(ii, IdentityInfo)),
                       key=lambda x: (_safe_lower(x.data.get('first_name')), _safe_lower(x.data.get('last_name')),
                                      _safe_lower(x.data['email'])))
    if users:
        table_data = [['ID', 'First Name', 'Last Name', 'Email', 'Affiliation']]
        for user in users:
            table_data.append([unicode(user.id), user.first_name, user.last_name, user.email, user.affiliation])
        table = AsciiTable(table_data, cformat('%{white!}Users%{reset}'))
        table.justify_columns[0] = 'right'
        print(table.table)
    if externals:
        if users:
            print()
        table_data = [['First Name', 'Last Name', 'Email', 'Affiliation', 'Source', 'Identifier']]
        for ii in externals:
            data = ii.data
            table_data.append([data.get('first_name', ''), data.get('last_name', ''), data['email'],
                               data.get('affiliation', '-'), ii.provider.name, ii.identifier])
        table = AsciiTable(table_data, cformat('%{white!}Externals%{reset}'))
        print(table.table)


@cli.command()
@click.option('--admin/--no-admin', '-a/', 'grant_admin', is_flag=True, help='Grant admin rights')
def user_create(grant_admin):
    """Creates new user"""
    user_type = 'user' if not grant_admin else 'admin'
    while True:
        email = prompt_email()
        if email is None:
            return
        email = email.lower()
        if not User.find(User.all_emails.contains(email), ~User.is_deleted, ~User.is_pending).count():
            break
        print(cformat('%{red}Email already exists'))
    first_name = click.prompt("First name").strip()
    last_name = click.prompt("Last name").strip()
    affiliation = click.prompt("Affiliation", '').strip()
    print()
    while True:
        username = click.prompt("Enter username").lower().strip()
        if not Identity.find(provider='indico', identifier=username).count():
            break
        print(cformat('%{red}Username already exists'))
    password = prompt_pass()
    if password is None:
        return

    identity = Identity(provider='indico', identifier=username, password=password)
    user = create_user(email, {'first_name': to_unicode(first_name), 'last_name': to_unicode(last_name),
                               'affiliation': to_unicode(affiliation)}, identity)
    user.is_admin = grant_admin
    _print_user_info(user)

    if click.confirm(cformat("%{yellow}Create the new {}?").format(user_type), default=True):
        db.session.add(user)
        db.session.commit()
        print(cformat("%{green}New {} created successfully with ID: %{green!}{}").format(user_type, user.id))


@cli.command()
@click.argument('user_id', type=int)
def user_grant(user_id):
    """Grants administration rights to a given user"""
    user = User.get(user_id)
    if user is None:
        print(cformat("%{red}This user does not exist"))
        return
    _print_user_info(user)
    if user.is_admin:
        print(cformat("%{yellow}This user already has administration rights"))
        return
    if click.confirm(cformat("%{yellow}Grant administration rights to this user?")):
        user.is_admin = True
        db.session.commit()
        print(cformat("%{green}Administration rights granted successfully"))


@cli.command()
@click.argument('user_id', type=int)
def user_revoke(user_id):
    """Revokes administration rights from a given user"""
    user = User.get(user_id)
    if user is None:
        print(cformat("%{red}This user does not exist"))
        return
    _print_user_info(user)
    if not user.is_admin:
        print(cformat("%{yellow}This user does not have administration rights"))
        return
    if click.confirm(cformat("%{yellow}Revoke administration rights from this user?")):
        user.is_admin = False
        db.session.commit()
        print(cformat("%{green}Administration rights revoked successfully"))
