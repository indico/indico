# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import random
from io import BytesIO

from flask import flash, redirect, request, session
from marshmallow import EXCLUDE
from PIL import Image
from sqlalchemy.orm import joinedload, load_only, undefer_group
from webargs import fields
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core.config import config
from indico.core.db import db
from indico.core.permissions import get_principal_permissions, update_permissions
from indico.modules.categories import logger
from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.categories.fields import EventRequestList
from indico.modules.categories.forms import (CategoryIconForm, CategoryLogoForm, CategoryProtectionForm,
                                             CategoryRoleForm, CategorySettingsForm, CreateCategoryForm,
                                             SplitCategoryForm)
from indico.modules.categories.models.categories import Category
from indico.modules.categories.models.event_move_request import EventMoveRequest, MoveRequestState
from indico.modules.categories.models.roles import CategoryRole
from indico.modules.categories.operations import (create_category, delete_category, move_category, update_category,
                                                  update_category_protection, update_event_move_request)
from indico.modules.categories.schemas import EventMoveRequestSchema
from indico.modules.categories.util import get_image_data, serialize_category_role
from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events import Event
from indico.modules.events.notifications import notify_move_request_closure, notify_move_request_creation
from indico.modules.events.operations import create_event_request
from indico.modules.logs.models.entries import CategoryLogRealm, LogKind
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence, ReservationOccurrenceLink
from indico.modules.users import User
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.util.marshmallow import ModelField, PrincipalList, not_empty
from indico.util.roles import ExportRoleMembersMixin, ImportRoleMembersMixin, RolesAPIMixin
from indico.util.string import crc32, natural_sort_key
from indico.web.args import parser, use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.forms.colors import get_role_colors
from indico.web.forms.fields.principals import serialize_principal
from indico.web.util import jsonify_data, jsonify_form, jsonify_template, url_for_index


CATEGORY_ICON_DIMENSIONS = (16, 16)
MAX_CATEGORY_LOGO_DIMENSIONS = (200, 200)


def _get_roles(category):
    return (CategoryRole.query.with_parent(category).options(joinedload('members')).all())


def _render_roles(category):
    tpl = get_template_module('events/roles/_roles.html')
    return tpl.render_roles(_get_roles(category), email_button=False)


def _render_role(role, collapsed=True):
    tpl = get_template_module('events/roles/_roles.html')
    return tpl.render_role(role, collapsed=collapsed, email_button=False)


class RHManageCategoryContent(RHManageCategoryBase):
    @property
    def _category_query_options(self):
        children_strategy = joinedload('children')
        children_strategy.undefer('deep_children_count')
        children_strategy.undefer('deep_events_count')
        return (children_strategy,)

    def _process(self):
        page = request.args.get('page', '1')
        order_columns = {'start_dt': Event.start_dt, 'title': db.func.lower(Event.title)}
        direction = 'desc' if request.args.get('desc', '1') == '1' else 'asc'
        order_column = order_columns[request.args.get('order', 'start_dt')]
        query = (Event.query.with_parent(self.category)
                 .options(joinedload('series'), undefer_group('series'), joinedload('pending_move_request'),
                          load_only('id', 'category_id', 'created_dt', 'end_dt', 'protection_mode', 'start_dt',
                                    'title', 'type_', 'series_pos', 'series_count', 'visibility'))
                 .order_by(getattr(order_column, direction)())
                 .order_by(Event.id))
        if page == 'all':
            events = query.paginate(show_all=True)
        else:
            events = query.paginate(page=int(page))
        return WPCategoryManagement.render_template('management/content.html', self.category, 'content',
                                                    subcategories=self.category.children,
                                                    events=events, page=page,
                                                    order_column=request.args.get('order', 'start_dt'),
                                                    direction=direction)


