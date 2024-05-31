# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import uuid
from operator import attrgetter

from flask import flash, jsonify, redirect, request, session
from marshmallow import fields
from sqlalchemy.orm import joinedload, subqueryload, undefer
from webargs.flaskparser import abort
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core.cache import make_scoped_cache
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode, render_acl
from indico.core.permissions import get_principal_permissions, update_permissions
from indico.legacy.pdfinterface.latex import ContribsToPDF, ContributionBook
from indico.modules.attachments.controllers.event_package import AttachmentPackageGeneratorMixin
from indico.modules.events.abstracts.forms import AbstractContentSettingsForm
from indico.modules.events.abstracts.settings import abstracts_settings
from indico.modules.events.contributions import contribution_settings, get_contrib_field_types
from indico.modules.events.contributions.clone import ContributionCloner
from indico.modules.events.contributions.controllers.common import ContributionListMixin
from indico.modules.events.contributions.forms import (AllowSubmitterEditsForm, ContributionDefaultDurationForm,
                                                       ContributionDurationForm, ContributionExportTeXForm,
                                                       ContributionProtectionForm, ContributionStartDateForm,
                                                       ContributionTypeForm, SubContributionForm)
from indico.modules.events.contributions.lists import ContributionListGenerator
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionField
from indico.modules.events.contributions.models.references import ContributionReference, SubContributionReference
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.contributions.operations import (create_contribution, create_subcontribution,
                                                            delete_contribution, delete_subcontribution,
                                                            log_contribution_update, update_contribution,
                                                            update_subcontribution)
from indico.modules.events.contributions.schemas import ContributionFieldSchema
from indico.modules.events.contributions.util import (contribution_type_row, generate_spreadsheet_from_contributions,
                                                      get_boa_export_formats, import_contributions_from_csv,
                                                      make_contribution_form)
from indico.modules.events.contributions.views import WPManageContributions
from indico.modules.events.controllers.base import EditEventSettingsMixin
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.management.controllers.base import RHContributionPersonListMixin
from indico.modules.events.management.controllers.emails import (EmailRolesMetadataMixin, EmailRolesPreviewMixin,
                                                                 EmailRolesSendMixin)
from indico.modules.events.management.util import flash_if_unregistered
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.sessions import Session
from indico.modules.events.timetable.forms import ImportContributionsForm
from indico.modules.events.timetable.operations import update_timetable_entry
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.util import (check_event_locked, get_field_values, set_custom_fields, track_location_changes,
                                        track_time_changes)
from indico.modules.logs import EventLogRealm, LogKind
from indico.util.date_time import format_datetime, format_human_timedelta
from indico.util.i18n import _, ngettext
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.util.string import handle_legacy_description
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file, url_for
from indico.web.forms.base import FormDefaults
from indico.web.forms.fields.principals import serialize_principal
from indico.web.rh import json_errors
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


export_list_cache = make_scoped_cache('contrib-export-list')


def _render_subcontribution_list(contrib):
    tpl = get_template_module('events/contributions/management/_subcontribution_list.html')
    subcontribs = (SubContribution.query.with_parent(contrib)
                   .options(undefer('attachment_count'))
                   .order_by(SubContribution.position)
                   .all())
    return tpl.render_subcontribution_list(contrib.event, contrib, subcontribs)


class RHManageContributionsBase(RHManageEventBase):
    """Base class for all contributions management RHs."""

    PERMISSION = 'contributions'

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.list_generator = ContributionListGenerator(event=self.event)


class RHManageContributionBase(RHManageContributionsBase):
    """Base class for a specific contribution."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        }
    }

    def _process_args(self):
        RHManageContributionsBase._process_args(self)
        self.contrib = Contribution.query.filter_by(id=request.view_args['contrib_id'], is_deleted=False).one()

    def _check_access(self):
        if not self.contrib.can_manage(session.user):
            raise Forbidden
        check_event_locked(self, self.event)


class RHManageSubContributionBase(RHManageContributionBase):
    """Base RH for a specific subcontribution."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.subcontrib
        }
    }

    def _process_args(self):
        RHManageContributionBase._process_args(self)
        self.subcontrib = SubContribution.get_or_404(request.view_args['subcontrib_id'], is_deleted=False)


