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

from operator import attrgetter

from indico.core.db import db
from indico.modules.events.layout.models.menu import MenuEntry, MenuEntryType, MenuPage
from indico.util.console import verbose_iterator, cformat
from indico.util.struct.iterables import committing_iterator
from indico.web.flask.templating import strip_tags
from indico_zodbimport import Importer, convert_to_unicode


class _AltString(object):
    def __init__(self, *strings):
        self.strings = set(strings)

    def __eq__(self, other):
        return other in self.strings

    def __ne__(self, other):
        return not (self == other)


MENU_ENTRY_NAME_MAP = {
    'overview': 'overview',
    'programme': 'program',
    'manageTrack': 'program_my_tracks',
    'CFA': 'call_for_abstracts',
    'ViewAbstracts': 'user_abstracts',
    'SubmitAbstract': 'abstract_submission',
    'timetable': 'timetable',
    'contributionList': 'contributions',
    'authorIndex': 'author_index',
    'speakerIndex': 'speaker_index',
    'mystuff': 'my_conference',
    'mytracks': 'my_tracks',
    'mysessions': 'my_sessions',
    'mycontribs': 'my_contributions',
    'paperreviewing': 'paper_reviewing',
    'managepaperreviewing': 'paper_setup',
    'assigncontributions': 'paper_assign',
    'judgelist': 'contributions_to_judge',
    'judgelistreviewer': 'contributions_as_reviewer',
    'judgelisteditor': 'contributions_as_editor',
    'uploadpaper': 'paper_upload',
    'downloadtemplate': 'download_template',
    'abstractsBook': 'abstracts_book',
    'registrationForm': 'registration',
    'registrants': 'registrants',
    'evaluation': 'evaluation',
    'newEvaluation': 'evaluation_form',
    'viewMyEvaluation': 'evaluation_edit',
    'chat-event-page': 'chatrooms',
    'vc-event-page': 'vc-event-page',
}


DEFAULT_MENU_STRUCTURE = [
    ['SystemLink', 'overview', 'overview', True, []],
    ['SystemLink', 'programme', 'scientific programme', True, [
        ['SystemLink', 'manageTrack', 'manage my tracks', True]
    ]],
    ['SystemLink', 'CFA', 'call for abstracts', True, [
        ['SystemLink', 'ViewAbstracts', 'view my abstracts', True],
        ['SystemLink', 'SubmitAbstract', _AltString('submit abstract', 'submit a new abstract'), True]
    ]],
    ['SystemLink', 'timetable', 'timetable', True, []],
    ['SystemLink', 'contributionList', 'contribution list', True, []],
    ['SystemLink', 'authorIndex', _AltString('author list', 'author index'), True, []],
    ['SystemLink', 'speakerIndex', _AltString('speaker list', 'author index'), False, []],
    ['SystemLink', 'mystuff', 'my conference', True, [
        ['SystemLink', 'mytracks', 'my tracks', True],
        ['SystemLink', 'mysessions', 'my sessions', True],
        ['SystemLink', 'mycontribs', 'my contributions', True]
    ]],
    ['SystemLink', 'paperreviewing', 'paper reviewing', True, [
        ['SystemLink', 'managepaperreviewing', 'manage paper reviewing', True],
        ['SystemLink', 'assigncontributions', 'assign papers', True],
        ['SystemLink', 'judgelist', 'referee area', True],
        ['SystemLink', 'judgelistreviewer', 'content reviewer area', True],
        ['SystemLink', 'judgelisteditor', 'layout reviewer area', True],
        ['SystemLink', 'uploadpaper', 'upload paper', True],
        ['SystemLink', 'downloadtemplate', 'download template', True]
    ]],
    ['SystemLink', 'abstractsBook', 'book of abstracts', True, []],
    ['SystemLink', 'registrationForm', 'registration', True, []],
    ['SystemLink', 'registrants', 'participant list', False, []],
    ['SystemLink', 'evaluation', 'evaluation', True, [
        ['SystemLink', 'newEvaluation', 'evaluation form', True],
        ['SystemLink', 'viewMyEvaluation', 'modify my evaluation', True]
    ]]
]

