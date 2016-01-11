# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from collections import namedtuple
from datetime import datetime
from operator import attrgetter

from flask import session, request, flash, jsonify, redirect
from markupsafe import Markup
from pytz import timezone
from werkzeug.exceptions import Forbidden, NotFound, BadRequest

from indico.core import signals
from indico.core.db import db
from indico.core.notifications import make_email
from indico.modules.users import User, logger
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.util import (get_related_categories, get_suggested_categories,
                                       serialize_user, search_users, merge_users)
from indico.modules.users.views import WPUserDashboard, WPUser, WPUsersAdmin
from indico.modules.users.forms import UserDetailsForm, UserPreferencesForm, UserEmailsForm, SearchForm, MergeForm
from indico.modules.auth.forms import LocalRegistrationForm
from indico.util.date_time import timedelta_split
from indico.util.event import truncate_path
from indico.util.i18n import _
from indico.util.redis import suggestions
from indico.util.redis import client as redis_client
from indico.util.redis import write_client as redis_write_client
from indico.util.signals import values_from_signal
from indico.util.string import make_unique_token
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults

from MaKaC.accessControl import AccessWrapper
from MaKaC.common.cache import GenericCache
from MaKaC.common.mail import GenericMailer
from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.conference import CategoryManager
from MaKaC.webinterface.rh.admins import RHAdminBase
from MaKaC.webinterface.rh.base import RHProtected

IDENTITY_ATTRIBUTES = {'first_name', 'last_name', 'email', 'affiliation', 'full_name'}
UserEntry = namedtuple('UserEntry', IDENTITY_ATTRIBUTES | {'profile_url'})


class RHUserBase(RHProtected):
    flash_user_status = True

    def _checkParams(self):
        if not session.user:
            return
        self.user = session.user
        if 'user_id' in request.view_args:
            self.user = User.get(request.view_args['user_id'])
            if self.user is None:
                raise NotFound('This user does not exist')
            elif request.method == 'GET' and not request.is_xhr and self.flash_user_status:
                # Show messages about the user's status if it's a simple GET request
                if self.user.is_deleted:
                    if self.user.merged_into_id is not None:
                        msg = _('This user has been merged into <a href="{url}">another user</a>.')
                        flash(Markup(msg).format(url=url_for(request.endpoint, self.user.merged_into_user)), 'warning')
                    else:
                        flash(_('This user is marked as deleted.'), 'warning')
                if self.user.is_pending:
                    flash(_('This user is marked as pending, i.e. it has been attached to something but never '
                            'logged in.'), 'warning')

    def _checkProtection(self):
        RHProtected._checkProtection(self)
        if not self._doProcess:  # not logged in
            return
        if not self.user.can_be_modified(session.user):
            raise Forbidden('You cannot modify this user.')


class RHUserDashboard(RHUserBase):
    def _process(self):
        if redis_write_client:
            suggestions.schedule_check(self.user)

        tz = timezone(DisplayTZ().getDisplayTZ())
        hours, minutes = timedelta_split(tz.utcoffset(datetime.now()))[:2]
        return WPUserDashboard.render_template('dashboard.html', redis_enabled=bool(redis_client), timezone=unicode(tz),
                                               offset='{:+03d}:{:02d}'.format(hours, minutes), user=self.user,
                                               categories=get_related_categories(self.user),
                                               suggested_categories=get_suggested_categories(self.user))


class RHPersonalData(RHUserBase):
    def _process(self):
        form = UserDetailsForm(obj=FormDefaults(self.user, skip_attrs={'title'}, title=self.user._title),
                               synced_fields=self.user.synced_fields, synced_values=self.user.synced_values)
        if form.validate_on_submit():
            self.user.synced_fields = form.synced_fields
            form.populate_obj(self.user, skip=self.user.synced_fields)
            self.user.synchronize_data(refresh=True)
            flash(_('Your personal data was successfully updated.'), 'success')
            return redirect(url_for('.user_profile'))
        return WPUser.render_template('personal_data.html', user=self.user, form=form)


class RHUserPreferences(RHUserBase):
    def _process(self):
        extra_preferences = [pref(self.user) for pref in values_from_signal(signals.users.preferences.send(self.user))]
        form_class = UserPreferencesForm
        defaults = FormDefaults(**self.user.settings.get_all(self.user))
        for pref in extra_preferences:
            form_class = pref.extend_form(form_class)
            pref.extend_defaults(defaults)
        form = form_class(obj=defaults)
        if form.validate_on_submit():
            data = form.data
            for pref in extra_preferences:
                pref.process_form_data(data)
            self.user.settings.set_multi(data)
            session.lang = self.user.settings.get('lang')
            session.timezone = (self.user.settings.get('timezone') if self.user.settings.get('force_timezone')
                                else 'LOCAL')
            flash(_('Preferences saved'), 'success')
            return redirect(url_for('.user_preferences'))
        return WPUser.render_template('preferences.html', user=self.user, form=form)


