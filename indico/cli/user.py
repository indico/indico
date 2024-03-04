# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import click
from flask_multipass import IdentityInfo
from sqlalchemy.exc import IntegrityError
from terminaltables import AsciiTable

from indico.cli.core import cli_group
from indico.core import signals
from indico.core.db import db
from indico.core.oauth.models.personal_tokens import PersonalToken
from indico.core.oauth.scopes import SCOPES
from indico.modules.auth import Identity
from indico.modules.users import User
from indico.modules.users.operations import create_user
from indico.modules.users.util import anonymize_user, search_users
from indico.util.console import cformat, prompt_email, prompt_pass
from indico.util.date_time import utc_to_server


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
    print('User info:')
    print(f'  ID: {user.id}')
    print(f'  First name: {user.first_name}')
    print(f'  Family name: {user.last_name}')
    print(f'  Email: {user.email}')
    print(f'  Affiliation: {user.affiliation}')
    print(f'  Last login: {user.last_login_dt.date() if user.last_login_dt else "never"}')
    if flags:
        print(cformat('  Flags: {}'.format(', '.join(flags))))
    print()


def _safe_lower(s):
    return (s or '').lower()


def _format_dt(dt):
    return utc_to_server(dt.replace(second=0, microsecond=0)).replace(tzinfo=None).isoformat(' ') if dt else None


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
    assert set(criteria.keys()) == {'first_name', 'last_name', 'email', 'affiliation'}
    criteria = {k: v for k, v in criteria.items() if v is not None}
    res = search_users(exact=(not substring), include_deleted=include_deleted, include_pending=include_pending,
                       include_blocked=include_blocked, external=include_external,
                       allow_system_user=include_system, **criteria)
    if not res:
        click.secho('No results found', fg='yellow')
        return
    elif len(res) > 100:
        click.confirm(f'{len(res)} results found. Show them anyway?', abort=True)
    users = sorted((u for u in res if isinstance(u, User)), key=lambda x: (x.first_name.lower(), x.last_name.lower(),
                                                                           x.email))
    externals = sorted((ii for ii in res if isinstance(ii, IdentityInfo)),
                       key=lambda x: (_safe_lower(x.data.get('first_name')), _safe_lower(x.data.get('last_name')),
                                      _safe_lower(x.data['email'])))
    if users:
        table_data = [['ID', 'First Name', 'Last Name', 'Email', 'Affiliation']]
        table_data.extend([str(user.id), user.first_name, user.last_name, user.email, user.affiliation]
                          for user in users)
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
        click.secho('Email already exists', fg='red')
    first_name = click.prompt('First name').strip()
    last_name = click.prompt('Last name').strip()
    affiliation = click.prompt('Affiliation', '').strip()
    print()
    while True:
        username = click.prompt('Enter username').lower().strip()
        if not Identity.query.filter_by(provider='indico', identifier=username).has_rows():
            break
        click.secho('Username already exists', fg='red')
    password = prompt_pass()
    if password is None:
        return

    identity = Identity(provider='indico', identifier=username, password=password)
    user = create_user(email, {'first_name': first_name, 'last_name': last_name, 'affiliation': affiliation}, identity)
    user.is_admin = grant_admin
    _print_user_info(user)

    if click.confirm(click.style(f'Create the new {user_type}?', fg='yellow'), default=True):
        db.session.add(user)
        db.session.commit()
        print(cformat('%{green}New {} created successfully with ID: %{green!}{}').format(user_type, user.id))


@cli.command()
@click.argument('user_id', type=int)
def grant_admin(user_id):
    """Grant administration rights to a given user."""
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red')
        return
    _print_user_info(user)
    if user.is_admin:
        click.secho('This user already has administration rights', fg='yellow')
        return
    if click.confirm(click.style('Grant administration rights to this user?', fg='yellow')):
        user.is_admin = True
        db.session.commit()
        click.secho('Administration rights granted successfully', fg='green')


