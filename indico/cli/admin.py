from __future__ import print_function

import transaction
from flask_script import Manager, prompt, prompt_bool

from indico.core.db import db
from indico.modules.users import User
from indico.util.console import cformat, prompt_email, prompt_pass, success, error, warning
from indico.util.string import to_unicode

IndicoAdminManager = Manager(usage="Manages administration actions")


def print_user_info(user):
    print()
    print(u'User info:')
    print(u"  First name: {}".format(user.first_name))
    print(u"  Family name: {}".format(user.last_name))
    print(u"  Email: {}".format(user.email))
    print(u"  Affiliation: {}".format(user.affiliation))
    print()


@IndicoAdminManager.option('-a', '--admin', action='store_true', dest="grant_admin",
                           help="Grants administration rights")
def user_create(grant_admin):
    """Creates new user"""
    user = User()
    user_type = 'user' if not grant_admin else 'admin'

    print()
    name = prompt("First name")
    surname = prompt("Last name")
    affiliation = prompt("Affiliation")
    print()
    username = prompt("Enter username")
    email = prompt_email()
    if email is None:
        return
    password = prompt_pass()
    if password is None:
        return

    user.first_name = to_unicode(name)
    user.last_name = to_unicode(surname)
    user.affiliation = to_unicode(affiliation)
    user.email = email
    user.is_admin = grant_admin
    print_user_info(user)

    if prompt_bool(cformat("%{yellow}Create the new {}?").format(user_type), default=True):
        # TODO: adapt to new authentication system, create local identity with username/password
        # user.identities.append(UserIdentity(..., identifier=username, password=password))
        db.session.add(user)
        transaction.commit()
        success("New {} created successfully with ID: {}".format(user_type, user.id))


@IndicoAdminManager.option('user_id', type=int, help="ID of user to be granted admin rights")
def user_grant(user_id):
    """Grants administration rights to a given user"""
    user = User.get(user_id)
    if user is None:
        error("This user does not exist")
        return
    print_user_info(user)
    if user.is_admin:
        warning("This user already has administration rights")
        return
    if prompt_bool(cformat("%{yellow}Grant administration rights to this user?")):
        user.is_admin = True
        transaction.commit()
        success("Administration rights granted successfully")


@IndicoAdminManager.option('user_id', help="ID of user to be revoked from admin rights")
def user_revoke(user_id):
    """Revokes administration rights from a given user"""
    user = User.get(user_id)
    if user is None:
        error("This user does not exist")
        return
    print_user_info(user)
    if not user.is_admin:
        warning("This user does not have administration rights")
        return
    if prompt_bool(cformat("%{yellow}Revoke administration rights from this user?")):
        user.is_admin = False
        transaction.commit()
        success("Administration rights revoked successfully")
