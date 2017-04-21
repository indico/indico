# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals, division

import math
import mimetypes
from operator import attrgetter

import click
from pytz import utc

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import update_session_options
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.events.registration.settings import (event_badge_settings, DEFAULT_BADGE_SETTINGS)
from indico.modules.designer import PageOrientation, PageSize
from indico.modules.designer.models.images import DesignerImageFile
from indico.modules.designer.models.templates import DesignerTemplate, TemplateType
from indico.modules.users import User
from indico.util.console import verbose_iterator, cformat
from indico.util.fs import secure_filename
from indico.util.string import to_unicode
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import LocalFileImporterMixin


def _lower(text):
    return to_unicode(text).lower()


def _convert_font_size(size):
    if size.endswith('pt'):
        return size
    else:
        return FONT_SIZE_MAPPING[size]


def _convert_font_family(name):
    if name in FONT_FAMILY_MAPPING:
        return FONT_FAMILY_MAPPING[name]
    else:
        print(cformat("%{yellow!}--%{reset} Unknown font: '{}'. Using 'sans-serif' instead.").format(name))
        return 'sans-serif'


ITEM_KEY_MAPPING = {
    'id': ('id', int),
    'text': ('text', to_unicode),
    'x': ('x', float),
    'y': ('y', float),
    'fontFamily': ('font_family', _convert_font_family),
    'fontSize': ('font_size', _convert_font_size),
    'color': ('color', _lower),
    'width': ('width', int),
    'bold': ('bold', bool),
    'italic': ('italic', bool),
    'textAlign': ('text_align', _lower)
}

ITEM_TYPE_MAPPING = {
    'Title': 'title',
    'Full Name': 'full_name',
    'Full Name (w/o title)': 'full_name_no_title',
    'Full Name B': 'full_name_b',
    'Full Name B (w/o title)': 'full_name_b_no_title',
    'Full Name C': 'full_name_c',
    'Full Name C (w/o title)': 'full_name_c_no_title',
    'Full Name D (abbrev)': 'full_name_d',
    'Full Name D (abbrev, w/o title)': 'full_name_d_no_title',
    'First Name': 'first_name',
    'Surname': 'last_name',
    'Institution': 'affiliation',
    'Position': 'position',
    'Address': 'address',
    'Country': 'country',
    'Phone': 'phone',
    'Email': 'email',
    'Amount': 'amount',
    'Conference Name': 'event_title',
    'Conference Dates': 'event_dates',
    'Lecture Category': 'category_title',
    'Lecture Name': 'event_title',
    'Lecture Date(s)': 'event_dates',
    'Speaker(s)': 'event_speakers',
    'Description': 'event_description',
    'Location (name)': 'event_venue',
    'Location (address)': 'event_address',
    'Location (room)': 'event_room',
    'Organisers': 'event_organizers',
    'Fixed Text': 'fixed'
}

FONT_SIZE_MAPPING = {
    'xx-small': '7pt',
    'x-small': '7.5pt',
    'small': '10pt',
    'medium': '12pt',
    'large': '13.5pt',
    'x-large': '18pt',
    'xx-large': '24pt'
}

FONT_FAMILY_MAPPING = {
    'Sans': 'sans-serif',
    'Times New Roman': 'serif',
    'Courier': 'courier',
    'LinuxLibertine': 'LinuxLibertine',
    'Kochi-Mincho': 'Kochi-Mincho',
    'Kochi-Gothic': 'Kochi-Gothic',
    'Uming-CN': 'Uming-CN'
}


def _sane_float(num):
    return float(num) if not math.isnan(num) else None


BADGE_CONFIG_MAPPING = {
    'top_margin': ('__BadgePDFOptions_topMargin', float),
    'bottom_margin': ('__BadgePDFOptions_bottomMargin', float),
    'left_margin': ('__BadgePDFOptions_leftMargin', float),
    'right_margin': ('__BadgePDFOptions_rightMargin', float),
    'margin_columns': ('__BadgePDFOptions_marginColumns', float),
    'margin_rows': ('__BadgePDFOptions_marginRows', float),
    'page_size': ('_pageSize', lambda s: getattr(PageSize, s.title())),
    'page_orientation': ('_landscape', lambda x: PageOrientation.landscape if x else PageOrientation.portrait),
    'dashed_border': ('_drawDashedRectangles', bool)
}


def _to_utc(dt):
    return dt.astimezone(utc) if dt else None