@cli.command()
@click.argument('user_id', type=int)
def revoke_admin(user_id):
    """Revoke administration rights from a given user."""
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red')
        return
    _print_user_info(user)
    if not user.is_admin:
        click.secho('This user does not have administration rights', fg='yellow')
        return
    if click.confirm(click.style('Revoke administration rights from this user?', fg='yellow')):
        user.is_admin = False
        db.session.commit()
        click.secho('Administration rights revoked successfully', fg='green')


@cli.command()
@click.argument('user_id', type=int)
def block(user_id):
    """Block a given user."""
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red')
        return
    _print_user_info(user)
    if user.is_blocked:
        click.secho('This user is already blocked', fg='yellow')
        return
    if click.confirm(click.style('Block this user?', fg='yellow')):
        user.is_blocked = True
        db.session.commit()
        click.secho('Successfully blocked user', fg='green')


@cli.command()
@click.argument('user_id', type=int)
def unblock(user_id):
    """Unblock a given user."""
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red')
        return
    _print_user_info(user)
    if not user.is_blocked:
        click.secho('This user is not blocked', fg='yellow')
        return
    if click.confirm(click.style('Unblock this user?', fg='yellow')):
        user.is_blocked = False
        db.session.commit()
        click.secho('Successfully unblocked user', fg='green')


@cli.command()
@click.argument('user_id', type=int)
def anonymize(user_id):
    """Anonymize a given user.

    This will remove all personal data about the given user including
    their name, affiliation and emails. Note that any data tied to events
    such as registrations or speaker roles will not be deleted.
    """
    if (user := User.get(user_id)) is None:
        click.secho('This user does not exist', fg='red')
        return
    _print_user_info(user)
    if not click.confirm(click.style('Permanently anonymize this user?', fg='yellow')):
        return

    anonymize_user(user)
    db.session.commit()
    click.secho('Successfully anonymized user', fg='green')


@cli.command()
@click.argument('user_id', type=int)
def delete(user_id):
    """Delete a given user.

    This will completely remove the user and everything
    they are connected to. Use at your own risk.
    """
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red')
        return
    _print_user_info(user)
    if not click.confirm(click.style('Permanently delete this user?', fg='yellow')):
        return

    signals.users.db_deleted.send(user, flushed=False)

    try:
        db.session.delete(user)
        db.session.flush()
    except IntegrityError as e:
        db.session.rollback()
        click.secho('Could not delete delete user', fg='red')
        click.echo(e)
    else:
        signals.users.db_deleted.send(user, flushed=True)
        db.session.commit()
        click.secho('Successfully deleted user', fg='green')


@cli.group('token')
def token_cli():
    """Manage personal user tokens."""


@token_cli.command('list')
@click.argument('user_id', type=int)
@click.option('--verbose', '-v', is_flag=True, help='Show more verbose information and include revoked tokens')
def token_list(user_id, verbose):
    """List the tokens of the user."""
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red', bold=True)
        return
    _print_user_info(user)
    query = (
        user.query_personal_tokens(include_revoked=verbose)
        .order_by(
            PersonalToken.revoked_dt.isnot(None),
            db.func.lower(PersonalToken.name)
        )
    )

    tokens = query.all()
    if not tokens:
        click.secho('This user has no tokens', fg='yellow')
        return

    verbose_cols = ('Last IP', 'Use count', 'Status', 'ID') if verbose else ()
    table_data = [['Name', 'Scope', 'Created', 'Last used', *verbose_cols]]
    for token in tokens:
        verbose_data = ()
        if verbose:
            verbose_data = (
                token.last_used_ip,
                token.use_count,
                'Revoked' if token.revoked_dt else 'Active',
                token.id,
            )
        table_data.append([
            token.name,
            token.get_scope(),
            _format_dt(token.created_dt),
            _format_dt(token.last_used_dt) or 'Never',
            *verbose_data,
        ])
    click.echo(AsciiTable(table_data, cformat('%{white!}Tokens%{reset}')).table)


