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

from collections import defaultdict

from flask import flash, redirect, request, session
from werkzeug.exceptions import Forbidden

from indico.core.notifications import make_email, send_email
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import (ContributionPersonLink, SubContributionPersonLink,
                                                                AuthorType)
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.management.util import can_lock
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.forms import EmailEventPersonsForm
from indico.util.i18n import _, ngettext
from indico.web.flask.util import url_for, jsonify_data
from indico.web.util import jsonify_form, jsonify_template

from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHDeleteEvent(RHConferenceModifBase):
    """Delete an event."""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)

    def _process_GET(self):
        return jsonify_template('events/management/delete_event.html', event=self._conf)

    def _process_POST(self):
        category = self._conf.getOwner()
        self._conf.delete(session.user)
        flash(_('Event "{}" successfully deleted.').format(self._conf.title), 'success')

        if category:
            redirect_url = url_for('category_mgmt.categoryModification', category)
        else:
            redirect_url = url_for('misc.index')

        return jsonify_data(url=redirect_url, flash=False)


class RHLockEvent(RHConferenceModifBase):
    """Lock an event."""

    CSRF_ENABLED = True

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        if not can_lock(self._conf, session.user):
            raise Forbidden

    def _process(self):
        return RH._process(self)

    def _process_GET(self):
        return jsonify_template('events/management/lock_event.html', event=self._conf)

    def _process_POST(self):
        self._conf.setClosed(True)
        flash(_('The event is now locked.'), 'success')
        return jsonify_data(url=url_for('event_mgmt.conferenceModification', self._conf), flash=False)


class RHUnlockEvent(RHConferenceModifBase):
    """Unlock an event."""

    CSRF_ENABLED = True

    def _checkProtection(self):
        self._allowClosed = can_lock(self._conf, session.user)
        RHConferenceModifBase._checkProtection(self)

    def _process(self):
        self._conf.setClosed(False)
        flash(_('The event is now unlocked.'), 'success')
        return redirect(url_for('event_mgmt.conferenceModification', self._conf))


class RHContributionPersonListMixin:
    """List of persons somehow related to contributions (co-authors, speakers...)"""

    @property
    def _membership_filter(self):
        raise NotImplementedError

    def _process(self):
        contribution_persons = (ContributionPersonLink
                                .find(ContributionPersonLink.contribution.has(self._membership_filter))
                                .all())
        contribution_persons.extend(SubContributionPersonLink
                                    .find(SubContributionPersonLink.subcontribution
                                          .has(SubContribution.contribution.has(self._membership_filter)))
                                    .all())

        contribution_persons_dict = defaultdict(lambda: {'speaker': False, 'primary_author': False,
                                                         'secondary_author': False})
        for contrib_person in contribution_persons:
            person_roles = contribution_persons_dict[contrib_person.person]
            person_roles['speaker'] |= contrib_person.is_speaker
            person_roles['primary_author'] |= contrib_person.author_type == AuthorType.primary
            person_roles['secondary_author'] |= contrib_person.author_type == AuthorType.secondary
        return jsonify_template('events/management/contribution_person_list.html',
                                event_persons=contribution_persons_dict, event=self.event_new)


class RHEmailEventPersons(RHConferenceModifBase):
    """Send emails to selected EventPersons"""

    def _checkParams(self, params):
        self._doNotSanitizeFields.append('from_address')
        RHConferenceModifBase._checkParams(self, params)

    def _process(self):
        person_ids = request.form.getlist('person_id')
        recipients = {p.email for p in self._find_event_persons(person_ids) if p.email}
        form = EmailEventPersonsForm(person_id=person_ids, recipients=', '.join(recipients))
        if form.validate_on_submit():
            for recipient in recipients:
                email = make_email(to_list=recipient, from_address=form.from_address.data,
                                   subject=form.subject.data, body=form.body.data, html=True)
                send_email(email, self.event_new, 'Event Persons')
            num = len(recipients)
            flash(ngettext('Your email has been sent.', '{} emails have been sent.', num).format(num))
            return jsonify_data()
        return jsonify_form(form, submit=_('Send'))

    def _find_event_persons(self, person_ids):
        return (self.event_new.persons
                .filter(EventPerson.id.in_(person_ids), EventPerson.email != '')
                .all())
