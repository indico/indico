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

import re
import os
from HTMLParser import HTMLParser
from io import BytesIO
from operator import attrgetter

import click
from PIL import Image

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.categories.models.categories import Category
from indico.modules.events.layout import theme_settings
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.users import User
from indico.util.console import cformat
from indico.util.fs import secure_filename
from indico.util.string import crc32, sanitize_email, is_valid_mail
from indico.web.flask.templating import strip_tags

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import patch_default_group_provider, get_archived_file, convert_principal


class CategoryImporter(Importer):
    def __init__(self, **kwargs):
        self.archive_dirs = kwargs.pop('archive_dir')
        self.default_group_provider = kwargs.pop('default_group_provider')
        super(CategoryImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--archive-dir', required=True, multiple=True,
                               help="The base path where resources are stored (ArchiveDir in indico.conf). "
                                    "When used multiple times, the dirs are checked in order until a file is "
                                    "found.")(command)
        command = click.option('--default-group-provider', required=True,
                               help="Name of the default group provider")(command)
        return command

    def has_data(self):
        return Category.query.has_rows()

    @no_autoflush
    def migrate(self):
        self.domain_mapping = {ipng.name.lower(): ipng for ipng in IPNetworkGroup.query}
        with patch_default_group_provider(self.default_group_provider):
            self.migrate_categories()
        self.fix_sequences('categories', {'categories'})

    def _process_icon(self, cat, icon):
        path = get_archived_file(icon, self.archive_dirs)[1]
        if path is None:
            self.print_error(cformat('%{red!}Icon not found on disk; skipping it'), event_id=cat.id)
            return

        try:
            icon_image = Image.open(path)
        except IOError as e:
            self.print_warning("Cannot open {}: {}".format(path, e), event_id=cat.id)
            return

        if icon_image.mode == 'CMYK':
            self.print_warning("Icon is a CMYK {}; converting to RGB".format(icon_image.format), always=False,
                               event_id=cat.id)
            # this may result in wrong colors, but there's not much we can do...
            icon_image = icon_image.convert('RGB')

        if icon_image.size != (16, 16):
            self.print_warning("Icon is {}x{}; resizing to 16x16".format(*icon_image.size), always=False,
                               event_id=cat.id)
            icon_image = icon_image.resize((16, 16), Image.ANTIALIAS)

        icon_bytes = BytesIO()
        icon_image.save(icon_bytes, 'PNG')
        icon_bytes.seek(0)
        icon_content = icon_bytes.read()
        icon_filename = secure_filename(convert_to_unicode(icon.fileName), 'icon')
        icon_filename = os.path.splitext(icon_filename)[0] + '.png'
        cat.icon_metadata = {
            'size': len(icon_content),
            'hash': crc32(icon_content),
            'filename': icon_filename,
            'content_type': 'image/png'
        }
        cat.icon = icon_content

    def convert_principal(self, old_principal):
        principal = convert_principal(old_principal)
        if (principal is None and old_principal.__class__.__name__ in ('Avatar', 'AvatarUserWrapper') and
                'email' in old_principal.__dict__):
            email = convert_to_unicode(old_principal.__dict__['email']).lower()
            principal = User.find_first(~User.is_deleted, User.all_emails.contains(email))
            if principal is not None:
                self.print_warning('Using {} for {} (matched via {})'.format(principal, old_principal, email))
        return principal

    def process_principal(self, cat, legacy_principal, name, color, read_access=None, full_access=None, roles=None):
        principal = self.convert_principal(legacy_principal)
        if principal is None:
            self.print_warning(cformat('%%{%s}{}%%{reset}%%{yellow} does not exist:%%{reset} {}' % color)
                               .format(name, legacy_principal))
            return
        updates = {}
        if read_access:
            updates['read_access'] = True
        if full_access:
            updates['full_access'] = True
        if roles:
            updates['add_roles'] = roles
        cat.update_principal(principal, quiet=True, **updates)
        self.print_msg(cformat('    - %%{%s}[{}]%%{reset} {}' % color).format(name.lower(), principal))

    def _process_protection(self, cat, old_cat):
        ac = old_cat._Category__ac
        cat.event_creation_restricted = bool(old_cat._Category__confCreationRestricted)
        cat.own_no_access_contact = convert_to_unicode(getattr(ac, 'contactInfo', ''))
        if ac._accessProtection == -1 or (old_cat.id == '0' and ac._accessProtection == 0):
            cat.protection_mode = ProtectionMode.public
        elif ac._accessProtection == 0:
            cat.protection_mode = ProtectionMode.inheriting
        elif ac._accessProtection == 1:
            cat.protection_mode = ProtectionMode.protected
        # migrate domain protection only if the category is public; switch to protected in that case
        if cat.protection_mode == ProtectionMode.public and ac.requiredDomains:
            cat.protection_mode = ProtectionMode.protected
            self._process_domains(cat, ac.requiredDomains)
        # read access
        for manager in ac.allowed:
            self.process_principal(cat, manager, 'User', 'cyan', read_access=True)
        # management access
        for manager in ac.managers:
            self.process_principal(cat, manager, 'Manager', 'blue!', full_access=True)
        # creation access
        for creator in old_cat._Category__confCreators:
            self.process_principal(cat, creator, 'Creator', 'magenta', roles={'create'})

    def _process_domains(self, cat, old_domains):
        for old_domain in old_domains:
            network = self.domain_mapping[convert_to_unicode(old_domain.name).lower()]
            cat.update_principal(network, read_access=True, quiet=True)

    def _process_default_themes(self, old_cat):
        default_themes = {
            'meeting': theme_settings.defaults['meeting'],
            'lecture': theme_settings.defaults['lecture']
        }
        old_default_styles = getattr(old_cat, '_defaultStyle', None)
        if old_default_styles:
            if not old_default_styles['simple_event']:
                pass
            elif old_default_styles['simple_event'] in theme_settings.get_themes_for('simple_event'):
                default_themes['lecture'] = old_default_styles['simple_event']
            else:
                self.print_warning('Invalid lecture theme: {}'.format(old_default_styles['simple_event']),
                                   always=False, event_id=old_cat.id)
            if not old_default_styles['meeting']:
                pass
            elif old_default_styles['meeting'] in theme_settings.get_themes_for('meeting'):
                default_themes['meeting'] = old_default_styles['meeting']
            else:
                self.print_warning('Invalid meeting theme: {}'.format(old_default_styles['meeting']),
                                   always=False, event_id=old_cat.id)
        return default_themes

    def _fix_title(self, title, categ_id, _ws_re=re.compile(r'\s+'),
                   _status_re=re.compile(r'<font[^>]+>\s*(open|closed)\s*$')):
        orig = title
        title = _status_re.sub(r'(\1)', title)  # XXX: remove for 2.0; only needed for a CERN indico catgory
        title = HTMLParser().unescape(strip_tags(title))
        title = _ws_re.sub(' ', title).strip()
        if title != orig:
            self.print_warning('Sanitized category title', event_id=categ_id)
            self.print_warning(cformat('%{red!}OLD: {}').format(orig))
            self.print_warning(cformat('%{green!}NEW: {}').format(title))
        return title

    def _migrate_category(self, old_cat, position):
        # unlimited visibility is 999 but we have a 994 for some reason.. since nobody
        # has 900 levels of nesting we can just go for that threshold instead
        visibility = None if old_cat._visibility > 900 else old_cat._visibility
        if visibility == 0:
            self.print_warning("Raising visibility from 'invisible' to 'category-only'", event_id=old_cat.id)
            visibility = 1
        emails = re.split(r'[\s;,]+', convert_to_unicode(getattr(old_cat, '_notifyCreationList', '')))
        emails = {sanitize_email(email).lower() for email in emails}
        emails = sorted(email for email in emails if is_valid_mail(email, False))
        default_themes = self._process_default_themes(old_cat)
        title = self._fix_title(convert_to_unicode(old_cat.name), old_cat.id)
        cat = Category(id=int(old_cat.id), position=position, title=title,
                       description=convert_to_unicode(old_cat.description), visibility=visibility,
                       timezone=convert_to_unicode(old_cat._timezone), event_creation_notification_emails=emails,
                       default_event_themes=default_themes,
                       suggestions_disabled=getattr(old_cat, '_suggestions_disabled', False))
        if not self.quiet:
            self.print_success(cat.title, event_id=cat.id)
        if old_cat._icon:
            self._process_icon(cat, old_cat._icon)
        self._process_protection(cat, old_cat)
        cat.children = [(self._migrate_category(old_subcat, i))
                        for i, old_subcat in enumerate(sorted(old_cat.subcategories.itervalues(),
                                                              key=attrgetter('_order')), 1)]
        return cat

    def migrate_categories(self):
        self.print_step("Migrating categories")
        old_root = self.zodb_root['rootCategory']
        assert old_root.id == '0'
        root = self._migrate_category(old_root, 1)
        db.session.add(root)
        db.session.commit()