class TemplateMigrationBase(object):
    def __init__(self, importer, conf, event, janitor_user):
        self.importer = importer
        self.conf = conf
        self.event = event
        self.janitor_user = janitor_user

    @property
    def event_id(self):
        return self.event.id if self.event else 'default'

    def run(self):
        manager = getattr(self.conf, '_Conference__{}TemplateManager'.format(self.obj_type), None)
        if not manager:
            # Not worth reporting this as a warning, since it's extremely common
            return
        self._migrate_data(manager)

    def _translate_tpl_item(self, item):
        result = {}
        new_type = None

        if 'key' in item:
            new_type = ITEM_TYPE_MAPPING.get(item['key'])
        elif 'name' in item:
            new_type = ITEM_TYPE_MAPPING.get(item['name'])

        item.pop('key', None)
        item.pop('name', None)

        if new_type is None:
            self.importer.print_warning(cformat('%{yellow!}Template attribute type unknown'), event_id=self.event_id)
            return

        result['type'] = new_type

        for old_k, old_v in item.viewitems():
            if old_k in {'selected', 'textAlignIndex', 'fontFamilyIndex', 'fontSizeIndex', 'styleIndex', 'colorIndex'}:
                continue
            new_k, datatype = ITEM_KEY_MAPPING[old_k]
            result[new_k] = datatype(old_v)
        diff = {v[0] for v in ITEM_KEY_MAPPING.viewvalues()} - set(result)
        if diff:
            self.importer.print_warning(cformat('%{yellow!}Template item misses some attributes: {}').format(diff),
                                        event_id=self.event_id)

        # we should store every position/size at 50px/cm
        # previously, posters were at 25px/cm, hence the multiplier
        result['x'] *= self.zoom_multiplier
        result['y'] *= self.zoom_multiplier
        result['width'] *= self.zoom_multiplier
        return result

    def _translate_tpl_data(self, tpl_data):
        width = _sane_float(tpl_data[1]['width'])
        height = _sane_float(tpl_data[1]['height'])

        if width is None or height is None:
            self.importer.print_error(cformat('%{red!}Template has invalid dimensions ({}, {})').format(width, height),
                                      event_id=self.event_id)
            return None
        return {
            'title': convert_to_unicode(tpl_data[0]),
            'data': {
                'width': width * self.zoom_multiplier,
                'height': _sane_float(tpl_data[1]['height']) * self.zoom_multiplier,
                'items': [self._translate_tpl_item(item) for item in tpl_data[4]]
            }
        }

    def _migrate_background(self, old_bg, tpl):
        storage_backend, storage_path, size = self.importer._get_local_file_info(old_bg)
        if storage_path is None:
            self.importer.print_error(cformat('%{red!}File not found on disk; skipping it [{}]')
                                      .format(convert_to_unicode(old_bg.fileName)),
                                      event_id=self.event_id)
            return
        content_type = mimetypes.guess_type(old_bg.fileName)[0] or 'application/octet-stream'
        filename = secure_filename(convert_to_unicode(old_bg.fileName), 'attachment')
        return DesignerImageFile(filename=filename, content_type=content_type, size=size,
                                 storage_backend=storage_backend, storage_file_id=storage_path)

    def _migrate_templates(self, manager):
        for tpl_id, old_tpl in getattr(manager, '_{}__templates'.format(self.manager_class)).iteritems():
            old_background_map = {}
            old_tpl_data = getattr(old_tpl, '_{}__templateData'.format(self.tpl_class))
            translated_data = self._translate_tpl_data(old_tpl_data)

            if translated_data is None:
                continue

            tpl = DesignerTemplate(type=self.type, **translated_data)
            for old_bg_id, old_bg in getattr(old_tpl, '_{}__backgrounds'.format(self.tpl_class)).viewitems():
                image = self._migrate_background(old_bg, tpl)
                if image:
                    old_background_map[int(old_bg_id)] = image
                    tpl.images.append(image)
                    self.importer.print_success(cformat('\t %{cyan!}{}').format(image), event_id=self.event_id)

            old_positions_map = getattr(old_tpl, '_{}__bgPositions'.format(self.tpl_class), None)
            old_used_bg_id = int(old_tpl_data[3])
            if old_used_bg_id >= 0:
                new_bg_image = old_background_map.get(old_used_bg_id)
                if new_bg_image:
                    tpl.background_image = new_bg_image
                else:
                    self.importer.print_warning(cformat("%{yellow!}Background '{}' not found").format(old_used_bg_id),
                                                event_id=self.event_id)
                if old_positions_map:
                    old_position = old_positions_map.get(old_used_bg_id)
                    if old_position:
                        tpl.data['background_position'] = unicode(old_position.lower())
                    else:
                        self.importer.print_warning(cformat('%{yellow!}Position setting for non-existing background'),
                                                    event_id=self.event_id)
            if 'background_position' not in tpl.data:
                tpl.data['background_position'] = 'stretch'

            if self.event is None:
                tpl.category = Category.get_root()
            else:
                tpl.event_new = self.event
            self.importer.print_success(cformat('%{blue!}{}').format(tpl), event_id=self.event_id)

    def _migrate_data(self, manager):
        self._migrate_templates(manager)


