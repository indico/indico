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

from indico.modules.users import User
from indico.modules.users.util import get_related_categories, get_suggested_categories
from indico.modules.users.views import WPUserDashboard, WPUser
from indico.modules.users.forms import UserDetailsForm, UserPreferencesForm, UserEmailsForm
from indico.util.date_time import timedelta_split
from indico.util.i18n import _
from indico.util.redis import suggestions
from indico.util.redis import client as redis_client
from indico.util.redis import write_client as redis_write_client
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.accessControl import AccessWrapper
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


class RHUserAccount(RHUserBase):
    def _process(self):
        form = UserDetailsForm()
        return WPUser.render_template('account.html', user=self.user, form=form)


class RHUserPreferences(RHUserBase):
    def _process(self):
        defaults = FormDefaults(**self.user.settings.get_all(self.user))
        form = UserPreferencesForm(obj=defaults)
        if form.validate_on_submit():
            self.user.settings.set_multi(form.data)
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
            # TODO: enable with a LegacyAvatarWrapper(self.user) once we have it
            # if not category.canAccess(AccessWrapper(self.user, request.remote_addr)):
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


class RHUserEmails(RHUserBase):
    def _process(self):
        form = UserEmailsForm()
        if form.validate_on_submit():
            email = form.email.data
            if email != self.user.email and email not in self.user.secondary_emails:
                self.user.secondary_emails.append(email)
                form.email.data = None
                flash(_('Your email was successfully added in your secondary emails. If you wish to make it your '
                        'primary email, click on the button Set as primary next to it.'), 'success')
            else:
                flash(_('This email already exists.'), 'warning')
        return WPUser.render_template('emails.html', user=self.user, form=form)


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
