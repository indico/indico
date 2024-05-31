# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict
from io import BytesIO

from flask import jsonify, redirect, request, session
from sqlalchemy.orm import joinedload, load_only
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.config import config
from indico.core.db import db
from indico.legacy.pdfinterface.latex import ContribsToPDF, ContribToPDF
from indico.modules.events.abstracts.util import filter_field_values
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.contributions.ical import contribution_to_ical
from indico.modules.events.contributions.lists import ContributionDisplayListGenerator
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import AuthorType, ContributionPersonLink
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.util import (get_contributions_for_user,
                                                      has_contributions_with_user_as_submitter)
from indico.modules.events.contributions.views import WPAuthorList, WPContributions, WPMyContributions, WPSpeakerList
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.layout.util import is_menu_entry_enabled
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPerson
from indico.util.i18n import _
from indico.web.flask.util import jsonify_data, send_file, url_for
from indico.web.rh import RH, allow_signed_url
from indico.web.util import jsonify_template


def _get_persons(event, condition):
    """
    Query event persons linked to contributions in the event,
    filtered using the condition provided.
    """
    return (event.persons.filter(EventPerson.contribution_links.any(
            db.and_(condition,
                    ContributionPersonLink.contribution.has(~Contribution.is_deleted))))
            .options(joinedload('contribution_links').joinedload('contribution'))
            .order_by(db.func.lower(EventPerson.last_name)))


def _author_page_active(event):
    return is_menu_entry_enabled('author_index', event) or is_menu_entry_enabled('contributions', event)


class RHContributionDisplayBase(RHDisplayEventBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        }
    }

    def _can_view_unpublished(self):
        return (self.event.can_manage(session.user, permission='contributions') or
                self.contrib.is_user_associated(session.user))

    def _check_access(self):
        if not self.contrib.can_access(session.user):
            # perform event access check since it may send the user to the access key or registration page
            RHDisplayEventBase._check_access(self)
            raise Forbidden
        published = contribution_settings.get(self.event, 'published')
        if not published and not self._can_view_unpublished():
            raise NotFound(_('The contributions of this event have not been published yet.'))

    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        self.contrib = Contribution.get_or_404(request.view_args['contrib_id'], is_deleted=False)


class RHDisplayProtectionBase(RHDisplayEventBase):
    def _check_access(self):
        RHDisplayEventBase._check_access(self)
        published = contribution_settings.get(self.event, 'published')
        can_manage = self.event.can_manage(session.user, permission='contributions')
        if not published and not can_manage and not has_contributions_with_user_as_submitter(self.event, session.user):
            raise NotFound(_('The contributions of this event have not been published yet.'))

        if not is_menu_entry_enabled(self.MENU_ENTRY_NAME, self.event):
            self._forbidden_if_not_admin()


class RHMyContributions(RHDisplayProtectionBase):
    """Display list of current user contributions."""

    MENU_ENTRY_NAME = 'my_contributions'

    def _check_access(self):
        RHDisplayProtectionBase._check_access(self)
        if not session.user:
            raise Forbidden

    def _process(self):
        contribs = get_contributions_for_user(self.event, session.user)
        categorized = defaultdict(set)
        for contrib in contribs:
            added = False
            links = [link for link in contrib.person_links if link.person.user == session.user]
            for link in links:
                if link.is_speaker:
                    categorized['speaker'].add(contrib)
                    added = True
                if link.author_type == AuthorType.primary:
                    categorized['primary'].add(contrib)
                    added = True
                if link.author_type == AuthorType.secondary:
                    categorized['secondary'].add(contrib)
                    added = True
            # Only add contributions to the submitter category if they are not in any other category
            if not added and contrib.can_manage(session.user, 'submit', allow_admin=False, check_parent=False):
                categorized['submitter'].add(contrib)
        return WPMyContributions.render_template('display/user_contribution_list.html', self.event,
                                                 contributions=categorized)


class RHContributionList(RHDisplayProtectionBase):
    """Display list of event contributions."""

    MENU_ENTRY_NAME = 'contributions'
    view_class = WPContributions

    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        self.list_generator = ContributionDisplayListGenerator(event=self.event)

    def _process(self):
        return self.view_class.render_template('display/contribution_list.html', self.event,
                                               timezone=self.event.display_tzinfo,
                                               published=contribution_settings.get(self.event, 'published'),
                                               **self.list_generator.get_list_kwargs())


class RHContributionDisplay(RHContributionDisplayBase):
    """Display page with contribution details."""

    view_class = WPContributions

    def _process(self):
        contrib = (Contribution.query
                   .filter_by(id=self.contrib.id)
                   .options(joinedload('type'),
                            joinedload('session'),
                            joinedload('subcontributions'),
                            joinedload('timetable_entry').lazyload('*'))
                   .one())
        if self.event.type_ == EventType.meeting:
            return redirect(url_for('events.display', self.event, _anchor=contrib.slug))
        can_manage = self.event.can_manage(session.user, permission='contributions')
        owns_abstract = contrib.abstract.user_owns(session.user) if contrib.abstract else None
        field_values = filter_field_values(contrib.field_values, can_manage, owns_abstract)
        return self.view_class.render_template('display/contribution_display.html', self.event,
                                               contribution=contrib,
                                               show_author_link=_author_page_active(self.event),
                                               field_values=field_values,
                                               page_title=contrib.title,
                                               published=contribution_settings.get(self.event, 'published'))