class RHManageCategorySettings(RHManageCategoryBase):
    def _process(self):
        kwargs = {
            'meeting_theme': self.category.default_event_themes['meeting'],
            'lecture_theme': self.category.default_event_themes['lecture']
        }

        if config.ENABLE_GOOGLE_WALLET:
            kwargs |= self.category.google_wallet_settings
        if config.ENABLE_APPLE_WALLET:
            kwargs |= self.category.apple_wallet_settings
        defaults = FormDefaults(self.category, **kwargs)
        form = CategorySettingsForm(obj=defaults, category=self.category)
        icon_form = CategoryIconForm(obj=self.category)
        logo_form = CategoryLogoForm(obj=self.category)

        if form.validate_on_submit():
            update_category(self.category, form.data, skip={'meeting_theme', 'lecture_theme'})
            self.category.default_event_themes = {
                'meeting': form.meeting_theme.data,
                'lecture': form.lecture_theme.data
            }
            flash(_('Category settings saved!'), 'success')
            return redirect(url_for('.manage_settings', self.category))
        else:
            if self.category.icon_metadata:
                icon_form.icon.data = self.category
            if self.category.logo_metadata:
                logo_form.logo.data = self.category
        return WPCategoryManagement.render_template('management/settings.html', self.category, 'settings', form=form,
                                                    icon_form=icon_form, logo_form=logo_form)


class RHAPIEventMoveRequests(RHManageCategoryBase):
    def _process_GET(self):
        move_requests = self.category.event_move_requests.filter(EventMoveRequest.state == MoveRequestState.pending)
        return EventMoveRequestSchema(many=True).jsonify(move_requests)

    @use_kwargs({
        'accept': fields.Bool(required=True),
        'reason': fields.String(load_default=None)
    })
    def _process_POST(self, accept, reason):
        move_requests = parser.parse({
            'requests': EventRequestList(required=True, category=self.category, validate=not_empty)
        }, unknown=EXCLUDE)['requests']

        for rq in move_requests:
            update_event_move_request(rq, accept, reason)
        notify_move_request_closure(move_requests, accept, reason)

        return '', 204


class RHManageCategoryModeration(RHManageCategoryBase):
    def _process(self):
        return WPCategoryManagement.render_template('management/moderation.html', self.category, 'moderation')


class RHCategoryImageUploadBase(RHManageCategoryBase):
    IMAGE_TYPE = None
    SAVED_FLASH_MSG = None
    DELETED_FLASH_MSG = None

    def _resize(self, img):
        return img

    def _set_image(self, data, metadata):
        raise NotImplementedError

    def _process_POST(self):
        f = request.files[self.IMAGE_TYPE]
        try:
            img = Image.open(f)
        except OSError:
            flash(_('You cannot upload this file as an icon/logo.'), 'error')
            return jsonify_data(content=None)
        if img.format.lower() not in {'jpeg', 'png', 'gif'}:
            flash(_('The file has an invalid format ({format})').format(format=img.format), 'error')
            return jsonify_data(content=None)
        if img.mode == 'CMYK':
            flash(_('The image you uploaded is using the CMYK colorspace and has been converted to RGB.  '
                    'Please check if the colors are correct and convert it manually if necessary.'), 'warning')
            img = img.convert('RGB')
        img = self._resize(img)
        image_bytes = BytesIO()
        img.save(image_bytes, 'PNG')
        image_bytes.seek(0)
        content = image_bytes.read()
        metadata = {
            'hash': crc32(content),
            'size': len(content),
            'filename': os.path.splitext(secure_filename(f.filename, self.IMAGE_TYPE))[0] + '.png',
            'content_type': 'image/png'
        }
        self._set_image(content, metadata)
        flash(self.SAVED_FLASH_MSG, 'success')
        logger.info(f"New {self.IMAGE_TYPE} '%s' uploaded by %s (%s)", f.filename, session.user, self.category)
        return jsonify_data(content=get_image_data(self.IMAGE_TYPE, self.category))

    def _process_DELETE(self):
        self._set_image(None, None)
        flash(self.DELETED_FLASH_MSG, 'success')
        logger.info(f'{self.IMAGE_TYPE.title()} of %s deleted by %s', self.category, session.user)
        return jsonify_data(content=None)