class RHUserFavorites(RHUserBase):
    def _process(self):
        categories = sorted([(cat, truncate_path(cat.getCategoryPathTitles()[:-1], chars=50))
                             for cat in self.user.favorite_categories], key=lambda c: (c[0].name, c[1]))
        return WPUser.render_template('favorites.html', user=self.user, favorite_categories=categories)


class RHUserFavoritesUsersAdd(RHUserBase):
    CSRF_ENABLED = True

    def _process(self):
        users = [User.get(int(id_)) for id_ in request.form.getlist('user_id')]
        self.user.favorite_users |= set(filter(None, users))
        tpl = get_template_module('users/_favorites.html')
        return jsonify(success=True, users=[serialize_user(user) for user in users],
                       html=tpl.favorite_users_list(self.user))


class RHUserFavoritesUserRemove(RHUserBase):
    CSRF_ENABLED = True

    def _process(self):
        user = User.get(int(request.view_args['fav_user_id']))
        if user in self.user.favorite_users:
            self.user.favorite_users.remove(user)
        return jsonify(success=True)


class RHUserFavoritesCategoryAPI(RHUserBase):
    CSRF_ENABLED = True

    def _process_PUT(self):
        category = CategoryManager().getById(request.view_args['category_id'])
        if category not in self.user.favorite_categories:
            if not category.canAccess(AccessWrapper(self.user.as_avatar)):
                raise Forbidden()
            self.user.favorite_categories.add(category)
            if redis_write_client:
                suggestions.unignore(self.user, 'category', category.getId())
                suggestions.unsuggest(self.user, 'category', category.getId())
        return jsonify(success=True)

    def _process_DELETE(self):
        category = CategoryManager().getById(request.view_args['category_id'])
        if category in self.user.favorite_categories:
            self.user.favorite_categories.remove(category)
            if redis_write_client:
                suggestions.unsuggest(self.user, 'category', category.getId())
        return jsonify(success=True)


class RHUserSuggestionsRemove(RHUserBase):
    CSRF_ENABLED = True

    def _process(self):
        suggestions.unsuggest(self.user, 'category', request.view_args['category_id'], True)
        return jsonify(success=True)


class RHUserEmails(RHUserBase):
    def _send_confirmation(self, email):
        token_storage = GenericCache('confirm-email')
        data = {'email': email, 'user_id': self.user.id}
        token = make_unique_token(lambda t: not token_storage.get(t))
        token_storage.set(token, data, 24 * 3600)
        GenericMailer.send(make_email(email, template=get_template_module('users/emails/verify_email.txt',
                                                                          user=self.user, email=email, token=token)))

    def _process(self):
        form = UserEmailsForm()
        if form.validate_on_submit():
            self._send_confirmation(form.email.data)
            flash(_("We have sent an email to {email}. Please click the link in that email within 24 hours to "
                    "confirm your new email address.").format(email=form.email.data), 'success')
            return redirect(url_for('.user_emails'))
        return WPUser.render_template('emails.html', user=self.user, form=form)


class RHUserEmailsVerify(RHUserBase):
    flash_user_status = False
    token_storage = GenericCache('confirm-email')

    def _validate(self, data):
        if not data:
            flash(_('The verification token is invalid or expired.'), 'error')
            return False, None
        user = User.get(data['user_id'])
        if not user or user != self.user:
            flash(_('This token is for a different Indico user. Please login with the correct account'), 'error')
            return False, None
        existing = UserEmail.find_first(is_user_deleted=False, email=data['email'])
        if existing and not existing.user.is_pending:
            if existing.user == self.user:
                flash(_('This email address is already attached to your account.'))
            else:
                flash(_('This email address is already in use by another account.'), 'error')
            return False, existing.user
        return True, existing.user if existing else None

    def _process(self):
        token = request.view_args['token']
        data = self.token_storage.get(token)
        valid, existing = self._validate(data)
        if valid:
            self.token_storage.delete(token)

            if existing and existing.is_pending:
                logger.info("Found pending user %s to be merged into %s", existing, self.user)
                merge_users(existing, self.user)
                flash(_("Merged data from existing '{}' identity").format(existing.email))
                existing.is_pending = False

            self.user.secondary_emails.add(data['email'])
            signals.users.email_added.send(self.user, email=data['email'])
            flash(_('The email address {email} has been added to your account.').format(email=data['email']), 'success')
        return redirect(url_for('.user_emails'))