class RHManageContributionsActionsBase(RHManageContributionsBase):
    """Base class for classes performing actions on event contributions."""

    _allow_get_all = False
    _contrib_query_options = ()

    @property
    def _contribution_query(self):
        query = Contribution.query.with_parent(self.event)
        if self._contrib_query_options:
            query = query.options(*self._contrib_query_options)
        return query

    @use_kwargs({
        'contribution_ids': fields.List(fields.Int(), data_key='contribution_id', load_default=lambda: [])
    })
    def _process_args(self, contribution_ids):
        RHManageContributionsBase._process_args(self)
        self.contrib_ids = contribution_ids
        query = self._contribution_query
        if request.method == 'POST' or not self._allow_get_all:
            # if it's POST we filter by abstract ids; otherwise we assume
            # the user wants everything (e.g. API-like usage via personal token)
            query = query.filter(Contribution.id.in_(contribution_ids))
        self.contribs = query.all()


class RHManageSubContributionsActionsBase(RHManageContributionBase):
    """Base class for RHs performing actions on subcontributions."""

    def _process_args(self):
        RHManageContributionBase._process_args(self)
        ids = {int(x) for x in request.form.getlist('subcontribution_id')}
        self.subcontribs = (SubContribution.query
                            .with_parent(self.contrib)
                            .filter(SubContribution.id.in_(ids))
                            .all())


class RHContributions(ContributionListMixin, RHManageContributionsBase):
    """Display contributions management page."""

    template = 'management/contributions.html'
    view_class = WPManageContributions


class RHContributionListCustomize(RHManageContributionsBase):
    """Filter options for the contributions list of an event."""

    ALLOW_LOCKED = True

    def _process_GET(self):
        list_config = self.list_generator._get_config()
        return jsonify_template('events/contributions/contrib_list_filter.html',
                                visible_items=list_config.get('items', ()),
                                filters=self.list_generator.list_config['filters'],
                                static_items=self.list_generator.static_items,
                                contrib_fields=self.list_generator.get_all_custom_fields(),
                                extra_filters=self.list_generator.extra_filters,
                                has_types=self.event.contribution_types.has_rows(),
                                management=True)

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(**self.list_generator.render_list())


class RHContributionListStaticURL(RHManageContributionsBase):
    """Generate a static URL for the configuration of the contribution list."""

    ALLOW_LOCKED = True

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHCreateContribution(RHManageContributionsBase):
    def _process(self):
        inherited_location = self.event.location_data
        inherited_location['inheriting'] = True
        default_duration = contribution_settings.get(self.event, 'default_duration')
        contrib_form_class = make_contribution_form(self.event)
        form = contrib_form_class(obj=FormDefaults(location_data=inherited_location, duration=default_duration),
                                  event=self.event)
        if form.validate_on_submit():
            # Create empty contribution so it can be compared to the new one in flash_if_unregistered
            contrib = Contribution()
            with flash_if_unregistered(self.event, lambda: contrib.person_links):
                contrib = create_contribution(self.event, *get_field_values(form.data))
            flash(_("Contribution '{}' created successfully").format(contrib.title), 'success')
            tpl_components = self.list_generator.render_list(contrib)
            if tpl_components['hide_contrib']:
                self.list_generator.flash_info_message(contrib)
            return jsonify_data(**tpl_components)
        return jsonify_template('events/contributions/forms/contribution.html', form=form, can_manage=True)