class RHManageCategoryIcon(RHCategoryImageUploadBase):
    IMAGE_TYPE = 'icon'
    SAVED_FLASH_MSG = _('New icon saved')
    DELETED_FLASH_MSG = _('Icon deleted')

    def _resize(self, img):
        if img.size != CATEGORY_ICON_DIMENSIONS:
            img = img.resize(CATEGORY_ICON_DIMENSIONS, Image.LANCZOS)
        return img

    def _set_image(self, data, metadata):
        self.category.icon = data
        self.category.icon_metadata = metadata


class RHManageCategoryLogo(RHCategoryImageUploadBase):
    IMAGE_TYPE = 'logo'
    SAVED_FLASH_MSG = _('New logo saved')
    DELETED_FLASH_MSG = _('Logo deleted')

    def _resize(self, logo):
        width, height = logo.size
        max_width, max_height = MAX_CATEGORY_LOGO_DIMENSIONS
        if width > max_width:
            ratio = max_width / float(width)
            width = int(width * ratio)
            height = int(height * ratio)
        if height > max_height:
            ratio = max_height / float(height)
            width = int(width * ratio)
            height = int(height * ratio)
        if (width, height) != logo.size:
            logo = logo.resize((width, height), Image.LANCZOS)
        return logo

    def _set_image(self, data, metadata):
        self.category.logo = data
        self.category.logo_metadata = metadata


class RHManageCategoryProtection(RHManageCategoryBase):
    def _process(self):
        form = CategoryProtectionForm(obj=self._get_defaults(), category=self.category)
        if form.validate_on_submit():
            update_permissions(self.category, form)
            update_category_protection(self.category,
                                       {'protection_mode': form.protection_mode.data,
                                        'own_no_access_contact': form.own_no_access_contact.data,
                                        'event_creation_mode': form.event_creation_mode.data,
                                        'visibility': form.visibility.data})
            flash(_('Protection settings of the category have been updated'), 'success')
            return redirect(url_for('.manage_protection', self.category))
        return WPCategoryManagement.render_template('management/category_protection.html', self.category, 'protection',
                                                    form=form)

    def _get_defaults(self):
        permissions = [[serialize_principal(p.principal), list(get_principal_permissions(p, Category))]
                       for p in self.category.acl_entries]
        permissions = [item for item in permissions if item[1]]
        return FormDefaults(self.category, permissions=permissions)


class RHCreateCategory(RHManageCategoryBase):
    def _sort_key(self, category):
        return natural_sort_key(category.title), category.id

    def _get_sort_order(self, categories):
        sorted_categories = sorted(self.category.children, key=self._sort_key)
        if categories == sorted_categories:
            return 'asc'
        elif categories == sorted_categories[::-1]:
            return 'desc'
        return None

    def _process(self):
        form = CreateCategoryForm()
        if form.validate_on_submit():
            sort_order = self._get_sort_order(self.category.children)
            new_category = create_category(self.category, form.data)
            if sort_order is not None:
                reverse = sort_order == 'desc'
                subcategories = sorted(self.category.children, key=self._sort_key, reverse=reverse)
                for position, category in enumerate(subcategories, start=1):
                    category.position = position
            flash(_('Category "{}" has been created.').format(new_category.title), 'success')
            return jsonify_data(flash=False, redirect=url_for('.manage_settings', new_category))
        return jsonify_form(form)


class RHDeleteCategory(RHManageCategoryBase):
    def _process(self):
        if self.category.is_root:
            raise BadRequest('The root category cannot be deleted')
        if not self.category.is_empty:
            raise BadRequest('Cannot delete a non-empty category')
        delete_category(self.category)
        parent = self.category.parent
        if parent.can_manage(session.user):
            url = url_for('.manage_content', parent)
        elif parent.can_access(session.user):
            url = url_for('.display', parent)
        else:
            url = url_for_index()
        if request.is_xhr:
            return jsonify_data(flash=False, redirect=url, is_parent_empty=parent.is_empty)
        else:
            flash(_('Category "{}" has been deleted.').format(self.category.title), 'success')
            return redirect(url)


