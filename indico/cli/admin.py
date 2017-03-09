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

from indico.cli.core import cli_group
from indico.core.db import db
from indico.modules.auth import Identity
from indico.modules.users import User
from indico.modules.users.operations import create_user
from indico.util.console import cformat, prompt_email, prompt_pass, success, error, warning
from indico.util.string import to_unicode

click.disable_unicode_literals_warning = True


@cli_group()
def cli():
    pass


def _print_user_info(user):
    print()
    print('User info:')
    print("  First name: {}".format(user.first_name))
    print("  Family name: {}".format(user.last_name))
    print("  Email: {}".format(user.email))
    print("  Affiliation: {}".format(user.affiliation))
    print()


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
        error('Email already exists')
    first_name = click.prompt("First name").strip()
    last_name = click.prompt("Last name").strip()
    affiliation = click.prompt("Affiliation", '').strip()
    print()
    while True:
        username = click.prompt("Enter username").lower().strip()
        if not Identity.find(provider='indico', identifier=username).count():
            break
        error('Username already exists')
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
        success("New {} created successfully with ID: {}".format(user_type, user.id))


@cli.command()
@click.argument('user_id', type=int)
def user_grant(user_id):
    """Grants administration rights to a given user"""
    user = User.get(user_id)
    if user is None:
        error("This user does not exist")
        return
    _print_user_info(user)
    if user.is_admin:
        warning("This user already has administration rights")
        return
    if click.confirm(cformat("%{yellow}Grant administration rights to this user?")):
        user.is_admin = True
        db.session.commit()
        success("Administration rights granted successfully")


@cli.command()
@click.argument('user_id', type=int)
def user_revoke(user_id):
    """Revokes administration rights from a given user"""
    user = User.get(user_id)
    if user is None:
        error("This user does not exist")
        return
    _print_user_info(user)
    if not user.is_admin:
        warning("This user does not have administration rights")
        return
    if click.confirm(cformat("%{yellow}Revoke administration rights from this user?")):
        user.is_admin = False
        db.session.commit()
        success("Administration rights revoked successfully")
