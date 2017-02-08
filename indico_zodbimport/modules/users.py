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

from datetime import timedelta
from uuid import uuid4

import click
import pytz
from babel.dates import get_timezone
from pytz import all_timezones_set

from indico.core.db import db
from indico.modules.api import APIKey
from indico.modules.auth import Identity
from indico.modules.users import User, user_settings
from indico.modules.users.models.users import UserTitle
from indico.util.caching import memoize
from indico.util.console import cformat
from indico.util.i18n import get_all_locales
from indico.util.string import is_valid_mail, sanitize_email
from indico.util.struct.iterables import committing_iterator, grouper

from indico_zodbimport import Importer, convert_to_unicode


USER_TITLE_MAP = {x.title: x for x in UserTitle}
SYNCED_FIELD_MAP = {
    'firstName': 'first_name',
    'surName': 'last_name',
    'affiliation': 'affiliation',
    'address': 'address',
    'phone': 'phone'
}


@memoize
def _get_all_locales():
    return set(get_all_locales())


class UserImporter(Importer):
    def __init__(self, **kwargs):
        self.ldap_provider_name = kwargs.pop('ldap_provider_name')
        self.ignore_local_accounts = kwargs.pop('ignore_local_accounts')
        super(UserImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--ldap-provider-name', default='legacy-ldap',
                               help="Provider name to use for existing LDAP identities")(command)
        command = click.option('--ignore-local-accounts', is_flag=True, default=False,
                               help="Do not migrate existing local accounts")(command)
        return command

    def has_data(self):
        return User.query.has_rows()

    def migrate(self):
        self.users_by_primary_email = {}
        self.users_by_secondary_email = {}
        self.migrate_users()
        self.fix_sequences('users', {'users'})
        self.migrate_favorite_users()
        self.migrate_admins()

    def migrate_users(self):
        print cformat('%{white!}migrating users')

        seen_identities = set()

        for avatar in committing_iterator(self._iter_avatars(), 5000):
            if getattr(avatar, '_mergeTo', None):
                print cformat('%{red!}!!!%{reset} '
                              '%{yellow!}Skipping {} - merged into {}').format(avatar.id, avatar._mergeTo.id)
                continue
            elif avatar.status == 'Not confirmed':
                print cformat('%{yellow!}!!!%{reset} '
                              '%{yellow!}Skipping {} - not activated').format(avatar.id)
                continue
            elif not avatar.name.strip() and not avatar.surName.strip():
                links = {(obj, role): list(objs)
                         for obj, x in avatar.linkedTo.iteritems()
                         for role, objs in x.iteritems()
                         if objs}
                if not avatar.identities and not links:
                    print cformat('%{yellow!}!!!%{reset} '
                                  '%{yellow!}Skipping {} - no names and no identities/links').format(avatar.id)
                    continue

            user = self._user_from_avatar(avatar)
            self._fix_collisions(user, avatar)
            db.session.add(user)
            settings = self._settings_from_avatar(avatar)
            user_settings.set_multi(user, settings)
            # favorite users cannot be migrated here since the target user might not have been migrated yet
            # XXX: adapt to new categories for 2.0
            user.favorite_categories = set(filter(None, avatar.linkedTo['category']['favorite']))
            db.session.flush()
            print cformat('%{green}+++%{reset} '
                          '%{white!}{:6d}%{reset} %{cyan}{}%{reset} [%{blue!}{}%{reset}] '
                          '{{%{cyan!}{}%{reset}}}').format(user.id, user.full_name, user.email,
                                                           ', '.join(user.secondary_emails))
            # migrate API keys
            self._migrate_api_keys(avatar, user)
            # migrate identities of non-deleted avatars
            if not user.is_deleted:
                for old_identity in avatar.identities:
                    identity = None
                    username = convert_to_unicode(old_identity.login).strip().lower()

                    if not username:
                        print cformat("%{red!}!!!%{reset} "
                                      "%{yellow!}Empty username: {}. Skipping identity.").format(
                                          old_identity)
                        continue

                    provider = {
                        'LocalIdentity': 'indico',
                        'LDAPIdentity': self.ldap_provider_name
                    }.get(old_identity.__class__.__name__)

                    if provider is None:
                        print cformat("%{red!}!!!%{reset} "
                                      "%{yellow!}Unsupported provider: {}. Skipping identity.").format(
                            old_identity.__class__.__name__)
                        continue

                    if (provider, username) in seen_identities:
                        print cformat("%{red!}!!!%{reset} "
                                      "%{yellow!}Duplicate identity: {}, {}. Skipping.").format(provider, username)
                        continue

                    if provider == 'indico' and not self.ignore_local_accounts:
                        identity = Identity(provider=provider, identifier=username)

                        if not hasattr(old_identity, 'algorithm'):  # plaintext password
                            if not old_identity.password:
                                # password is empty, skip identity
                                print cformat("%{red!}!!!%{reset} "
                                              "%{yellow!}Identity '{}' has empty password. Skipping identity.").format(
                                                  old_identity.login)
                                continue
                            identity.password = old_identity.password
                        else:
                            assert old_identity.algorithm == 'bcrypt'
                            identity.password_hash = old_identity.password

                    elif provider == self.ldap_provider_name:
                        identity = Identity(provider=provider, identifier=username)

                    if identity:
                        print cformat('%{blue!}<->%{reset}  %{yellow}{}%{reset}').format(identity)
                        user.identities.add(identity)
                        seen_identities.add((provider, username))

            for merged_avatar in getattr(avatar, '_mergeFrom', ()):
                if merged_avatar.id == avatar.id:
                    continue
                merged = self._user_from_avatar(merged_avatar, is_deleted=True, merged_into_id=user.id)
                print cformat('%{blue!}***%{reset} '
                              '%{white!}{:6d}%{reset} %{cyan}{}%{reset} [%{blue!}{}%{reset}] '
                              '{{%{cyan!}{}%{reset}}}').format(merged.id, merged.full_name, merged.email,
                                                               ', '.join(merged.secondary_emails))
                self._fix_collisions(merged, merged_avatar)
                db.session.add(merged)
                db.session.flush()

    def _migrate_api_keys(self, avatar, user):
        ak = getattr(avatar, 'apiKey', None)
        if not ak:
            return
        last_used_uri = None
        if ak._lastPath and ak._lastQuery:
            last_used_uri = '{}?{}'.format(convert_to_unicode(ak._lastPath), convert_to_unicode(ak._lastQuery))
        elif ak._lastPath:
            last_used_uri = convert_to_unicode(ak._lastPath)

        api_key = APIKey(token=ak._key, secret=ak._signKey, is_blocked=ak._isBlocked,
                         is_persistent_allowed=getattr(ak, '_persistentAllowed', False),
                         created_dt=self._to_utc(ak._createdDT), last_used_dt=self._to_utc(ak._lastUsedDT),
                         last_used_ip=ak._lastUsedIP, last_used_uri=last_used_uri,
                         last_used_auth=ak._lastUseAuthenticated, use_count=ak._useCount)
        user.api_key = api_key
        print cformat('%{blue!}<->%{reset}  %{yellow}{}%{reset}').format(api_key)

        for old_key in ak._oldKeys:
            # We have no creation time so we use *something* older..
            fake_created_dt = self._to_utc(ak._createdDT) - timedelta(hours=1)
            # We don't have anything besides the api key for old keys, so we use a random secret
            user.old_api_keys.append(APIKey(token=old_key, secret=unicode(uuid4()), created_dt=fake_created_dt,
                                            is_active=False))

    def migrate_favorite_users(self):
        print cformat('%{white!}migrating favorite users')
        for avatars in grouper(self._iter_avatars_with_favorite_users(), 2500, skip_missing=True):
            avatars = list(avatars)
            users = {u.id: u for u in User.find(User.id.in_(int(a.id) for a, _ in avatars))}
            for avatar, user_ids in committing_iterator(avatars, 1000):
                user = users.get(int(avatar.id))
                if user is None:
                    print cformat('%{red!}!!!%{reset} '
                                  '%{yellow!}User {} does not exist').format(avatar.id)
                    continue
                print cformat('%{green}+++%{reset} '
                              '%{white!}{:6d}%{reset} %{cyan}{}%{reset}').format(user.id, user.full_name)
                valid_users = {u.id: u for u in User.find(User.id.in_(user_ids))}
                for user_id in user_ids:
                    target = valid_users.get(user_id)
                    if target is None:
                        print cformat('%{yellow!}!!!%{reset} '
                                      '%{yellow!}User {} does not exist').format(user_id)
                        continue
                    user.favorite_users.add(target)
                    print cformat('%{blue!}<->%{reset} '
                                  '%{white!}{:6d}%{reset} %{cyan}{}%{reset}').format(target.id, target.full_name)

    def migrate_admins(self):
        print cformat('%{white!}migrating admins')
        for avatar in committing_iterator(self.zodb_root['adminlist']._AdminList__list):
            try:
                user = User.get(int(avatar.id))
            except ValueError:
                continue
            if user is None or user.is_deleted:
                continue
            user.is_admin = True
            print cformat('%{green}+++%{reset} %{cyan}{}').format(user)

    def _user_from_avatar(self, avatar, **kwargs):
        email = sanitize_email(convert_to_unicode(avatar.email).lower().strip())
        secondary_emails = {sanitize_email(convert_to_unicode(x).lower().strip()) for x in avatar.secondaryEmails}
        secondary_emails = {x for x in secondary_emails if x and is_valid_mail(x, False) and x != email}
        # we handle deletion later. otherwise it might be set before secondary_emails which would
        # result in those emails not being marked as deleted
        is_deleted = kwargs.pop('is_deleted', False)
        user = User(id=int(avatar.id),
                    email=email,
                    first_name=convert_to_unicode(avatar.name).strip() or 'UNKNOWN',
                    last_name=convert_to_unicode(avatar.surName).strip() or 'UNKNOWN',
                    title=USER_TITLE_MAP.get(avatar.title, UserTitle.none),
                    phone=convert_to_unicode(avatar.telephone[0]).strip(),
                    affiliation=convert_to_unicode(avatar.organisation[0]).strip(),
                    address=convert_to_unicode(avatar.address[0]).strip(),
                    secondary_emails=secondary_emails,
                    is_blocked=avatar.status == 'disabled',
                    **kwargs)
        if is_deleted or not is_valid_mail(user.email):
            user.is_deleted = True
        return user

    def _settings_from_avatar(self, avatar):
        timezone = avatar.timezone
        if not timezone or timezone not in all_timezones_set:
            timezone = getattr(self.zodb_root['MaKaCInfo']['main'], '_timezone', 'UTC')
        language = avatar._lang

        if language not in _get_all_locales():
            language = getattr(self.zodb_root['MaKaCInfo']['main'], '_lang', 'en_GB')
        show_past_events = False

        if hasattr(avatar, 'personalInfo'):
            show_past_events = bool(getattr(avatar.personalInfo, '_showPastEvents', False))

        settings = {
            'lang': language,
            'timezone': timezone,
            'force_timezone': avatar.displayTZMode == 'MyTimezone',
            'show_past_events': show_past_events,
        }

        unlocked_fields = {SYNCED_FIELD_MAP.get(field) for field in getattr(avatar, 'unlockedFields', [])} - {None}
        if unlocked_fields:
            settings['synced_fields'] = list(set(SYNCED_FIELD_MAP.viewvalues()) - unlocked_fields)

        return settings

    def _fix_collisions(self, user, avatar):
        is_deleted = user.is_deleted
        # Mark both users as deleted if there's a primary email collision
        coll = self.users_by_primary_email.get(user.email)
        if coll and not is_deleted:
            if bool(avatar.identities) ^ bool(coll.identities):
                # exactly one of them has identities - keep the one that does
                to_delete = {coll if avatar.identities else user}
            else:
                to_delete = {user, coll}
            for u in to_delete:
                print cformat('%{magenta!}---%{reset} '
                              '%{yellow!}Deleting {} - primary email collision%{reset} '
                              '[%{blue!}{}%{reset}]').format(u.id, u.email)
                u.is_deleted = True
                db.session.flush()
        # if the user was already deleted we don't care about primary email collisions
        if not is_deleted:
            self.users_by_primary_email[user.email] = user

        # Remove primary email from another user's secondary email list
        coll = self.users_by_secondary_email.get(user.email)
        if coll and user.merged_into_id != coll.id:
            print cformat('%{magenta!}---%{reset} '
                          '%{yellow!}1 Removing colliding secondary email (P/S) from {}%{reset} '
                          '[%{blue!}{}%{reset}]').format(coll, user.email)
            coll.secondary_emails.remove(user.email)
            del self.users_by_secondary_email[user.email]
            db.session.flush()

        # Remove email from both users if there's a collision
        for email in list(user.secondary_emails):
            # colliding with primary email
            coll = self.users_by_primary_email.get(email)
            if coll:
                print cformat('%{magenta!}---%{reset} '
                              '%{yellow!}Removing colliding secondary email (S/P) from {}%{reset} '
                              '[%{blue!}{}%{reset}]').format(user, email)
                user.secondary_emails.remove(email)
                db.session.flush()
            # colliding with a secondary email
            coll = self.users_by_secondary_email.get(email)
            if coll:
                print cformat('%{magenta!}---%{reset} '
                              '%{yellow!}Removing colliding secondary email (S/S) from {}%{reset} '
                              '[%{blue!}{}%{reset}]').format(user, email)
                user.secondary_emails.remove(email)
                db.session.flush()
                self.users_by_secondary_email[email] = coll
            # if the user was already deleted we don't care about secondary email collisions
            if not is_deleted and email in user.secondary_emails:
                self.users_by_secondary_email[email] = user

    def _to_utc(self, dt):
        if dt is None:
            return None
        server_tz = get_timezone(getattr(self.zodb_root['MaKaCInfo']['main'], '_timezone', 'UTC'))
        return server_tz.localize(dt).astimezone(pytz.utc)

    def _iter_avatars(self):
        return self.zodb_root['avatars'].itervalues()

    def _iter_avatars_with_favorite_users(self):
        for avatar in self._iter_avatars():
            if not hasattr(avatar, 'personalInfo'):
                continue
            if not avatar.personalInfo._basket._users:
                continue
            yield avatar, map(int, avatar.personalInfo._basket._users)