class RHMoveCategoryBase(RHManageCategoryBase):
    def _process_args(self):
        RHManageCategoryBase._process_args(self)
        target_category_id = request.form.get('target_category_id')
        if target_category_id is None:
            self.target_category = None
        else:
            self.target_category = Category.get_or_404(int(target_category_id), is_deleted=False)
            if not self.target_category.can_manage(session.user):
                raise Forbidden(_('You are not allowed to manage the selected destination.'))


class RHMoveCategory(RHMoveCategoryBase):
    """Move a category."""

    def _process_args(self):
        RHMoveCategoryBase._process_args(self)
        if self.category.is_root:
            raise BadRequest(_('Cannot move the root category.'))
        if self.target_category is not None:
            if self.target_category == self.category:
                raise BadRequest(_('Cannot move the category inside itself.'))
            if self.target_category.parent_chain_query.filter(Category.id == self.category.id).count():
                raise BadRequest(_('Cannot move the category in a descendant of itself.'))

    def _process(self):
        move_category(self.category, self.target_category)
        flash(_('Category "{}" moved to "{}".').format(self.category.title, self.target_category.title), 'success')
        return jsonify_data(flash=False)


class RHDeleteSubcategories(RHManageCategoryBase):
    """Bulk-delete subcategories."""

    def _process_args(self):
        RHManageCategoryBase._process_args(self)
        self.subcategories = (Category.query
                              .with_parent(self.category)
                              .filter(Category.id.in_(map(int, request.form.getlist('category_id'))))
                              .all())

    def _process(self):
        if 'confirmed' in request.form:
            for subcategory in self.subcategories:
                if not subcategory.is_empty:
                    raise BadRequest(f'Category "{subcategory.title}" is not empty')
                delete_category(subcategory)
            return jsonify_data(flash=False, is_empty=self.category.is_empty)
        return jsonify_template('categories/management/delete_categories.html', categories=self.subcategories,
                                category_ids=[x.id for x in self.subcategories])


class RHMoveSubcategories(RHMoveCategoryBase):
    """Bulk-move subcategories."""

    def _process_args(self):
        RHMoveCategoryBase._process_args(self)
        subcategory_ids = request.values.getlist('category_id', type=int)
        self.subcategories = (Category.query.with_parent(self.category)
                              .filter(Category.id.in_(subcategory_ids))
                              .order_by(Category.title)
                              .all())
        if self.target_category is not None:
            if self.target_category.id in subcategory_ids:
                raise BadRequest(_('Cannot move a category inside itself.'))
            if self.target_category.parent_chain_query.filter(Category.id.in_(subcategory_ids)).count():
                raise BadRequest(_('Cannot move a category in a descendant of itself.'))

    def _process(self):
        for subcategory in self.subcategories:
            move_category(subcategory, self.target_category)
        flash(ngettext('{0} category moved to "{1}".', '{0} categories moved to "{1}".', len(self.subcategories))
              .format(len(self.subcategories), self.target_category.title), 'success')
        return jsonify_data(flash=False)


class RHSortSubcategories(RHManageCategoryBase):
    @use_kwargs({
        'categories': fields.List(fields.Int(), required=True)
    })
    def _process(self, categories):
        subcategories = {category.id: category for category in self.category.children}
        for position, id_ in enumerate(categories, start=1):
            subcategories[id_].position = position
        self.category.log(CategoryLogRealm.category, LogKind.change, 'Content', 'Subcategories sorted', session.user)
        return jsonify_data(flash=False)


class RHManageCategorySelectedEventsBase(RHManageCategoryBase):
    """Base RH to manage selected events in a category."""

    @use_kwargs({
        'all_selected': fields.Bool(load_default=False),
        'event_ids': fields.List(fields.Int(), data_key='event_id', load_default=lambda: []),
    })
    def _process_args(self, all_selected, event_ids):
        RHManageCategoryBase._process_args(self)
        query = (Event.query
                 .with_parent(self.category)
                 .order_by(Event.start_dt.desc()))
        if not all_selected:
            query = query.filter(Event.id.in_(event_ids))
        self.events = query.all()


