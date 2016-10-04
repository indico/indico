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

from operator import attrgetter

from flask import flash, request, jsonify, redirect, session
from sqlalchemy.orm import undefer
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import render_acl, ProtectionMode
from indico.modules.attachments.controllers.event_package import AttachmentPackageGeneratorMixin
from indico.modules.events.abstracts.forms import AbstractContentSettingsForm
from indico.modules.events.abstracts.settings import abstracts_settings
from indico.modules.events.contributions import get_contrib_field_types
from indico.modules.events.contributions.forms import (ContributionProtectionForm, SubContributionForm,
                                                       ContributionStartDateForm, ContributionDurationForm,
                                                       ContributionTypeForm)
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionField
from indico.modules.events.contributions.models.references import ContributionReference, SubContributionReference
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.contributions.operations import (create_contribution, update_contribution,
                                                            delete_contribution, create_subcontribution,
                                                            update_subcontribution, delete_subcontribution)
from indico.modules.events.contributions.util import (ContributionListGenerator, contribution_type_row,
                                                      make_contribution_form, generate_spreadsheet_from_contributions)
from indico.modules.events.contributions.views import WPManageContributions
from indico.modules.events.logs import EventLogRealm, EventLogKind
from indico.modules.events.management.controllers import RHContributionPersonListMixin
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.sessions import Session
from indico.modules.events.timetable.operations import update_timetable_entry
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.util import update_object_principals, track_time_changes, get_field_values
from indico.util.date_time import format_datetime, format_human_timedelta
from indico.util.i18n import _, ngettext
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.util.string import handle_legacy_description
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for, send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template
from MaKaC.PDFinterface.conference import ContribsToPDF, ContributionBook
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


def _render_subcontribution_list(contrib):
    tpl = get_template_module('events/contributions/management/_subcontribution_list.html')
    subcontribs = (SubContribution.query.with_parent(contrib)
                   .options(undefer('attachment_count'))
                   .order_by(SubContribution.position)
                   .all())
    return tpl.render_subcontribution_list(contrib.event_new, contrib, subcontribs)


class RHManageContributionsBase(RHConferenceModifBase):
    """Base class for all contributions management RHs"""
    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.list_generator = ContributionListGenerator(event=self.event_new)

    def _process(self):
        return RH._process(self)


class RHManageContributionBase(RHManageContributionsBase):
    """Base class for a specific contribution"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        }
    }

    def _checkParams(self, params):
        RHManageContributionsBase._checkParams(self, params)
        self.contrib = Contribution.find_one(id=request.view_args['contrib_id'], is_deleted=False)

    def _checkProtection(self):
        if not self.contrib.can_manage(session.user):
            raise Forbidden


class RHManageSubContributionBase(RHManageContributionBase):
    """Base RH for a specific subcontribution"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.subcontrib
        }
    }

    def _checkParams(self, params):
        RHManageContributionBase._checkParams(self, params)
        self.subcontrib = SubContribution.get_one(request.view_args['subcontrib_id'], is_deleted=False)


class RHManageContributionsActionsBase(RHManageContributionsBase):
    """Base class for classes performing actions on event contributions"""

    def _checkParams(self, params):
        RHManageContributionsBase._checkParams(self, params)
        ids = {int(x) for x in request.form.getlist('contribution_id')}
        self.contribs = Contribution.query.with_parent(self.event_new).filter(Contribution.id.in_(ids)).all()


class RHManageSubContributionsActionsBase(RHManageContributionBase):
    """Base class for RHs performing actions on subcontributions"""

    def _checkParams(self, params):
        RHManageContributionBase._checkParams(self, params)
        ids = {int(x) for x in request.form.getlist('subcontribution_id')}
        self.subcontribs = (SubContribution.query
                            .with_parent(self.contrib)
                            .filter(SubContribution.id.in_(ids))
                            .all())


