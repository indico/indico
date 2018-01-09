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

from __future__ import unicode_literals

from collections import namedtuple
from datetime import datetime
from operator import attrgetter

from dateutil.relativedelta import relativedelta
from flask import flash, jsonify, redirect, request, session
from markupsafe import Markup, escape
from sqlalchemy.orm import joinedload, load_only, subqueryload, undefer
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import get_n_matching
from indico.core.notifications import make_email, send_email
from indico.legacy.common.cache import GenericCache
from indico.modules.admin import RHAdminBase
from indico.modules.auth import Identity
from indico.modules.auth.models.registration_requests import RegistrationRequest
from indico.modules.auth.util import register_user
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.users import User, logger, user_management_settings
from indico.modules.users.forms import (AdminAccountRegistrationForm, AdminsForm, AdminUserSettingsForm, MergeForm,
                                        SearchForm, UserDetailsForm, UserEmailsForm, UserPreferencesForm)
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.operations import create_user
from indico.modules.users.util import (get_linked_events, get_related_categories, get_suggested_categories, merge_users,
                                       search_users, serialize_user)
from indico.modules.users.views import WPUser, WPUsersAdmin
from indico.util.date_time import now_utc, timedelta_split
from indico.util.event import truncate_path
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.util.string import make_unique_token
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import RHProtected
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


IDENTITY_ATTRIBUTES = {'first_name', 'last_name', 'email', 'affiliation', 'full_name'}
UserEntry = namedtuple('UserEntry', IDENTITY_ATTRIBUTES | {'profile_url', 'user'})


class RHUserBase(RHProtected):
    flash_user_status = True
    allow_system_user = False

    def _process_args(self):
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
        if not self.allow_system_user and self.user.is_system:
            return redirect(url_for('users.user_profile'))

    def _check_access(self):
        RHProtected._check_access(self)
        if not self.user.can_be_modified(session.user):
            raise Forbidden('You cannot modify this user.')


class RHUserDashboard(RHUserBase):
    management_roles = {'conference_creator', 'conference_chair', 'conference_manager', 'session_manager',
                        'session_coordinator', 'contribution_manager'}
    reviewer_roles = {'paper_manager', 'paper_judge', 'paper_content_reviewer', 'paper_layout_reviewer',
                      'contribution_referee', 'contribution_editor', 'contribution_reviewer', 'abstract_reviewer',
                      'track_convener'}
    attendance_roles = {'contributor', 'contribution_submission', 'abstract_submitter', 'abstract_person',
                        'registration_registrant', 'survey_submitter', 'lecture_speaker'}

    def _process(self):
        self.user.settings.set('suggest_categories', True)
        tz = session.tzinfo
        hours, minutes = timedelta_split(tz.utcoffset(datetime.now()))[:2]
        categories = get_related_categories(self.user)
        categories_events = []
        if categories:
            category_ids = {c['categ'].id for c in categories.itervalues()}
            today = now_utc(False).astimezone(tz).date()
            query = (Event.query
                     .filter(~Event.is_deleted,
                             Event.category_chain_overlaps(category_ids),
                             Event.start_dt.astimezone(session.tzinfo) >= today)
                     .options(joinedload('category').load_only('id', 'title'),
                              joinedload('series'),
                              subqueryload('acl_entries'),
                              load_only('id', 'category_id', 'start_dt', 'end_dt', 'title', 'access_key',
                                        'protection_mode', 'series_id', 'series_pos', 'series_count'))
                     .order_by(Event.start_dt, Event.id))
            categories_events = get_n_matching(query, 10, lambda x: x.can_access(self.user))
        from_dt = now_utc(False) - relativedelta(weeks=1, hour=0, minute=0, second=0)
        linked_events = [(event, {'management': bool(roles & self.management_roles),
                                  'reviewing': bool(roles & self.reviewer_roles),
                                  'attendance': bool(roles & self.attendance_roles)})
                         for event, roles in get_linked_events(self.user, from_dt, 10).iteritems()]
        return WPUser.render_template('dashboard.html', 'dashboard',
                                      offset='{:+03d}:{:02d}'.format(hours, minutes), user=self.user,
                                      categories=categories,
                                      categories_events=categories_events,
                                      suggested_categories=get_suggested_categories(self.user),
                                      linked_events=linked_events)


class RHPersonalData(RHUserBase):
    allow_system_user = True

    def _process(self):
        form = UserDetailsForm(obj=FormDefaults(self.user, skip_attrs={'title'}, title=self.user._title),
                               synced_fields=self.user.synced_fields, synced_values=self.user.synced_values)
        if form.validate_on_submit():
            self.user.synced_fields = form.synced_fields
            form.populate_obj(self.user, skip=self.user.synced_fields)
            self.user.synchronize_data(refresh=True)
            flash(_('Your personal data was successfully updated.'), 'success')
            return redirect(url_for('.user_profile'))
        return WPUser.render_template('personal_data.html', 'personal_data', user=self.user, form=form)


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
        return WPUser.render_template('preferences.html', 'preferences', user=self.user, form=form)