class RHEditContribution(RHManageContributionBase):
    """Edit a contribution.

    If configured in the contribution settings, editing is also
    allowed for the submitters.
    """

    def _check_access(self):
        if not self.contrib.can_edit(session.user):
            raise Forbidden
        check_event_locked(self, self.event)

    def _process(self):
        can_manage = self.contrib.can_manage(session.user)
        contrib_form_class = make_contribution_form(self.event, management=can_manage)
        custom_field_values = {f'custom_{x.contribution_field_id}': x.data for x in self.contrib.field_values}
        parent_session_block = (self.contrib.timetable_entry.parent.session_block
                                if (self.contrib.timetable_entry and self.contrib.timetable_entry.parent) else None)
        form = contrib_form_class(obj=FormDefaults(self.contrib, start_date=self.contrib.start_dt,
                                                   **custom_field_values),
                                  event=self.event, contrib=self.contrib, session_block=parent_session_block,
                                  submitter_edit=(not can_manage))
        if form.validate_on_submit():
            with (
                track_time_changes(),
                track_location_changes(),
                flash_if_unregistered(self.event, lambda: self.contrib.person_links)
            ):
                update_contribution(self.contrib, *get_field_values(form.data))
            flash(_("Contribution '{}' successfully updated").format(self.contrib.title), 'success')
            if not can_manage or request.args.get('standalone') == '1':
                return jsonify_data(flash=False)
            tpl_components = self.list_generator.render_list(self.contrib)
            if tpl_components['hide_contrib']:
                self.list_generator.flash_info_message(self.contrib)
            return jsonify_data(flash=(request.args.get('flash') == '1'), **tpl_components)
        elif not form.is_submitted():
            handle_legacy_description(form.description, self.contrib)
        self.commit = False
        return jsonify_template('events/contributions/forms/contribution.html', form=form, can_manage=can_manage)