class RHContributions(RHManageContributionsBase):
    """Display contributions management page"""

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        contrib_list_args = self.list_generator.get_list_kwargs()
        selected_entry = request.args.get('selected')
        selected_entry = int(selected_entry) if selected_entry else None
        return WPManageContributions.render_template('management/contributions.html', self._conf, event=self.event_new,
                                                     selected_entry=selected_entry, **contrib_list_args)


class RHContributionListCustomize(RHManageContributionsBase):
    """Filter options for the contributions list of an event"""

    def _process_GET(self):
        return WPManageContributions.render_template('contrib_list_filter.html', self._conf,
                                                     event=self.event_new,
                                                     filters=self.list_generator.list_config['filters'],
                                                     static_items=self.list_generator.static_items)

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(**self.list_generator.render_list())


class RHContributionListStaticURL(RHManageContributionsBase):
    """Generate a static URL for the configuration of the contribution list"""

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHCreateContribution(RHManageContributionsBase):
    def _process(self):
        inherited_location = self.event_new.location_data
        inherited_location['inheriting'] = True
        contrib_form_class = make_contribution_form(self.event_new)
        form = contrib_form_class(obj=FormDefaults(location_data=inherited_location), event=self.event_new)
        if form.validate_on_submit():
            contrib = create_contribution(self.event_new, *get_field_values(form.data))
            flash(_("Contribution '{}' created successfully").format(contrib.title), 'success')
            tpl_components = self.list_generator.render_list(contrib)
            if tpl_components['hide_contrib']:
                self.list_generator.flash_info_message(contrib)
            return jsonify_data(**tpl_components)
        return jsonify_template('events/contributions/forms/contribution.html', form=form)


class RHEditContribution(RHManageContributionBase):
    def _process(self):
        contrib_form_class = make_contribution_form(self.event_new)
        custom_field_values = {'custom_{}'.format(x.contribution_field_id): x.data for x in self.contrib.field_values}
        parent_session_block = (self.contrib.timetable_entry.parent.session_block
                                if (self.contrib.timetable_entry and self.contrib.timetable_entry.parent) else None)
        form = contrib_form_class(obj=FormDefaults(self.contrib, start_date=self.contrib.start_dt,
                                                   **custom_field_values),
                                  event=self.event_new, contrib=self.contrib, session_block=parent_session_block)
        if form.validate_on_submit():
            with track_time_changes():
                update_contribution(self.contrib, *get_field_values(form.data))
            flash(_("Contribution '{}' successfully updated").format(self.contrib.title), 'success')
            tpl_components = self.list_generator.render_list(self.contrib)
            if tpl_components['hide_contrib']:
                self.list_generator.flash_info_message(self.contrib)
            return jsonify_data(**tpl_components)
        elif not form.is_submitted():
            handle_legacy_description(form.description, self.contrib)
        self.commit = False
        return jsonify_template('events/contributions/forms/contribution.html', form=form)