def _show_available_scopes(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    table_data = [['Name', 'Description'], *sorted(SCOPES.items())]
    click.echo(AsciiTable(table_data, cformat('%{white!}Available scopes%{reset}')).table)
    ctx.exit()


@token_cli.command('create')
@click.argument('user_id', type=int)
@click.argument('token_name')
@click.option('--scope', '-s', 'scopes', multiple=True, metavar='SCOPE', type=click.Choice(SCOPES),
              help='Include the specified scope; repeat for multiple scopes')
@click.option('--list-scopes', is_flag=True, callback=_show_available_scopes, expose_value=False, is_eager=True,
              help='Show a list of available scopes and exit')
def token_create(user_id, token_name, scopes):
    """Create a personal token for a user."""
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red', bold=True)
        return
    token = user.query_personal_tokens().filter(db.func.lower(PersonalToken.name) == token_name.lower()).first()
    if token:
        click.secho('A token with this name already exists', fg='red', bold=True)
        return
    token = PersonalToken(user=user, name=token_name, scopes=scopes)
    access_token = token.generate_token()
    db.session.commit()
    click.echo(cformat("%{green}Token '{}' created: %{white!}{}").format(token.name, access_token))
    click.echo(f'Scopes: {token.get_scope() or "-"}')


@token_cli.command('update')
@click.argument('user_id', type=int)
@click.argument('token_name')
@click.option('--name', '-n', 'new_token_name', metavar='NAME', help='Rename the token')
@click.option('--reset', '-r', 'reset_token', is_flag=True, help='Reset the access token')
@click.option('--add-scope', '-A', 'add_scopes', multiple=True, metavar='SCOPE', type=click.Choice(SCOPES),
              help='Add the specified scope; repeat for multiple scopes')
@click.option('--del-scope', '-D', 'del_scopes', multiple=True, metavar='SCOPE', type=click.Choice(SCOPES),
              help='Remove the specified scope; repeat for multiple scopes')
@click.option('--list-scopes', is_flag=True, callback=_show_available_scopes, expose_value=False, is_eager=True,
              help='Show a list of available scopes and exit')
def token_update(user_id, token_name, add_scopes, del_scopes, new_token_name, reset_token):
    """Update a personal token of a user."""
    if not add_scopes and not del_scopes and not new_token_name and not reset_token:
        click.echo('Nothing to do')
        return
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red', bold=True)
        return
    token = user.query_personal_tokens().filter(db.func.lower(PersonalToken.name) == token_name.lower()).first()
    if not token:
        click.secho('This token does not exist or has been revoked', fg='red', bold=True)
        return
    old_scopes = set(token.scopes)
    old_name = token.name
    new_access_token = None
    if add_scopes or del_scopes:
        token.scopes = (token.scopes | set(add_scopes)) - set(del_scopes)
    if new_token_name:
        conflict = (
            user.query_personal_tokens()
            .filter(
                PersonalToken.id != token.id,
                db.func.lower(PersonalToken.name) == new_token_name.lower()
            )
            .has_rows()
        )
        if conflict:
            click.secho('A token with this name already exists', fg='red', bold=True)
            return
        token.name = new_token_name
    if reset_token:
        new_access_token = token.generate_token()
    db.session.commit()
    click.secho(f"Token '{old_name}' updated", fg='green')
    if token.name != old_name:
        click.secho(f'Name: {token.name}', bold=True)
    if new_access_token:
        click.secho(f'Token: {new_access_token}', bold=True)
    if token.scopes != old_scopes:
        click.echo(f'Scopes: {token.get_scope() or "-"}')


@token_cli.command('revoke')
@click.argument('user_id', type=int)
@click.argument('token_name')
def token_revoke(user_id, token_name):
    """Revoke a user's personal token."""
    user = User.get(user_id)
    if user is None:
        click.secho('This user does not exist', fg='red', bold=True)
        return
    token = user.query_personal_tokens().filter(db.func.lower(PersonalToken.name) == token_name.lower()).first()
    if not token:
        click.secho('This token does not exist or has been revoked', fg='red', bold=True)
        return
    elif token.revoked_dt:
        click.secho('This token is already revoked', fg='yellow')
        return
    token.revoke()
    db.session.commit()
    click.secho(f"Token '{token.name}' revoked", fg='green')