class RHDeleteContributions(RHManageContributionsActionsBase):
    def _process(self):
        for contrib in self.contribs:
            delete_contribution(contrib)
        deleted_count = len(self.contribs)
        flash(ngettext('The contribution has been deleted.',
                       '{count} contributions have been deleted.', deleted_count)
              .format(count=deleted_count), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHContributionACL(RHManageContributionBase):
    """Display the ACL of the contribution."""

    def _process(self):
        return render_acl(self.contrib)


class RHContributionACLMessage(RHManageContributionBase):
    """Render the inheriting ACL message."""

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
        if set(data.keys()) > {'session_id', 'track_id'}:
            raise BadRequest
        if not self.event.can_manage(session.user):
            raise Forbidden
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
            session = Session.query.with_parent(self.event).filter_by(id=session_id).first()
            if not session:
                raise BadRequest('Invalid session id')
            if session != self.contrib.session:
                updates['session'] = session
        return updates

    def _get_contribution_track_updates(self, track_id):
        updates = {}
        if track_id is None:
            updates['track'] = None
        else:
            track = Track.query.with_parent(self.event).filter_by(id=track_id).first()
            if not track:
                raise BadRequest('Invalid track id')
            if track_id != self.contrib.track_id:
                updates['track'] = track
        return updates


class RHContributionPersonList(RHContributionPersonListMixin, RHManageContributionsActionsBase):
    """List of persons in the contribution."""

    ALLOW_LOCKED = True

    @property
    def _membership_filter(self):
        contribution_ids = {contrib.id for contrib in self.contribs}
        return Contribution.id.in_(contribution_ids)


class RHContributionProtection(RHManageContributionBase):
    """Manage contribution protection."""

    def _process(self):
        form = ContributionProtectionForm(obj=FormDefaults(**self._get_defaults()), contrib=self.contrib,
                                          prefix='contribution-protection-')
        if form.validate_on_submit():
            update_permissions(self.contrib, form)
            update_contribution(self.contrib, {'protection_mode': form.protection_mode.data})
            return jsonify_data(flash=False, **self.list_generator.render_list(self.contrib))
        return jsonify_template('events/management/protection_dialog.html', form=form)

    def _get_defaults(self):
        permissions = [[serialize_principal(p.principal), list(get_principal_permissions(p, Contribution))]
                       for p in self.contrib.acl_entries]
        permissions = [item for item in permissions if item[1]]
        return {'permissions': permissions, 'protection_mode': self.contrib.protection_mode}


class RHContributionSubContributions(RHManageContributionBase):
    """Get a list of subcontributions."""

    def _process(self):
        return jsonify_data(html=_render_subcontribution_list(self.contrib))


class RHCreateSubContribution(RHManageContributionBase):
    """Create a subcontribution."""

    def _process(self):
        form = SubContributionForm(event=self.event)
        if form.validate_on_submit():
            subcontrib = create_subcontribution(self.contrib, form.data)
            flash(_("Subcontribution '{}' created successfully").format(subcontrib.title), 'success')
            return jsonify_data(html=_render_subcontribution_list(self.contrib))
        return jsonify_template('events/contributions/forms/subcontribution.html', form=form, can_manage=True)


class RHEditSubContribution(RHManageSubContributionBase):
    """Edit a subcontribution.

    If configured in the contribution settings, editing is also
    allowed for the submitters of the parent contribution.
    """

    def _check_access(self):
        if not self.subcontrib.can_edit(session.user):
            raise Forbidden
        check_event_locked(self, self.event)

    def _process(self):
        can_manage = self.subcontrib.can_manage(session.user)
        form = SubContributionForm(obj=FormDefaults(self.subcontrib), event=self.event, subcontrib=self.subcontrib,
                                   submitter_edit=(not can_manage))
        if form.validate_on_submit():
            update_subcontribution(self.subcontrib, form.data)
            flash(_("Subcontribution '{}' updated successfully").format(self.subcontrib.title), 'success')
            if not can_manage or request.args.get('standalone') == '1':
                return jsonify_data(flash=False)
            return jsonify_data(html=_render_subcontribution_list(self.contrib))
        elif not form.is_submitted():
            handle_legacy_description(form.description, self.subcontrib)
        self.commit = False
        return jsonify_template('events/contributions/forms/subcontribution.html', form=form, can_manage=can_manage)


class RHSubContributionREST(RHManageSubContributionBase):
    """REST endpoint for management of a single subcontribution."""

    def _process_DELETE(self):
        delete_subcontribution(self.subcontrib)
        flash(_("Subcontribution '{}' deleted successfully").format(self.subcontrib.title), 'success')
        return jsonify_data(html=_render_subcontribution_list(self.contrib))


class RHCreateSubContributionREST(RHManageContributionBase):
    """REST endpoint to create a subcontribution."""

    def _process_POST(self):
        form = SubContributionForm(event=self.event)
        if form.validate_on_submit():
            subcontrib = create_subcontribution(self.contrib, form.data)
            return jsonify(id=subcontrib.id, contribution_id=subcontrib.contribution_id, event_id=self.event.id)
        return jsonify_data(success=False, errors=form.errors), 400


class RHDeleteSubContributions(RHManageSubContributionsActionsBase):
    def _process(self):
        for subcontrib in self.subcontribs:
            delete_subcontribution(subcontrib)
        return jsonify_data(html=_render_subcontribution_list(self.contrib))


class RHSortSubContributions(RHManageContributionBase):
    def _process(self):
        subcontrib_ids = request.form.getlist('subcontrib_ids', type=int)
        subcontribs = {s.id: s for s in self.contrib.subcontributions}
        for position, subcontrib_id in enumerate(subcontrib_ids, 1):
            if subcontrib_id in subcontribs:
                subcontribs[subcontrib_id].position = position


class RHContributionUpdateStartDate(RHManageContributionBase):
    def _process_args(self):
        RHManageContributionBase._process_args(self)
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
    def _process_args(self):
        RHManageContributionBase._process_args(self)
        if self.contrib.session_block:
            raise BadRequest

    def _process(self):
        form = ContributionDurationForm(obj=FormDefaults(self.contrib), contrib=self.contrib)
        if form.validate_on_submit():
            with track_time_changes():
                update_contribution(self.contrib, {'duration': form.duration.data})
            return jsonify_data(new_value=format_human_timedelta(self.contrib.duration, narrow=True))
        return jsonify_form(form, back_button=False, disabled_until_change=True)


class RHManageContributionsExportActionsBase(RHManageContributionsActionsBase):
    ALLOW_LOCKED = True
    _allow_get_all = True

    _contrib_query_options = (subqueryload('field_values'),
                              subqueryload('person_links'),
                              joinedload('track').joinedload('track_group'),
                              joinedload('type'),
                              joinedload('session_block'),
                              joinedload('timetable_entry').lazyload('*'),
                              undefer('is_scheduled'))

    def _process_args(self):
        RHManageContributionsActionsBase._process_args(self)
        # some PDF export options do not sort the contribution list so we keep
        # the order in which they were displayed when the user selected them
        if self.contrib_ids:
            self.contribs.sort(key=lambda c: self.contrib_ids.index(c.id))


class RHContributionsMaterialPackage(RHManageContributionsExportActionsBase, AttachmentPackageGeneratorMixin):
    """Generate a ZIP file with materials for a given list of contributions."""

    ALLOW_UNSCHEDULED = True
    ALLOW_LOCKED = True

    def _process(self):
        attachments = self._filter_by_contributions({c.id for c in self.contribs}, None)
        if not attachments:
            flash(_('The selected contributions do not have any materials.'), 'warning')
            return redirect(url_for('.manage_contributions', self.event))
        return self._generate_zip_file(attachments, name_suffix=self.event.id)


class RHContributionsExportJSON(RHManageContributionsExportActionsBase):
    """Export list of contributions to JSON."""

    def _process(self):
        from indico.modules.events.contributions.schemas import FullContributionSchema
        resp = FullContributionSchema(many=True).jsonify(sorted(self.contribs, key=attrgetter('friendly_id')))
        resp.headers['Content-Disposition'] = 'attachment; filename="contributions.json"'
        return resp


class RHContributionsExportCSV(RHManageContributionsExportActionsBase):
    """Export list of contributions to CSV."""

    def _process(self):
        headers, rows = generate_spreadsheet_from_contributions(self.contribs)
        return send_csv('contributions.csv', headers, rows)


class RHContributionsExportExcel(RHManageContributionsExportActionsBase):
    """Export list of contributions to XLSX."""

    def _process(self):
        headers, rows = generate_spreadsheet_from_contributions(self.contribs)
        return send_xlsx('contributions.xlsx', headers, rows, tz=self.event.tzinfo)


class RHContributionsExportPDF(RHManageContributionsExportActionsBase):
    def _process(self):
        if not config.LATEX_ENABLED:
            raise NotFound
        pdf = ContribsToPDF(self.event, self.contribs)
        return send_file('contributions.pdf', pdf.generate(), 'application/pdf')


class RHContributionsExportTeX(RHManageContributionsExportActionsBase):
    def _process(self):
        tex = ContribsToPDF(self.event, self.contribs)
        archive = tex.generate_source_archive()
        return send_file('contributions-tex.zip', archive, 'application/zip', inline=False)


class RHContributionExportTexConfig(RHManageContributionsExportActionsBase):
    """Configure Export via LaTeX."""

    ALLOW_LOCKED = True

    def _process(self):
        form = ContributionExportTeXForm(contribs=self.contribs)
        form.format.choices = [(k, v[0]) for k, v in get_boa_export_formats().items()]
        if form.validate_on_submit():
            data = form.data
            data.pop('submitted', None)
            key = str(uuid.uuid4())
            export_list_cache.set(key, data, timeout=1800)
            download_url = url_for('.contributions_tex_export_book', self.event, uuid=key)
            return jsonify_data(flash=False, redirect=download_url, redirect_no_loading=True)

        return jsonify_form(form, submit=_('Export'), disabled_until_change=False)


class RHContributionsExportTeXBook(RHManageContributionsExportActionsBase):
    """Handle export contributions via LaTeX."""

    def _process(self):
        config_params = export_list_cache.get(request.view_args['uuid'])
        output_format = config_params['format']
        sort_by = config_params['sort_by']
        contribs = (Contribution.query.with_parent(self.event)
                    .filter(Contribution.id.in_(config_params['contribution_ids']))
                    .all())

        func = get_boa_export_formats()[output_format][1]
        return func(self.event, contribs, sort_by, ContributionBook)


class RHContributionsImportCSV(RHManageContributionsBase):
    """Import contributions from a CSV file."""

    def _process(self):
        form = ImportContributionsForm()

        if form.validate_on_submit():
            contributions, changes = import_contributions_from_csv(self.event, form.source_file.data)
            flash(ngettext('{} contribution has been imported.',
                           '{} contributions have been imported.',
                           len(contributions)).format(len(contributions)), 'success')
            if changes:
                flash(_('Event dates/times adjusted due to imported data.'), 'warning')
            return jsonify_data(flash=False, redirect=url_for('.manage_contributions', self.event))
        return jsonify_template('events/contributions/management/import_contributions.html', form=form,
                                event=self.event)


class RHManageContributionTypes(RHManageContributionsBase):
    """Dialog to manage the ContributionTypes of an event."""

    def _process(self):
        contrib_types = self.event.contribution_types.order_by(db.func.lower(ContributionType.name)).all()
        return jsonify_template('events/contributions/management/types_dialog.html', event=self.event,
                                contrib_types=contrib_types)


class RHManageDefaultContributionDuration(RHManageContributionsBase):
    """Dialog to manage the default contribution duration."""

    def _process(self):
        form = ContributionDefaultDurationForm(duration=contribution_settings.get(self.event, 'default_duration'))
        if form.validate_on_submit():
            contribution_settings.set(self.event, 'default_duration', form.duration.data)
            flash(_('Default contribution duration was changed successfully'), 'success')
            return jsonify_data()
        return jsonify_form(form)


class RHManageSubmitterEdits(EditEventSettingsMixin, RHManageContributionsBase):
    """Dialog to configure submitter edit permissions."""

    settings_proxy = contribution_settings
    form_cls = AllowSubmitterEditsForm
    success_message = _('Submitter edit settings changed successfully')
    log_module = 'Contributions'
    log_message = 'Submitter privileges updated'
    log_fields = {'submitters_can_edit': 'Edit basic fields',
                  'submitters_can_edit_custom': 'Edit custom fields'}


class RHManageContributionPublicationREST(RHManageContributionsBase):
    """Manage contribution publication setting."""

    # Publishing and unpublishing contribution requires full management permissions
    PERMISSION = None

    def _process_GET(self):
        return jsonify(contribution_settings.get(self.event, 'published'))

    def _process_PUT(self):
        contribution_settings.set(self.event, 'published', True)
        self.event.log(EventLogRealm.management, LogKind.positive, 'Contributions',
                       'Contributions published', session.user)
        return '', 204

    def _process_DELETE(self):
        contribution_settings.set(self.event, 'published', False)
        self.event.log(EventLogRealm.management, LogKind.negative, 'Contributions',
                       'Contributions unpublished', session.user)
        return '', 204


class RHManageContributionTypeBase(RHManageContributionsBase):
    """Manage a contribution type of an event."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib_type
        }
    }

    def _process_args(self):
        RHManageContributionsBase._process_args(self)
        self.contrib_type = ContributionType.get_or_404(request.view_args['contrib_type_id'])


class RHEditContributionType(RHManageContributionTypeBase):
    """Dialog to edit a ContributionType."""

    def _process(self):
        form = ContributionTypeForm(event=self.event, obj=self.contrib_type)
        if form.validate_on_submit():
            old_name = self.contrib_type.name
            form.populate_obj(self.contrib_type)
            db.session.flush()
            self.event.log(EventLogRealm.management, LogKind.change, 'Contributions',
                           f'Updated type: {old_name}', session.user)
            return contribution_type_row(self.contrib_type)
        return jsonify_form(form)


class RHCreateContributionType(RHManageContributionsBase):
    """Dialog to add a ContributionType."""

    def _process(self):
        form = ContributionTypeForm(event=self.event)
        if form.validate_on_submit():
            contrib_type = ContributionType()
            form.populate_obj(contrib_type)
            self.event.contribution_types.append(contrib_type)
            db.session.flush()
            self.event.log(EventLogRealm.management, LogKind.positive, 'Contributions',
                           f'Added type: {contrib_type.name}', session.user)
            return contribution_type_row(contrib_type)
        return jsonify_form(form)


class RHDeleteContributionType(RHManageContributionTypeBase):
    """Dialog to delete a ContributionType."""

    def _process(self):
        db.session.delete(self.contrib_type)
        db.session.flush()
        self.event.log(EventLogRealm.management, LogKind.negative, 'Contributions',
                       f'Deleted type: {self.contrib_type.name}', session.user)
        return jsonify_data(flash=False)


class RHManageContributionFields(RHManageContributionsBase):
    """Dialog to manage the custom contribution fields of an event."""

    def _process(self):
        custom_fields = self.event.contribution_fields.order_by(ContributionField.position).all()
        custom_field_types = sorted(get_contrib_field_types().values(), key=attrgetter('friendly_name'))
        return jsonify_template('events/contributions/management/fields_dialog.html', event=self.event,
                                custom_fields=custom_fields, custom_field_types=custom_field_types)


class RHManageContributionFieldsAPI(RHManageContributionsBase):
    """API endpoint to get the custom contribution fields."""

    def _process(self):
        custom_fields = self.event.contribution_fields.order_by(ContributionField.position).all()
        return ContributionFieldSchema(many=True).jsonify(custom_fields)


class RHSortContributionFields(RHManageContributionsBase):
    """Sort the custom contribution fields of an event."""

    def _process(self):
        field_by_id = {field.id: field for field in self.event.contribution_fields}
        field_ids = request.form.getlist('field_ids', type=int)
        for index, field_id in enumerate(field_ids, 0):
            field_by_id[field_id].position = index
            del field_by_id[field_id]
        for index, field in enumerate(sorted(field_by_id.values(), key=attrgetter('position')), len(field_ids)):
            field.position = index
        db.session.flush()
        self.event.log(EventLogRealm.management, LogKind.change, 'Contributions',
                       'Custom fields reordered', session.user)
        return jsonify_data(flash=False)


class RHCreateContributionField(RHManageContributionsBase):
    """Dialog to create a new custom field."""

    def _process_args(self):
        RHManageContributionsBase._process_args(self)
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
            self.event.contribution_fields.append(contrib_field)
            db.session.flush()
            self.event.log(EventLogRealm.management, LogKind.positive, 'Contributions',
                           f'Added field: {contrib_field.title}', session.user)

            return jsonify_data(flash=False)
        return jsonify_template('events/contributions/forms/contribution_field_form.html', form=form)


class RHManageContributionFieldBase(RHManageContributionsBase):
    """Manage a custom contribution field of an event."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib_field
        }
    }

    def _process_args(self):
        RHManageContributionsBase._process_args(self)
        self.contrib_field = ContributionField.get_or_404(request.view_args['contrib_field_id'])