class RHDeleteEvents(RHManageCategorySelectedEventsBase):
    """Delete multiple events."""

    def _process(self):
        is_submitted = 'confirmed' in request.form
        if not is_submitted:
            # find out which active booking occurrences are linked to the events in question
            num_booking_occurrences = (ReservationOccurrence.query
                                       .join(ReservationOccurrenceLink)
                                       .join(Event, Event.id == ReservationOccurrenceLink.linked_event_id)
                                       .filter(Event.id.in_(e.id for e in self.events), ReservationOccurrence.is_valid)
                                       .count())
            return jsonify_template('events/management/delete_events.html',
                                    events=self.events, num_booking_occurrences=num_booking_occurrences)
        for ev in self.events[:]:
            ev.delete('Bulk-deleted by category manager', session.user)
        flash(ngettext('You have deleted one event', 'You have deleted {} events', len(self.events))
              .format(len(self.events)), 'success')
        return jsonify_data(flash=False, redirect=url_for('.manage_content', self.category))


class RHSplitCategory(RHManageCategorySelectedEventsBase):
    def _process_args(self):
        RHManageCategorySelectedEventsBase._process_args(self)
        self.cat_events = set(self.category.events)
        self.sel_events = set(self.events)

    def _process(self):
        form = SplitCategoryForm(formdata=request.form)
        if form.validate_on_submit():
            self._move_events(self.sel_events, form.first_category.data)
            if not form.all_selected.data and form.second_category.data:
                self._move_events(self.cat_events - self.sel_events, form.second_category.data)
            if form.all_selected.data or not form.second_category.data:
                flash(_('Your events have been moved to the category "{}"')
                      .format(form.first_category.data), 'success')
            else:
                flash(_('Your events have been split into the categories "{}" and "{}"')
                      .format(form.first_category.data, form.second_category.data), 'success')
            return jsonify_data(flash=False, redirect=url_for('.manage_content', self.category))
        return jsonify_form(form, submit=_('Split'))

    def _move_events(self, events, category_title):
        category = create_category(self.category, {'title': category_title})
        for event in events:
            event.move(category)
        db.session.flush()


class RHMoveEvents(RHManageCategorySelectedEventsBase):
    @use_kwargs({
        'target_category': ModelField(Category, filter_deleted=True, required=True, data_key='target_category_id'),
        'comment': fields.String(load_default=''),
    })
    def _process_args(self, target_category, comment):
        RHManageCategorySelectedEventsBase._process_args(self)
        self.target_category = target_category
        self.comment = comment

    def _check_access(self):
        RHManageCategorySelectedEventsBase._check_access(self)
        if (not self.target_category.can_create_events(session.user)
                and not self.target_category.can_propose_events(session.user)):
            raise Forbidden(_('You may not move events to this category.'))

    def _process(self):
        if self.target_category.can_create_events(session.user):
            for event in self.events:
                event.move(self.target_category)
            flash(ngettext('You have moved {count} event to the category "{cat}"',
                           'You have moved {count} events to the category "{cat}"', len(self.events))
                  .format(count=len(self.events), cat=self.target_category.title), 'success')
        else:
            for event in self.events:
                create_event_request(event, self.target_category, self.comment)
            notify_move_request_creation(self.events, self.target_category, self.comment)
            flash(ngettext('You have requested the move of {count} event to the category "{cat}"',
                           'You have requested the move of {count} events to the category "{cat}"', len(self.events))
                  .format(count=len(self.events), cat=self.target_category.title), 'success')
        return jsonify_data(flash=False)


class RHCategoryRoles(RHManageCategoryBase):
    """Category role management."""

    def _process(self):
        return WPCategoryManagement.render_template('management/roles.html', self.category, 'roles',
                                                    roles=_get_roles(self.category))