class RHUserFavorites(RHUserBase):
    def _process(self):
        query = (Category.query
                 .filter(Category.id.in_(c.id for c in self.user.favorite_categories))
                 .options(undefer('chain_titles')))
        categories = sorted([(cat, truncate_path(cat.chain_titles[:-1], chars=50)) for cat in query],
                            key=lambda c: (c[0].title, c[1]))
        return WPUser.render_template('favorites.html', 'favorites', user=self.user, favorite_categories=categories)


class RHUserFavoritesUsersAdd(RHUserBase):
    def _process(self):
        users = [User.get(int(id_)) for id_ in request.form.getlist('user_id')]
        self.user.favorite_users |= set(filter(None, users))
        tpl = get_template_module('users/_favorites.html')
        return jsonify(success=True, users=[serialize_user(user) for user in users],
                       html=tpl.favorite_users_list(self.user))


class RHUserFavoritesUserRemove(RHUserBase):
    def _process(self):
        user = User.get(int(request.view_args['fav_user_id']))
        self.user.favorite_users.discard(user)
        try:
            db.session.flush()
        except StaleDataError:
            # Deleted in another transaction
            db.session.rollback()
        return jsonify(success=True)


class RHUserFavoritesCategoryAPI(RHUserBase):
    def _process_args(self):
        RHUserBase._process_args(self)
        self.category = Category.get_one(request.view_args['category_id'])
        self.suggestion = self.user.suggested_categories.filter_by(category=self.category).first()

    def _process_PUT(self):
        if self.category not in self.user.favorite_categories:
            if not self.category.can_access(self.user):
                raise Forbidden()
            self.user.favorite_categories.add(self.category)
            if self.suggestion:
                self.user.suggested_categories.remove(self.suggestion)
        return jsonify(success=True)

    def _process_DELETE(self):
        if self.category in self.user.favorite_categories:
            self.user.favorite_categories.discard(self.category)
            try:
                db.session.flush()
            except StaleDataError:
                # Deleted in another transaction
                db.session.rollback()
            suggestion = self.user.suggested_categories.filter_by(category=self.category).first()
            if suggestion:
                self.user.suggested_categories.remove(suggestion)
        return jsonify(success=True)


class RHUserSuggestionsRemove(RHUserBase):
    def _process(self):
        suggestion = self.user.suggested_categories.filter_by(category_id=request.view_args['category_id']).first()
        if suggestion:
            suggestion.is_ignored = True
        return jsonify(success=True)


class RHUserEmails(RHUserBase):
    def _send_confirmation(self, email):
        token_storage = GenericCache('confirm-email')
        data = {'email': email, 'user_id': self.user.id}
        token = make_unique_token(lambda t: not token_storage.get(t))
        token_storage.set(token, data, 24 * 3600)
        send_email(make_email(email, template=get_template_module('users/emails/verify_email.txt',
                                                                  user=self.user, email=email, token=token)))

    def _process(self):
        form = UserEmailsForm()
        if form.validate_on_submit():
            self._send_confirmation(form.email.data)
            flash(_("We have sent an email to {email}. Please click the link in that email within 24 hours to "
                    "confirm your new email address.").format(email=form.email.data), 'success')
            return redirect(url_for('.user_emails'))
        return WPUser.render_template('emails.html', 'emails', user=self.user, form=form)


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

                # If the pending user has missing names, copy them from the active one
                # to allow it to be marked as not pending and deleted during the merge.
                existing.first_name = existing.first_name or self.user.first_name
                existing.last_name = existing.last_name or self.user.last_name

                merge_users(existing, self.user)
                flash(_("Merged data from existing '{}' identity").format(existing.email))
                existing.is_pending = False

            self.user.secondary_emails.add(data['email'])
            signals.users.email_added.send(self.user, email=data['email'])
            flash(_('The email address {email} has been added to your account.').format(email=data['email']), 'success')
        return redirect(url_for('.user_emails'))


class RHUserEmailsDelete(RHUserBase):
    def _process(self):
        email = request.view_args['email']
        if email in self.user.secondary_emails:
            self.user.secondary_emails.remove(email)
        return jsonify(success=True)


class RHUserEmailsSetPrimary(RHUserBase):
    def _process(self):
        email = request.form['email']
        if email in self.user.secondary_emails:
            self.user.make_email_primary(email)
            flash(_('Your primary email was updated successfully.'), 'success')
        return redirect(url_for('.user_emails'))