class RHEditContributionField(RHManageContributionFieldBase):
    """Dialog to edit a custom field."""

    def _process(self):
        field_class = get_contrib_field_types()[self.contrib_field.field_type]
        form = field_class.create_config_form(obj=FormDefaults(self.contrib_field, **self.contrib_field.field_data))
        if form.validate_on_submit():
            old_title = self.contrib_field.title
            self.contrib_field.mgmt_field.update_object(form.data)
            db.session.flush()
            self.event.log(EventLogRealm.management, LogKind.change, 'Contributions',
                           f'Modified field: {old_title}', session.user)
            return jsonify_data(flash=False)
        return jsonify_template('events/contributions/forms/contribution_field_form.html', form=form)


class RHDeleteContributionField(RHManageContributionFieldBase):
    """Dialog to delete a custom contribution field."""

    def _process(self):
        db.session.delete(self.contrib_field)
        db.session.flush()
        self.event.log(EventLogRealm.management, LogKind.negative, 'Contributions',
                       f'Deleted field: {self.contrib_field.title}', session.user)


class RHManageDescriptionField(RHManageContributionsBase):
    """Manage the description field used by the abstracts."""

    def _process(self):
        description_settings = abstracts_settings.get(self.event, 'description_settings')
        form = AbstractContentSettingsForm(obj=FormDefaults(description_settings))
        if form.validate_on_submit():
            abstracts_settings.set(self.event, 'description_settings', form.data)
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHCreateReferenceMixin:
    """
    Common methods for RH class creating a ContributionReference
    or SubContributionReference.
    """

    def _process_args(self):
        self.reference_value = request.form['value']
        reference_type_name = request.form['type']
        self.reference_type = (ReferenceType.query
                               .filter(db.func.lower(ReferenceType.name) == reference_type_name.lower())
                               .one())

    @staticmethod
    def jsonify_reference(reference):
        return jsonify(id=reference.id)