class RHDeleteContributions(RHManageContributionsActionsBase):
    def _process(self):
        for contrib in self.contribs:
            delete_contribution(contrib)
        deleted_count = len(self.contribs)
        flash(ngettext("The contribution has been deleted.",
                       "{count} contributions have been deleted.", deleted_count)
              .format(count=deleted_count), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHContributionACL(RHManageContributionBase):
    """Display the ACL of the contribution"""

    def _process(self):
        return render_acl(self.contrib)


class RHContributionACLMessage(RHManageContributionBase):
    """Render the inheriting ACL message"""

    def _process(self):
        mode = ProtectionMode[request.args['mode']]
        return jsonify_template('forms/protection_field_acl_message.html', object=self.contrib, mode=mode,
                                endpoint='contributions.acl')


class RHContributionREST(RHManageContributionBase):
    def _process_DELETE(self):
        delete_contribution(self.contrib)
        flash(_("Contribution '{}' successfully deleted").format(self.contrib.title), 'success')
        return jsonify_data(**self.list_generator.render_list())

    def _process_PATCH(self):
        data = request.json
        updates = {}
        if data.viewkeys() > {'session_id', 'track_id'}:
            raise BadRequest
        if 'session_id' in data:
            updates.update(self._get_contribution_session_updates(data['session_id']))
        if 'track_id' in data:
            updates.update(self._get_contribution_track_updates(data['track_id']))
        rv = {}
        if updates:
            rv = update_contribution(self.contrib, updates)
        return jsonify(unscheduled=rv.get('unscheduled', False), undo_unschedule=rv.get('undo_unschedule'))

    def _get_contribution_session_updates(self, session_id):
        updates = {}
        if session_id is None:
            updates['session'] = None
        else:
            session = Session.query.with_parent(self.event_new).filter_by(id=session_id).first()
            if not session:
                raise BadRequest('Invalid session id')
            if session != self.contrib.session:
                updates['session'] = session
        return updates

    def _get_contribution_track_updates(self, track_id):
        updates = {}
        if track_id is None:
            updates['track_id'] = None
        else:
            track = Track.get(track_id)
            if not track:
                raise BadRequest('Invalid track id')
            if track_id != self.contrib.track_id:
                updates['track_id'] = track_id
        return updates


class RHContributionPersonList(RHContributionPersonListMixin, RHManageContributionsActionsBase):
    """List of persons in the contribution"""

    @property
    def _membership_filter(self):
        contribution_ids = {contrib.id for contrib in self.contribs}
        return Contribution.id.in_(contribution_ids)


class RHContributionProtection(RHManageContributionBase):
    """Manage contribution protection"""

    def _process(self):
        form = ContributionProtectionForm(obj=FormDefaults(**self._get_defaults()), contrib=self.contrib,
                                          prefix='contribution-protection-')
        if form.validate_on_submit():
            update_contribution(self.contrib, {'protection_mode': form.protection_mode.data})
            update_object_principals(self.contrib, form.managers.data, full_access=True)
            if self.contrib.is_protected:
                update_object_principals(self.contrib, form.acl.data, read_access=True)
            update_object_principals(self.contrib, form.submitters.data, role='submit')
            return jsonify_data(flash=False, **self.list_generator.render_list(self.contrib))
        return jsonify_form(form)

    def _get_defaults(self):
        managers = {p.principal for p in self.contrib.acl_entries if p.full_access}
        submitters = {p.principal for p in self.contrib.acl_entries if p.has_management_role('submit', explicit=True)}
        acl = {p.principal for p in self.contrib.acl_entries if p.read_access}
        return {'managers': managers, 'submitters': submitters, 'protection_mode': self.contrib.protection_mode,
                'acl': acl}


class RHContributionSubContributions(RHManageContributionBase):
    """Get a list of subcontributions"""

    def _process(self):
        return jsonify_data(html=_render_subcontribution_list(self.contrib))


class RHCreateSubContribution(RHManageContributionBase):
    """Create a subcontribution"""

    def _process(self):
        form = SubContributionForm(event=self.event_new)
        if form.validate_on_submit():
            subcontrib = create_subcontribution(self.contrib, form.data)
            flash(_("Subcontribution '{}' created successfully").format(subcontrib.title), 'success')
            return jsonify_data(html=_render_subcontribution_list(self.contrib))
        return jsonify_template('events/contributions/forms/subcontribution.html', form=form)


class RHEditSubContribution(RHManageSubContributionBase):
    """Edit the subcontribution"""

    def _process(self):
        form = SubContributionForm(obj=FormDefaults(self.subcontrib), event=self.event_new, subcontrib=self.subcontrib)
        if form.validate_on_submit():
            update_subcontribution(self.subcontrib, form.data)
            flash(_("Subcontribution '{}' updated successfully").format(self.subcontrib.title), 'success')
            return jsonify_data(html=_render_subcontribution_list(self.contrib))
        elif not form.is_submitted():
            handle_legacy_description(form.description, self.subcontrib)
        self.commit = False
        return jsonify_template('events/contributions/forms/subcontribution.html', form=form)


class RHSubContributionREST(RHManageSubContributionBase):
    """REST endpoint for management of a single subcontribution"""

    def _process_DELETE(self):
        delete_subcontribution(self.subcontrib)
        flash(_("Subcontribution '{}' deleted successfully").format(self.subcontrib.title), 'success')
        return jsonify_data(html=_render_subcontribution_list(self.contrib))


class RHCreateSubContributionREST(RHManageContributionBase):
    """REST endpoint to create a subcontribution"""

    def _process_POST(self):
        form = SubContributionForm(event=self.event_new)
        if form.validate_on_submit():
            subcontrib = create_subcontribution(self.contrib, form.data)
            return jsonify(id=subcontrib.id, contribution_id=subcontrib.contribution_id, event_id=self.event_new.id)
        return jsonify_data(success=False, errors=form.errors), 400


class RHDeleteSubContributions(RHManageSubContributionsActionsBase):
    def _process(self):
        for subcontrib in self.subcontribs:
            delete_subcontribution(subcontrib)
        return jsonify_data(html=_render_subcontribution_list(self.contrib))


class RHSortSubContributions(RHManageContributionBase):
    def _process(self):
        subcontrib_ids = map(int, request.form.getlist('subcontrib_ids'))
        subcontribs = {s.id: s for s in self.contrib.subcontributions}
        for position, subcontrib_id in enumerate(subcontrib_ids, 1):
            if subcontrib_id in subcontribs:
                subcontribs[subcontrib_id].position = position


class RHContributionUpdateStartDate(RHManageContributionBase):
    def _checkParams(self, params):
        RHManageContributionBase._checkParams(self, params)
        if self.contrib.session_block:
            raise BadRequest

    def _process(self):
        form = ContributionStartDateForm(obj=FormDefaults(start_dt=self.contrib.start_dt), contrib=self.contrib)
        if form.validate_on_submit():
            with track_time_changes():
                update_timetable_entry(self.contrib.timetable_entry, {'start_dt': form.start_dt.data})
            return jsonify_data(new_value=format_datetime(self.contrib.start_dt, 'short'))
        return jsonify_form(form, back_button=False, disabled_until_change=True)


class RHContributionUpdateDuration(RHManageContributionBase):
    def _checkParams(self, params):
        RHManageContributionBase._checkParams(self, params)
        if self.contrib.session_block:
            raise BadRequest

    def _process(self):
        form = ContributionDurationForm(obj=FormDefaults(self.contrib), contrib=self.contrib)
        if form.validate_on_submit():
            with track_time_changes():
                update_contribution(self.contrib, {'duration': form.duration.data})
            return jsonify_data(new_value=format_human_timedelta(self.contrib.duration))
        return jsonify_form(form, back_button=False, disabled_until_change=True)


class RHContributionsMaterialPackage(RHManageContributionsActionsBase, AttachmentPackageGeneratorMixin):
    """Generate a ZIP file with materials for a given list of contributions"""

    ALLOW_UNSCHEDULED = True

    def _process(self):
        attachments = self._filter_by_contributions({c.id for c in self.contribs}, None)
        if not attachments:
            flash(_('The selected contributions do not have any materials.'), 'warning')
            return redirect(url_for('.manage_contributions', self.event_new))
        return self._generate_zip_file(attachments, name_suffix=self.event_new.id)


class RHContributionsExportCSV(RHManageContributionsActionsBase):
    """Export list of contributions to CSV"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_contributions(self.contribs)
        return send_csv('contributions.csv', headers, rows)


class RHContributionsExportExcel(RHManageContributionsActionsBase):
    """Export list of contributions to XLSX"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_contributions(self.contribs)
        return send_xlsx('contributions.xlsx', headers, rows)


class RHContributionsExportPDF(RHManageContributionsActionsBase):
    def _process(self):
        pdf = ContribsToPDF(self._conf, self.contribs)
        return send_file('contributions.pdf', pdf.generate(), 'application/pdf')


class RHContributionsExportPDFBook(RHManageContributionsActionsBase):
    def _process(self):
        pdf = ContributionBook(self._conf, session.user, self.contribs, tz=self.event_new.timezone)
        return send_file('book_of_abstracts.pdf', pdf.generate(), 'application/pdf')


class RHContributionsExportPDFBookSorted(RHManageContributionsActionsBase):
    def _process(self):
        pdf = ContributionBook(self._conf, session.user, self.contribs, tz=self.event_new.timezone,
                               sort_by='board_number')
        return send_file('book_of_abstracts.pdf', pdf.generate(), 'application/pdf')


class RHManageContributionTypes(RHManageContributionsBase):
    """Dialog to manage the ContributionTypes of an event"""

    def _process(self):
        contrib_types = self.event_new.contribution_types.all()
        return jsonify_template('events/contributions/management/types_dialog.html', event=self.event_new,
                                contrib_types=contrib_types)


class RHManageContributionTypeBase(RHManageContributionsBase):
    """Manage a contribution type of an event"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib_type
        }
    }

    def _checkParams(self, params):
        RHManageContributionsBase._checkParams(self, params)
        self.contrib_type = ContributionType.get_one(request.view_args['contrib_type_id'])


class RHEditContributionType(RHManageContributionTypeBase):
    """Dialog to edit a ContributionType"""

    def _process(self):
        form = ContributionTypeForm(event=self.event_new, obj=self.contrib_type)
        if form.validate_on_submit():
            old_name = self.contrib_type.name
            form.populate_obj(self.contrib_type)
            db.session.flush()
            self.event_new.log(EventLogRealm.management, EventLogKind.change, 'Contributions',
                               'Updated type: {}'.format(old_name), session.user)
            return contribution_type_row(self.contrib_type)
        return jsonify_form(form)


class RHCreateContributionType(RHManageContributionsBase):
    """Dialog to add a ContributionType"""

    def _process(self):
        form = ContributionTypeForm(event=self.event_new)
        if form.validate_on_submit():
            contrib_type = ContributionType()
            form.populate_obj(contrib_type)
            self.event_new.contribution_types.append(contrib_type)
            db.session.flush()
            self.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Contributions',
                               'Added type: {}'.format(contrib_type.name), session.user)
            return contribution_type_row(contrib_type)
        return jsonify_form(form)


class RHDeleteContributionType(RHManageContributionTypeBase):
    """Dialog to delete a ContributionType"""

    def _process(self):
        db.session.delete(self.contrib_type)
        db.session.flush()
        self.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Contributions',
                           'Deleted type: {}'.format(self.contrib_type.name), session.user)
        return jsonify_data(flash=False)


class RHManageContributionFields(RHManageContributionsBase):
    """Dialog to manage the custom contribution fields of an event"""

    def _process(self):
        custom_fields = self.event_new.contribution_fields.order_by(ContributionField.position)
        custom_field_types = sorted(get_contrib_field_types().values(), key=attrgetter('friendly_name'))
        return jsonify_template('events/contributions/management/fields_dialog.html', event=self.event_new,
                                custom_fields=custom_fields, custom_field_types=custom_field_types)


class RHSortContributionFields(RHManageContributionsBase):
    """Sort the custom contribution fields of an event"""

    def _process(self):
        field_by_id = {field.id: field for field in self.event_new.contribution_fields}
        field_ids = map(int, request.form.getlist('field_ids'))
        for index, field_id in enumerate(field_ids, 0):
            field_by_id[field_id].position = index
            del field_by_id[field_id]
        for index, field in enumerate(sorted(field_by_id.values(), key=attrgetter('position')), len(field_ids)):
            field.position = index
        db.session.flush()
        self.event_new.log(EventLogRealm.management, EventLogKind.change, 'Contributions',
                           'Custom fields have been reordered', session.user)
        return jsonify_data(flash=False)


class RHCreateContributionField(RHManageContributionsBase):
    """Dialog to create a new custom field"""

    def _checkParams(self, params):
        RHManageContributionsBase._checkParams(self, params)
        field_types = get_contrib_field_types()
        try:
            self.field_cls = field_types[request.view_args['field_type']]
        except KeyError:
            raise NotFound

    def _process(self):
        form = self.field_cls.create_config_form()
        if form.validate_on_submit():
            contrib_field = ContributionField()
            field = self.field_cls(contrib_field)
            field.update_object(form.data)
            self.event_new.contribution_fields.append(contrib_field)
            db.session.flush()
            self.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Contributions',
                               'Added field: {}'.format(contrib_field.title), session.user)
            return jsonify_data(flash=False)
        return jsonify_template('forms/form_common_fields_first.html', form=form)


class RHManageContributionFieldBase(RHManageContributionsBase):
    """Manage a custom contribution field of an event"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib_field
        }
    }

    def _checkParams(self, params):
        RHManageContributionsBase._checkParams(self, params)
        self.contrib_field = ContributionField.get_one(request.view_args['contrib_field_id'])


