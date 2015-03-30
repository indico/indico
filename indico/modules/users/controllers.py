# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from datetime import datetime

from flask import session, request, flash, jsonify, redirect
from pytz import timezone
from werkzeug.exceptions import Forbidden, NotFound

from indico.core import signals
from indico.core.notifications import make_email
from indico.modules.users import User
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.util import get_related_categories, get_suggested_categories
from indico.modules.users.views import WPUserDashboard, WPUser
from indico.modules.users.forms import UserDetailsForm, UserPreferencesForm, UserEmailsForm
from indico.util.date_time import timedelta_split
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
from MaKaC.webinterface.rh.base import RHProtected


class RHUserBase(RHProtected):
    def _checkParams(self):
        if not session.user:
            return
        self.user = session.new_user
        if 'user_id' in request.view_args:
            self.user = User.get(request.view_args['user_id'])
            if self.user is None:
                raise NotFound('This user does not exist')

    def _checkProtection(self):
        RHProtected._checkProtection(self)
        if not self._doProcess:  # not logged in
            return
        if not self.user.can_be_modified(session.new_user):
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
        form = UserDetailsForm(obj=FormDefaults(self.user, skip_attrs={'title'}, title=self.user._title))
        if form.validate_on_submit():
            form.populate_obj(self.user)
            flash(_('Your account details were successfully updated.'), 'success')
            return redirect(url_for('.user_profile'))
        return WPUser.render_template('account.html', user=self.user, form=form)


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
            flash(_('Preferences saved'), 'success')
            return redirect(url_for('.user_preferences'))
        return WPUser.render_template('preferences.html', user=self.user, form=form)


class RHUserFavorites(RHUserBase):
    def _process(self):
        return WPUser.render_template('favorites.html', user=self.user)


class RHUserFavoritesUsersAdd(RHUserBase):
    def _process(self):
        users = [User.get(int(id_)) for id_ in request.form.getlist('user_id')]
        self.user.favorite_users |= set(filter(None, users))
        tpl = get_template_module('users/_favorites.html')
        return jsonify(success=True, html=tpl.favorite_users_list(self.user))


class RHUserFavoritesUserRemove(RHUserBase):
    def _process(self):
        user = User.get(int(request.view_args['fav_user_id']))
        if user in self.user.favorite_users:
            self.user.favorite_users.remove(user)
        return jsonify(success=True)


class RHUserFavoritesCategoryAPI(RHUserBase):
    def _process_PUT(self):
        category = CategoryManager().getById(request.view_args['category_id'])
        if category not in self.user.favorite_categories:
            # TODO: enable once there's a user.avatar property returning a wrapper with Avatar-style methods
            # if not category.canAccess(AccessWrapper(self.user.avatar, request.remote_addr)):
            #     raise Forbidden()
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
    token_storage = GenericCache('confirm-email')

    def _validate(self, data):
        if not data:
            flash(_('The verification token is invalid or expired.'), 'error')
            return False
        user = User.get(data['user_id'])
        if not user or user != self.user:
            flash(_('This token is for a different Indico user. Please login with the correct account'), 'error')
            return False
        existing = UserEmail.find_first(is_user_deleted=False, email=data['email'])
        if existing:
            if existing.user == self.user:
                flash(_('This email address is already attached to your account.'))
            else:
                flash(_('This email address is already in use by another account.'), 'error')
            return False
        return True

    def _process(self):
        token = request.view_args['token']
        data = self.token_storage.get(token)
        if self._validate(data):
            self.token_storage.delete(token)
            self.user.secondary_emails.add(data['email'])
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