class RHCreateContributionReferenceREST(RHCreateReferenceMixin, RHManageContributionBase):
    """REST endpoint to add a reference to a Contribution."""

    def _process_args(self):
        RHManageContributionBase._process_args(self)
        RHCreateReferenceMixin._process_args(self)

    def _process_POST(self):
        reference = ContributionReference(reference_type=self.reference_type, value=self.reference_value,
                                          contribution=self.contrib)
        db.session.flush()
        return self.jsonify_reference(reference)


@json_errors
class RHContributionFieldsREST(RHManageContributionBase):
    """REST endpoint to manage custom field values for a Contribution."""

    @use_kwargs({'friendly': fields.Bool(load_default=False)}, location='query')
    def _process_GET(self, friendly):
        return jsonify({f'custom_{fv.contribution_field.id}': (fv.friendly_data if friendly else fv.data)
                        for fv in self.contrib.field_values})

    def _process_PATCH(self):
        # it'd be nicer to use marshmallow here but converting the custom field logic to support
        # marshmallow would be a significant refactoring. let's do that only when moving all the
        # places that use those fields to react so we can just replace wtforms with
        # marshmallow there altogether!
        form = make_contribution_form(self.event, only_custom_fields=True)()
        formdata = request.json if request.is_json else request.form
        # wtforms has no partial mode but we never want to overwrite fields not specified,
        # so we remove any fields not in the request data
        for field in list(form):
            if field.name not in formdata:
                delattr(form, field.name)
        if not form.validate_on_submit():
            abort(422, messages=form.errors)
        changes = set_custom_fields(self.contrib, form.data)
        log_contribution_update(self.contrib, changes)
        return self._process_GET()