class PosterMigration(TemplateMigrationBase):
    zoom_multiplier = 2
    obj_type = 'poster'
    manager_class = 'PosterTemplateManager'
    tpl_class = 'PosterTemplate'
    type = TemplateType.poster


class BadgeMigration(TemplateMigrationBase):
    zoom_multiplier = 1
    obj_type = 'badge'
    manager_class = 'BadgeTemplateManager'
    tpl_class = 'BadgeTemplate'
    type = TemplateType.badge

    def _migrate_data(self, manager):
        super(BadgeMigration, self)._migrate_data(manager)
        options = getattr(manager, '_PDFOptions', None)
        if options is None:
            if not self.importer.quiet:
                self.importer.print_warning(cformat('%{yellow!}Event has no badge PDF options'), event_id=self.event.id)
            return

        if not self.event:
            # don't migrate server-wide defaults
            return

        new_settings = {}
        for new_prop, (old_prop, datatype) in BADGE_CONFIG_MAPPING.viewitems():
            value = getattr(options, old_prop, None)
            if value is not None:
                value = datatype(value)
                # only record setting value if it's different from the default
                if value != DEFAULT_BADGE_SETTINGS[new_prop]:
                    new_settings[new_prop] = value

        if new_settings:
            event_badge_settings.set_multi(self.event, new_settings)


class BadgePosterImporter(LocalFileImporterMixin, Importer):
    def __init__(self, **kwargs):
        kwargs = self._set_config_options(**kwargs)
        self.janitor_user_id = kwargs.pop('janitor_user_id')
        self.janitor_user = None
        super(BadgePosterImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--janitor-user-id', type=int, required=True, help="The ID of the Janitor user")(command)
        return super(BadgePosterImporter, BadgePosterImporter).decorate_command(command)

    def has_data(self):
        return (DesignerTemplate.query.has_rows() or DesignerImageFile.query.has_rows())

    def migrate(self):
        update_session_options(db, {'expire_on_commit': False})
        self.janitor_user = User.get_one(self.janitor_user_id)
        self.migrate_global_templates()
        self.migrate_event_templates()

    def _migrate_badges(self, conf, event):
        mig = BadgeMigration(self, conf, event, self.janitor_user)
        mig.run()

    def _migrate_posters(self, conf, event):
        mig = PosterMigration(self, conf, event, self.janitor_user)
        mig.run()

    def migrate_global_templates(self):
        self.print_step("Migrating global templates")
        default_conference = getattr(self.zodb_root['MaKaCInfo']['main'], '_defaultConference', None)
        if not default_conference:
            self.print_warning(cformat('%{yellow!}Server has no default conference'))
            return
        self._migrate_badges(default_conference, None)
        self._migrate_posters(default_conference, None)

    def migrate_event_templates(self):
        self.print_step("Migrating event templates")
        for conf, event in committing_iterator(self._iter_events(), n=10000):
            with db.session.no_autoflush:
                self._migrate_badges(conf, event)
                self._migrate_posters(conf, event)
        db.session.commit()

    def _iter_events(self):
        event_it = self.zodb_root['conferences'].itervalues()
        events_query = Event.find(is_deleted=False).order_by(Event.id)
        event_total = Event.query.count()
        all_events = {ev.id: ev for ev in events_query}
        if self.quiet:
            event_it = verbose_iterator(event_it, event_total, attrgetter('id'), lambda x: '')
        for conf in self.flushing_iterator(event_it):
            event = all_events.get(int(conf.id))
            if event is None:
                self.print_error(cformat('%{red!}Event not found in DB'), event_id=conf.id)
                continue
            yield conf, event
