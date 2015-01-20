from __future__ import print_function

from flask_script import Manager, prompt, prompt_bool

from indico.core.db.util import with_zodb
from indico.util.console import cformat, prompt_email, prompt_pass, success, error, warning
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.errors import UserError
from MaKaC.user import AvatarHolder, Avatar, LoginInfo


IndicoAdminManager = Manager(usage="Manages administration actions")


def print_user_info(avatar):
    print()
    print('User info:')
    print("  First name: {}".format(avatar.getFirstName()))
    print("  Family name: {}".format(avatar.getFamilyName()))
    print("  Email: {}".format(avatar.getEmail()))
    print("  Affiliation: {}".format(avatar.getAffiliation()))
    print()


@IndicoAdminManager.option('-a', '--admin', action='store_true', dest="grant_admin",
                           help="Grants administration rights")
@with_zodb
def user_create(grant_admin):
    """Creates new user"""
    avatar = Avatar()
    user_type = 'user' if not grant_admin else 'admin'

    print()
    name = prompt("First name")
    surname = prompt("Last name")
    organization = prompt("Affiliation")
    print()
    login = prompt("Enter username")
    email = prompt_email().encode('utf-8')
    if email is None:
        return
    password = prompt_pass().encode('utf-8')
    if password is None:
        return

    avatar.setName(name)
    avatar.setSurName(surname)
    avatar.setOrganisation(organization)
    avatar.setLang("en_GB")
    avatar.setEmail(email)
    print_user_info(avatar)

    if prompt_bool(cformat("%{yellow}Create the new {}?").format(user_type), default=True):
        from MaKaC.authentication import AuthenticatorMgr
        avatar.activateAccount()
        login_info = LoginInfo(login, password)
        auth_mgr = AuthenticatorMgr()
        try:
            user_id = auth_mgr.createIdentity(login_info, avatar, "Local")
            auth_mgr.add(user_id)
            AvatarHolder().add(avatar)
            if grant_admin:
                admin_list = HelperMaKaCInfo.getMaKaCInfoInstance().getAdminList()
                admin_list.grant(avatar)
            success("New {} created successfully with ID: {}".format(user_type, avatar.getId()))
        except UserError as e:
            error("Error: {}".format(str(e)))


@IndicoAdminManager.option('user_id', help="ID of user to be granted admin rights")
@with_zodb
def user_grant(user_id):
    """Grants administration rights to a given user"""
    avatar = AvatarHolder().getById(user_id)
    if avatar is None:
        error("This user does not exist")
        return
    print_user_info(avatar)
    if avatar.isAdmin():
        warning("This user already has administration rights")
        return
    if prompt_bool(cformat("%{yellow}Grant administration rights to this user?")):
        admin_list = HelperMaKaCInfo.getMaKaCInfoInstance().getAdminList()
        admin_list.grant(avatar)
        avatar.activateAccount()
        success("Administration rights granted successfully")


@IndicoAdminManager.option('user_id', help="ID of user to be revoked from admin rights")
@with_zodb
def user_revoke(user_id):
    """Revokes administration rights from a given user"""
    avatar = AvatarHolder().getById(user_id)
    if avatar is None:
        error("This user does not exist")
        return
    print_user_info(avatar)
    if not avatar.isAdmin():
        warning("This user does not have administration rights")
        return
    if prompt_bool(cformat("%{yellow}Revoke administration rights from this user?")):
        admin_list = HelperMaKaCInfo.getMaKaCInfoInstance().getAdminList()
        admin_list.revoke(avatar)
        success("Administration rights revoked successfully")