DEFAULT_MENU_STRUCTURE_2 = DEFAULT_MENU_STRUCTURE + [
    ['SystemLink', 'vc-event-page', 'videoconference rooms', True, []],
    ['SystemLink', 'chat-event-page', 'chat rooms', True, []]
]
DEFAULT_MENU_STRUCTURES = [DEFAULT_MENU_STRUCTURE, DEFAULT_MENU_STRUCTURE_2]
REMOVED_MENU_NAMES = {'ViewMyRegistration', 'NewRegistration', 'downloadETicket', 'collaboration', 'instantMessaging'}
NOT_TOP_LEVEL_NAMES = {'program_my_tracks', 'evaluation_form', 'evaluation_edit'}


def _menu_item_data(entry, children=True):
    if entry._name in REMOVED_MENU_NAMES:
        return None
    data = [entry.__class__.__name__, entry._name, getattr(entry, '_caption', '').lower(), entry._active]
    if children:
        data.append(filter(None, (_menu_item_data(child, False) for child in getattr(entry, '_listLink', []))))
    return data


def _get_menu_structure(display_mgr):
    return filter(None, map(_menu_item_data, display_mgr._menu._listLink))


class EventMenuImporter(Importer):
    def has_data(self):
        return MenuEntry.has_rows

    def migrate(self):
        self.migrate_event_menus()

    def migrate_event_menus(self):
        self.print_step('migrating conference menus')
        for event, display_mgr in committing_iterator(self._iter_events()):
            if _get_menu_structure(display_mgr) in DEFAULT_MENU_STRUCTURES:
                continue
            self.print_success('', event_id=event.id)
            db.session.add_all(self._migrate_menu(event, display_mgr._menu))

    def _migrate_menu(self, event, container, parent=None, used=None):
        if used is None:
            used = set()
        for pos, item in enumerate(container._listLink, 1):
            data = {'parent': parent, 'event_id': int(event.id), 'is_enabled': item._active, 'position': pos}
            item_type = item.__class__.__name__
            if item_type == 'SystemLink':
                if item._name in REMOVED_MENU_NAMES:
                    continue
                data['name'] = MENU_ENTRY_NAME_MAP[item._name]
                if not parent and data['name'] in NOT_TOP_LEVEL_NAMES:
                    self.print_warning(cformat('%{yellow}Skipping top-level menu entry {}').format(data['name']),
                                       event_id=event.id)
                    continue
                elif data['name'] in used:
                    self.print_error(cformat('%{red!}duplicate menu entry name {}; skipping').format(data['name']),
                                     event_id=event.id)
                    continue
                used.add(data['name'])
                data['title'] = strip_tags(convert_to_unicode(item._caption)).strip()
                if item._name == 'chatrooms':
                    data['plugin'] = 'chat'
                    data['type'] = MenuEntryType.plugin_link
                else:
                    data['type'] = MenuEntryType.internal_link
            elif item_type == 'Spacer':
                data['type'] = MenuEntryType.separator
            elif item_type == 'ExternLink':
                data['type'] = MenuEntryType.user_link
                data['title'] = strip_tags(convert_to_unicode(item._caption)).strip()
                data['link_url'] = item._URL.strip()
                if not data['link_url']:
                    if getattr(item, '_listLink', None):
                        self.print_warning(cformat('%{yellow!}Link "{}" has no URL but children').format(
                            data['title']), event_id=event.id)
                    else:
                        self.print_warning(cformat('%{yellow}Skipping link "{}" with no URL').format(
                            data['title']), event_id=event.id)
                        continue
            elif item_type == 'PageLink':
                data['type'] = MenuEntryType.page
                data['title'] = strip_tags(convert_to_unicode(item._caption)).strip()
                data['page'] = MenuPage(html=item._page._content)
                # TODO: handle item._page._isHome
            else:
                self.print_error('Unexpected menu item type: {}'.format(item_type), event_id=event.id)
                continue
            entry = MenuEntry(**data)
            yield entry
            if getattr(item, '_listLink', None):
                # child entries
                if not parent:
                    for sub_entry in self._migrate_menu(event, item, entry, used):
                        yield sub_entry
                else:
                    self.print_warning('Skipping children inside nested entry', event_id=event.id)

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))
        wfr = self.zodb_root['webfactoryregistry']
        dmr = self.zodb_root['displayRegistery']
        for event in self.flushing_iterator(it):
            if wfr.get(event.id) is None:  # only conferences
                yield event, dmr[event.id]