class RHAdmins(RHAdminBase):
    """Show Indico administrators"""

    def _process(self):
        admins = set(User.query
                     .filter_by(is_admin=True, is_deleted=False)
                     .order_by(db.func.lower(User.first_name), db.func.lower(User.last_name)))

        form = AdminsForm(admins=admins)
        if form.validate_on_submit():
            added = form.admins.data - admins
            removed = admins - form.admins.data
            for user in added:
                user.is_admin = True
                logger.warn('Admin rights granted to %r by %r [%s]', user, session.user, request.remote_addr)
                flash(_('Admin added: {name} ({email})').format(name=user.name, email=user.email), 'success')
            for user in removed:
                user.is_admin = False
                logger.warn('Admin rights revoked from %r by %r [%s]', user, session.user, request.remote_addr)
                flash(_('Admin removed: {name} ({email})').format(name=user.name, email=user.email), 'success')
            return redirect(url_for('.admins'))

        return WPUsersAdmin.render_template('admins.html', 'admins', form=form)


class RHUsersAdmin(RHAdminBase):
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
            matches = search_users(exact=exact, include_deleted=include_deleted, include_pending=include_pending,
                                   external=external, allow_system_user=True, **form_data)
            for entry in matches:
                if isinstance(entry, User):
                    search_results.append(UserEntry(
                        profile_url=url_for('.user_profile', entry),
                        user=entry,
                        **{k: getattr(entry, k) for k in IDENTITY_ATTRIBUTES}
                    ))
                else:
                    search_results.append(UserEntry(
                        profile_url=None,
                        user=None,
                        full_name="{first_name} {last_name}".format(**entry.data.to_dict()),
                        **{k: entry.data.get(k) for k in (IDENTITY_ATTRIBUTES - {'full_name'})}
                    ))
            search_results.sort(key=attrgetter('first_name', 'last_name'))

        num_reg_requests = RegistrationRequest.query.count()
        return WPUsersAdmin.render_template('users_admin.html', 'users', form=form, search_results=search_results,
                                            num_of_users=num_of_users, num_deleted_users=num_deleted_users,
                                            num_reg_requests=num_reg_requests)


class RHUsersAdminSettings(RHAdminBase):
    """Manage global suer-related settings."""

    def _process(self):
        form = AdminUserSettingsForm(obj=FormDefaults(**user_management_settings.get_all()))
        if form.validate_on_submit():
            user_management_settings.set_multi(form.data)
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHUsersAdminCreate(RHAdminBase):
    """Create user (admin)"""

    def _process(self):
        form = AdminAccountRegistrationForm()
        if form.validate_on_submit():
            data = form.data
            if data.pop('create_identity', False):
                identity = Identity(provider='indico', identifier=data.pop('username'), password=data.pop('password'))
            else:
                identity = None
                data.pop('username', None)
                data.pop('password', None)
            user = create_user(data.pop('email'), data, identity, from_moderation=True)
            msg = Markup('{} <a href="{}">{}</a>').format(
                escape(_('The account has been created.')),
                url_for('users.user_profile', user),
                escape(_('Show details'))
            )
            flash(msg, 'success')
            return jsonify_data()
        return jsonify_template('users/users_admin_create.html', form=form)


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

        return WPUsersAdmin.render_template('users_merge.html', 'users', form=form)


class RHUsersAdminMergeCheck(RHAdminBase):
    def _process(self):
        source = User.get_one(request.args['source'])
        target = User.get_one(request.args['target'])
        errors, warnings = _get_merge_problems(source, target)
        return jsonify(errors=errors, warnings=warnings)


class RHRegistrationRequestList(RHAdminBase):
    """List all registration requests"""

    def _process(self):
        requests = RegistrationRequest.query.order_by(RegistrationRequest.email).all()
        return WPUsersAdmin.render_template('registration_requests.html', 'users', pending_requests=requests)


class RHRegistrationRequestBase(RHAdminBase):
    """Base class to process a registration request"""

    def _process_args(self):
        RHAdminBase._process_args(self)
        self.request = RegistrationRequest.get_one(request.view_args['request_id'])


class RHAcceptRegistrationRequest(RHRegistrationRequestBase):
    """Accept a registration request"""

    def _process(self):
        user, identity = register_user(self.request.email, self.request.extra_emails, self.request.user_data,
                                       self.request.identity_data, self.request.settings)
        tpl = get_template_module('users/emails/registration_request_accepted.txt', user=user)
        send_email(make_email(self.request.email, template=tpl))
        flash(_('The request has been approved.'), 'success')
        return jsonify_data()


class RHRejectRegistrationRequest(RHRegistrationRequestBase):
    """Reject a registration request"""

    def _process(self):
        db.session.delete(self.request)
        tpl = get_template_module('users/emails/registration_request_rejected.txt', req=self.request)
        send_email(make_email(self.request.email, template=tpl))
        flash(_('The request has been rejected.'), 'success')
        return jsonify_data()