class RHEditContributionField(RHManageContributionFieldBase):
    """Dialog to edit a custom field"""

    def _process(self):
        field_class = get_contrib_field_types()[self.contrib_field.field_type]
        form = field_class.create_config_form(obj=FormDefaults(self.contrib_field, **self.contrib_field.field_data))
        if form.validate_on_submit():
            old_title = self.contrib_field.title
            self.contrib_field.mgmt_field.update_object(form.data)
            db.session.flush()
            self.event_new.log(EventLogRealm.management, EventLogKind.change, 'Contributions',
                               'Modified field: {}'.format(old_title), session.user)
            return jsonify_data(flash=False)
        return jsonify_template('forms/form_common_fields_first.html', form=form)


class RHDeleteContributionField(RHManageContributionFieldBase):
    """Dialog to delete a custom contribution field"""

    def _process(self):
        db.session.delete(self.contrib_field)
        db.session.flush()
        self.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Contributions',
                           'Deleted field: {}'.format(self.contrib_field.title), session.user)


class RHManageDescriptionField(RHManageContributionsBase):
    """Manage the description field used by the abstracts"""

    def _process(self):
        description_settings = abstracts_settings.get(self.event_new, 'description_settings')
        form = AbstractContentSettingsForm(obj=FormDefaults(description_settings))
        if form.validate_on_submit():
            abstracts_settings.set(self.event_new, 'description_settings', form.data)
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHCreateReferenceMixin:
    """Common methods for RH class creating a ContibutionReference or SubContributionReference"""

    def _checkParams(self):
        self.reference_value = request.form['value']
        reference_type_name = request.form['type']
        self.reference_type = ReferenceType.find_one(db.func.lower(ReferenceType.name) == reference_type_name.lower())

    @staticmethod
    def jsonify_reference(reference):
        return jsonify(id=reference.id)


class RHCreateContributionReferenceREST(RHCreateReferenceMixin, RHManageContributionBase):
    """REST endpoint to add a reference to a Contribution"""

    def _checkParams(self, params):
        RHManageContributionBase._checkParams(self, params)
        RHCreateReferenceMixin._checkParams(self)

    def _process_POST(self):
        reference = ContributionReference(reference_type=self.reference_type, value=self.reference_value,
                                          contribution=self.contrib)
        db.session.flush()
        return self.jsonify_reference(reference)


class RHCreateSubContributionReferenceREST(RHCreateReferenceMixin, RHManageSubContributionBase):
    """REST endpoint to add a reference to a SubContribution"""

    def _checkParams(self, params):
        RHManageSubContributionBase._checkParams(self, params)
        RHCreateReferenceMixin._checkParams(self)

    def _process_POST(self):
        reference = SubContributionReference(reference_type=self.reference_type, value=self.reference_value)
        self.subcontrib.references.append(reference)
        db.session.flush()
        return self.jsonify_reference(reference)