class RHAddCategoryRole(RHManageCategoryBase):
    """Add a new category role."""

    def _process(self):
        form = CategoryRoleForm(category=self.category, color=self._get_color())
        if form.validate_on_submit():
            role = CategoryRole(category=self.category)
            form.populate_obj(role)
            db.session.flush()
            logger.info('Category role %r created by %r', role, session.user)
            self.category.log(CategoryLogRealm.category, LogKind.positive, 'Roles',
                              f'Added role: "{role.name}"', session.user)
            return jsonify_data(html=_render_roles(self.category), role=serialize_category_role(role))
        return jsonify_form(form)

    def _get_color(self):
        used_colors = {role.color for role in self.category.roles}
        unused_colors = set(get_role_colors()) - used_colors
        return random.choice(tuple(unused_colors) or get_role_colors())


class RHManageCategoryRole(RHManageCategoryBase):
    """Base class to manage a specific category role."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.role
        }
    }

    def _process_args(self):
        RHManageCategoryBase._process_args(self)
        self.role = CategoryRole.get_or_404(request.view_args['role_id'])


class RHEditCategoryRole(RHManageCategoryRole):
    """Edit a category role."""

    def _process(self):
        form = CategoryRoleForm(obj=self.role, category=self.category)
        if form.validate_on_submit():
            form.populate_obj(self.role)
            db.session.flush()
            logger.info('Category role %r updated by %r', self.role, session.user)
            self.category.log(CategoryLogRealm.category, LogKind.change, 'Roles',
                              f'Updated role: "{self.role.name}"', session.user)
            return jsonify_data(html=_render_role(self.role))
        return jsonify_form(form)


class RHDeleteCategoryRole(RHManageCategoryRole):
    """Delete a category role."""

    def _process(self):
        db.session.delete(self.role)
        logger.info('Category role %r deleted by %r', self.role, session.user)
        self.category.log(CategoryLogRealm.category, LogKind.negative, 'Roles',
                          f'Deleted role: "{self.role.name}"', session.user)
        return jsonify_data(html=_render_roles(self.category))


class RHRemoveCategoryRoleMember(RHManageCategoryRole):
    """Remove a user from a category role."""

    normalize_url_spec = dict(RHManageCategoryRole.normalize_url_spec, preserved_args={'user_id'})

    def _process_args(self):
        RHManageCategoryRole._process_args(self)
        self.user = User.get_or_404(request.view_args['user_id'])

    def _process(self):
        if self.user in self.role.members:
            self.role.members.remove(self.user)
            logger.info('User %r removed from role %r by %r', self.user, self.role, session.user)
            self.category.log(CategoryLogRealm.category, LogKind.negative, 'Roles',
                              f'Removed user from role "{self.role.name}"', session.user,
                              data={'Name': self.user.full_name, 'Email': self.user.email})
        return jsonify_data(html=_render_role(self.role, collapsed=False))


class RHAddCategoryRoleMembers(RHManageCategoryRole):
    """Add users to a category role."""

    @use_kwargs({
        'users': PrincipalList(required=True, allow_external_users=True),
    })
    def _process(self, users):
        for user in users - self.role.members:
            self.role.members.add(user)
            logger.info('User %r added to role %r by %r', user, self.role, session.user)
            self.category.log(CategoryLogRealm.category, LogKind.positive, 'Roles',
                              f'Added user to role "{self.role.name}"', session.user,
                              data={'Name': user.full_name, 'Email': user.email})
        return jsonify_data(html=_render_role(self.role, collapsed=False))


class RHCategoryRoleMembersImportCSV(ImportRoleMembersMixin, RHManageCategoryRole):
    """Add users to a category role from CSV."""

    logger = logger
    log_realm = CategoryLogRealm.category


class RHCategoryRoleMembersExportCSV(ExportRoleMembersMixin, RHManageCategoryRole):
    """Export category role members to a CSV."""


class RHCategoryRolesAPI(RolesAPIMixin, RHManageCategoryBase):
    """Export category role members to JSON."""

    def _process_args(self):
        RHManageCategoryBase._process_args(self)
        self.roles = CategoryRole.query.with_parent(self.category).options(joinedload('members'))