class RHUserEmailsDelete(RHUserBase):
    CSRF_ENABLED = True

    def _process(self):
        email = request.view_args['email']
        if email in self.user.secondary_emails:
            self.user.secondary_emails.remove(email)
        return jsonify(success=True)


class RHUserEmailsSetPrimary(RHUserBase):
    CSRF_ENABLED = True

    def _process(self):
        email = request.form['email']
        if email in self.user.secondary_emails:
            self.user.make_email_primary(email)
            flash(_('Your primary email was updated successfully.'), 'success')
        return redirect(url_for('.user_emails'))


class RHUsersAdminSettings(RHAdminBase):
    """Admin users overview"""

    def _process(self):
        form = SearchForm(obj=FormDefaults(exact=True))
        form_data = form.data
        search_results = None
        num_of_users = User.query.count()
        num_deleted_users = User.find(is_deleted=True).count()
        if form.validate_on_submit():
            search_results = []
            exact = form_data.pop('exact')
            include_deleted = form_data.pop('include_deleted')
            include_pending = form_data.pop('include_pending')
            external = form_data.pop('external')
            form_data = {k: v for (k, v) in form_data.iteritems() if v and v.strip()}

            for entry in search_users(exact=exact, include_deleted=include_deleted,
                                      include_pending=include_pending, external=external, **form_data):
                if isinstance(entry, User):
                    search_results.append(UserEntry(profile_url=url_for('.user_profile', entry),
                                                    **{k: getattr(entry, k) for k in IDENTITY_ATTRIBUTES}))
                else:
                    search_results.append(UserEntry(
                        profile_url=None, full_name="{first_name} {last_name}".format(**entry.data.to_dict()),
                        **{k: entry.data.get(k) for k in (IDENTITY_ATTRIBUTES - {'full_name'})}))

            search_results.sort(key=attrgetter('first_name', 'last_name'))
        return WPUsersAdmin.render_template('users_admin.html', form=form, search_results=search_results,
                                            num_of_users=num_of_users, num_deleted_users=num_deleted_users)


class RHUsersAdminCreate(RHAdminBase):
    """Create user (admin)"""

    def _process(self):
        form = LocalRegistrationForm()
        return WPUsersAdmin.render_template('users_create.html', form=form)


def _get_merge_problems(source, target):
    errors = []
    warnings = []
    if source == target:
        errors.append(_("Users are the same!"))
    if (source.first_name.strip().lower() != target.first_name.strip().lower() or
            source.last_name.strip().lower() != target.last_name.strip().lower()):
        warnings.append(_("Users' names seem to be different!"))
    if source.is_pending:
        warnings.append(_("Source user has never logged in to Indico!"))
    if target.is_pending:
        warnings.append(_("Target user has never logged in to Indico!"))
    if source.is_deleted:
        errors.append(_("Source user has been deleted!"))
    if target.is_deleted:
        errors.append(_("Target user has been deleted!"))
    if source.is_admin:
        warnings.append(_("Source user is an administrator!"))
    if target.is_admin:
        warnings.append(_("Target user is an administrator!"))
    if source.is_admin and not target.is_admin:
        errors.append(_("Source user is an administrator but target user isn't!"))
    return errors, warnings


class RHUsersAdminMerge(RHAdminBase):
    """Merge users (admin)"""

    def _process(self):
        form = MergeForm()
        if form.validate_on_submit():
            source = form.source_user.data
            target = form.target_user.data
            errors, warnings = _get_merge_problems(source, target)
            if errors:
                raise BadRequest(_('Merge aborted due to failed sanity check'))
            if warnings:
                logger.info("User %s initiated merge of %s into %s (with %d warnings)",
                            session.user, source, target, len(warnings))
            else:
                logger.info("User %s initiated merge of %s into %s", session.user, source, target)
            merge_users(source, target)
            flash(_('The users have been successfully merged.'), 'success')
            return redirect(url_for('.user_profile', user_id=target.id))

        return WPUsersAdmin.render_template('users_merge.html', form=form)


class RHUsersAdminMergeCheck(RHAdminBase):
    def _process(self):
        source = User.get_one(request.args['source'])
        target = User.get_one(request.args['target'])
        errors, warnings = _get_merge_problems(source, target)
        return jsonify(errors=errors, warnings=warnings)
