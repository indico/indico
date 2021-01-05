# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import print_function, unicode_literals

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
    flags = []
    if user.is_admin:
        flags.append('%{yellow}admin%{reset}')
    if user.is_blocked:
        flags.append('%{red}blocked%{reset}')
    if user.is_deleted:
        flags.append('%{red!}deleted%{reset}')
    if user.is_pending:
        flags.append('%{cyan}pending%{reset}')
    print()
    print('User info:')
    print("  ID: {}".format(user.id))
    print("  First name: {}".format(user.first_name))
    print("  Family name: {}".format(user.last_name))
    print("  Email: {}".format(user.email))
    print("  Affiliation: {}".format(user.affiliation))
    if flags:
        print(cformat("  Flags: {}".format(', '.join(flags))))
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
@click.option('--include-blocked', '-B', is_flag=True,
              help='Include blocked users in the results')
@click.option('--include-external', '-X', is_flag=True,
              help='Also include external users (e.g. from LDAP). This is potentially very slow in substring mode')
@click.option('--include-system', '-S', is_flag=True,
              help='Also include the system user')
@click.option('--first-name', '-n', help='First name of the user')
@click.option('--last-name', '-s', help='Last name of the user')
@click.option('--email', '-e', help='Email address of the user')
@click.option('--affiliation', '-a', help='Affiliation of the user')
def search(substring, include_deleted, include_pending, include_blocked, include_external, include_system, **criteria):
    """Search users matching some criteria."""
    assert set(criteria.viewkeys()) == {'first_name', 'last_name', 'email', 'affiliation'}
    criteria = {k: v for k, v in criteria.viewitems() if v is not None}
    res = search_users(exact=(not substring), include_deleted=include_deleted, include_pending=include_pending,
                       include_blocked=include_blocked, external=include_external,
                       allow_system_user=include_system, **criteria)
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
def create(grant_admin):
    """Create a new user."""
    user_type = 'user' if not grant_admin else 'admin'
    while True:
        email = prompt_email()
        if email is None:
            return
        email = email.lower()
        if not User.query.filter(User.all_emails == email, ~User.is_deleted, ~User.is_pending).has_rows():
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
def grant_admin(user_id):
    """Grant administration rights to a given user."""
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
def revoke_admin(user_id):
    """Revoke administration rights from a given user."""
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


@cli.command()
@click.argument('user_id', type=int)
def block(user_id):
    """Block a given user."""
    user = User.get(user_id)
    if user is None:
        print(cformat("%{red}This user does not exist"))
        return
    _print_user_info(user)
    if user.is_blocked:
        print(cformat("%{yellow}This user is already blocked"))
        return
    if click.confirm(cformat("%{yellow}Block this user?")):
        user.is_blocked = True
        db.session.commit()
        print(cformat("%{green}Successfully blocked user"))


@cli.command()
@click.argument('user_id', type=int)
def unblock(user_id):
    """Unblock a given user."""
    user = User.get(user_id)
    if user is None:
        print(cformat("%{red}This user does not exist"))
        return
    _print_user_info(user)
    if not user.is_blocked:
        print(cformat("%{yellow}This user is not blocked"))
        return
    if click.confirm(cformat("%{yellow}Unblock this user?")):
        user.is_blocked = False
        db.session.commit()
        print(cformat("%{green}Successfully unblocked user"))