class RHContributionJSON(RHContributionDisplayBase):
    """Return JSON data for a contribution."""

    def _process(self):
        from indico.modules.events.contributions.schemas import FullContributionSchema
        can_manage = self.contrib.can_manage(session.user)
        return FullContributionSchema(context={
            'hide_restricted_data': not can_manage,
            'user_can_manage': can_manage,
            'user_owns_abstract': self.contrib.abstract.user_owns(session.user) if self.contrib.abstract else None,
        }).jsonify(self.contrib)


class RHAuthorList(RHDisplayProtectionBase):
    MENU_ENTRY_NAME = 'author_index'
    view_class = WPAuthorList

    def _process(self):
        authors = _get_persons(self.event, ContributionPersonLink.author_type != AuthorType.none)
        return self.view_class.render_template('display/author_list.html', self.event, authors=authors)


class RHSpeakerList(RHDisplayProtectionBase):
    MENU_ENTRY_NAME = 'speaker_index'
    view_class = WPSpeakerList

    def _process(self):
        speakers = _get_persons(self.event, ContributionPersonLink.is_speaker)
        return self.view_class.render_template('display/speaker_list.html', self.event, speakers=speakers)


class RHContributionAuthor(RHContributionDisplayBase):
    """Display info about an author."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.author
        }
    }

    def _check_access(self):
        RHContributionDisplayBase._check_access(self)
        if not _author_page_active(self.event):
            self._forbidden_if_not_admin()

    def _process_args(self):
        RHContributionDisplayBase._process_args(self)
        self.author = (ContributionPersonLink.query
                       .filter(ContributionPersonLink.author_type != AuthorType.none,
                               ContributionPersonLink.id == request.view_args['person_id'],
                               ContributionPersonLink.contribution == self.contrib)
                       .one())

    def _process(self):
        author_contribs = (Contribution.query.with_parent(self.event)
                           .join(ContributionPersonLink)
                           .options(joinedload('event'))
                           .options(load_only('id', 'title'))
                           .filter(ContributionPersonLink.id == self.author.id,
                                   ContributionPersonLink.author_type != AuthorType.none)
                           .all())
        return WPContributions.render_template('display/contribution_author.html', self.event,
                                               author=self.author, contribs=author_contribs)


class RHContributionExportToPDF(RHContributionDisplayBase):
    def _process(self):
        if not config.LATEX_ENABLED:
            raise NotFound
        pdf = ContribToPDF(self.contrib)
        return send_file('contribution.pdf', pdf.generate(), 'application/pdf')


class RHContributionsExportToPDF(RHContributionList):
    def _process(self):
        if not config.LATEX_ENABLED:
            raise NotFound
        contribs = self.list_generator.get_list_kwargs()['contribs']
        pdf = ContribsToPDF(self.event, contribs)
        return send_file('contributions.pdf', pdf.generate(), 'application/pdf')


@allow_signed_url
class RHContributionExportToICAL(RHContributionDisplayBase):
    """Export contribution to ICS."""

    def _process(self):
        if not self.contrib.is_scheduled:
            raise NotFound('This contribution is not scheduled')
        return send_file('contribution.ics', BytesIO(contribution_to_ical(self.contrib)), 'text/calendar')


class RHContributionListFilter(RHContributionList):
    """Display dialog with filters."""

    def _process(self):
        return RH._process(self)

    def _process_GET(self):
        list_config = self.list_generator._get_config()
        return jsonify_template('events/contributions/contrib_list_filter.html',
                                visible_items=list_config.get('items', ()),
                                filters=self.list_generator.list_config['filters'],
                                static_items=self.list_generator.static_items,
                                contrib_fields=[],
                                extra_filters=self.list_generator.extra_filters,
                                has_types=self.event.contribution_types.has_rows(),
                                management=False)

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(**self.list_generator.render_contribution_list())


class RHContributionListDisplayStaticURL(RHContributionList):
    """Generate static URL for the current set of filters."""

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHSubcontributionDisplay(RHDisplayEventBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.subcontrib
        }
    }
    view_class = WPContributions

    def _check_access(self):
        if not self.subcontrib.can_access(session.user):
            # perform event access check since it may send the user to the access key or registration page
            RHDisplayEventBase._check_access(self)
            raise Forbidden
        published = contribution_settings.get(self.event, 'published')
        if (not published and not self.event.can_manage(session.user, permission='contributions')
                and not self.subcontrib.is_user_associated(session.user)):
            raise NotFound(_('The contributions of this event have not been published yet.'))

    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        self.subcontrib = SubContribution.get_or_404(request.view_args['subcontrib_id'], is_deleted=False)

    def _process(self):
        if self.event.type_ == EventType.meeting:
            return redirect(url_for('events.display', self.event, _anchor=self.subcontrib.slug))
        return self.view_class.render_template('display/subcontribution_display.html', self.event,
                                               subcontrib=self.subcontrib)
