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

from flask import flash, redirect, session

from indico.modules.events.contributions.models.persons import (ContributionPersonLink, SubContributionPersonLink,
                                                                AuthorType)
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.management.forms import EventProtectionForm
from indico.modules.events.management.util import can_lock
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.operations import update_event
from indico.modules.events.util import get_object_from_args, update_object_principals
from indico.util.i18n import _
from indico.web.flask.util import url_for, jsonify_data
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template

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
            redirect_url = url_for('categories.manage_content', category)
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


class RHShowNonInheriting(RHConferenceModifBase):
    """Show a list of non-inheriting child objects"""

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.obj = get_object_from_args()[2]
        if self.obj is None:
            raise NotFound

    def _process(self):
        objects = self.obj.get_non_inheriting_objects()
        return jsonify_template('events/management/non_inheriting_objects.html', objects=objects)


class RHEventProtection(RHConferenceModifBase):
    """Show event protection"""

    def _process(self):
        form = EventProtectionForm(obj=FormDefaults(**self._get_defaults()), event=self.event_new)
        if form.validate_on_submit():
            update_event(self.event_new, {'protection_mode': form.protection_mode.data})
            self.event_new.as_legacy.setAccessKey(form.access_key.data)
            if self.event_new.is_self_protected:
                update_object_principals(self.event_new, form.acl.data, read_access=True)
            update_object_principals(self.event_new, form.managers.data, full_access=True)
            update_object_principals(self.event_new, form.registration_managers.data, role='registration')
            flash(_('Protection settings have been updated'), 'success')
            return redirect(url_for('.protection', self.event_new))
        return WPEventManagement.render_template('event_protection.html', self._conf, form=form, event=self.event_new)

    def _get_defaults(self):
        acl = {p.principal for p in self.event_new.acl_entries if p.read_access}
        managers = {p.principal for p in self.event_new.acl_entries if p.full_access}
        registration_managers = {p.principal for p in self.event_new.acl_entries
                                 if p.has_management_role('registration', explicit=True)}
        return dict({'protection_mode': self.event_new.protection_mode, 'acl': acl, 'managers': managers,
                     'registration_managers': registration_managers,
                     'access_key': self.event_new.as_legacy.getAccessKey()})



class RHGrantSubmissionRights(RHConferenceModifBase):
    """Grants submission rights to all contribution speakers"""

    def _process(self):
        for cont in self._target.as_event.contributions:
            speakers = cont.speakers[:]
            for subcontrib in cont.subcontributions:
                speakers += subcontrib.speakers
            for speaker in speakers:
                principal = speaker.person.principal
                if principal:
                    cont.update_principal(principal, add_roles={'submit'})
                    self.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Protection',
                                       'Speaker {} has been granted with submission privileges'.format(principal),
                                       session.user)
        flash(_('Submission rights have been granted to contribution speakers'))
        return jsonify_data()


class RHGrantModificationRights(RHConferenceModifBase):
    """Grants session modification rights to all session conveners"""

    def _process(self):
        for sess in self.event_new.sessions:
            for convener in sess.conveners:
                principal = convener.person.principal
                if principal:
                    sess.update_principal(principal, full_access=True)
                    log_msg = ('Session convener {} has been granted with modification privileges to session {}'
                               .format(principal, sess))
                    self.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Protection', log_msg,
                                       session.user)
        flash(_('Session modification rights have been granted to session conveners'))
        return jsonify_data()


class RHRevokeSubmissionRights(RHConferenceModifBase):
    """Revokes submission rights"""

    def _process(self):
        for cont in self.event_new.contributions:
            for entry in set(cont.acl_entries):
                cont.update_principal(entry.principal, del_roles={'submit'})
                self.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Protection',
                                   'Submission privileges has been revoked from {} in {}'.format(entry.principal, cont),
                                   session.user)
        for entry in set(self.event_new.acl_entries):
            self.event_new.update_principal(entry.principal, del_roles={'submit'})
            self.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Protection',
                               'Submission privileges has been revoked from event submitter {}'.format(entry.principal),
                               session.user)
        flash(_('Submission rights have been revoked'))
        return jsonify_data()