class RHCreateSubContributionReferenceREST(RHCreateReferenceMixin, RHManageSubContributionBase):
    """REST endpoint to add a reference to a SubContribution."""

    def _process_args(self):
        RHManageSubContributionBase._process_args(self)
        RHCreateReferenceMixin._process_args(self)

    def _process_POST(self):
        reference = SubContributionReference(reference_type=self.reference_type, value=self.reference_value)
        self.subcontrib.references.append(reference)
        db.session.flush()
        return self.jsonify_reference(reference)


class RHCloneContribution(RHManageContributionBase):
    def _check_access(self):
        # Just like creating contributions, cloning one requires full event management access
        RHManageContributionsBase._check_access(self)

    def _process(self):
        ContributionCloner.clone_single_contribution(self.contrib)
        return jsonify_data(**self.list_generator.render_list())


class RHContributionsAPIEmailContribRolesMetadata(EmailRolesMetadataMixin, RHManageContributionsBase):
    object_context = 'contributions'


class RHContributionsAPIEmailContribRolesPreview(EmailRolesPreviewMixin, RHManageContributionsActionsBase):
    object_context = 'contributions'

    def get_placeholder_kwargs(self):
        for contrib in self.contribs:
            for p in contrib.person_links:
                if p.email:
                    return {'person': p, 'contribution': contrib}
        return {'person': self.event.creator, 'contribution': self.contribs[0]}


class RHContributionsAPIEmailContribRolesSend(EmailRolesSendMixin, RHManageContributionsActionsBase):
    object_context = 'contributions'
    log_module = 'Contributions'

    def get_recipients(self, roles):
        for contrib in self.contribs:
            log_metadata = {'contribution_id': contrib.id}
            for person_link in contrib.person_links:
                if person_link.email and self.get_roles_from_person_link(person_link) & roles:
                    yield person_link.email, {'contribution': contrib, 'person': person_link}, log_metadata
