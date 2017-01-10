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

from __future__ import unicode_literals
from operator import attrgetter

from indico.core.db import db
from indico.modules.users import User
from indico.modules.groups.models.groups import LocalGroup
from indico.util.console import cformat
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer, convert_to_unicode


class GroupImporter(Importer):
    def has_data(self):
        return LocalGroup.query.has_rows()

    def migrate(self):
        self.migrate_groups()
        self.fix_sequences('users', {'groups'})

    def migrate_groups(self):
        print cformat('%{white!}migrating groups')

        for old_group in committing_iterator(self.zodb_root['groups'].itervalues()):
            if old_group.__class__.__name__ != 'Group':
                continue
            group = LocalGroup(id=int(old_group.id), name=convert_to_unicode(old_group.name).strip())
            print cformat('%{green}+++%{reset} %{white!}{:6d}%{reset} %{cyan}{}%{reset}').format(group.id, group.name)
            members = set()
            for old_member in old_group.members:
                if old_member.__class__.__name__ != 'Avatar':
                    print cformat('%{yellow!}!!!        Unsupported group member type: {}').format(
                        old_member.__class__.__name__)
                    continue
                user = User.get(int(old_member.id))
                if user is None:
                    print cformat('%{yellow!}!!!        User not found: {}').format(old_member.id)
                    continue
                while user.merged_into_user:
                    user = user.merged_into_user
                if user.is_deleted:
                    print cformat('%{yellow!}!!!        User deleted: {}').format(user.id)
                    continue
                members.add(user)
            for member in sorted(members, key=attrgetter('full_name')):
                print cformat('%{blue!}<->%{reset}        %{white!}{:6d} %{yellow}{} ({})').format(
                    member.id, member.full_name, member.email)
            group.members = members
            db.session.add(group)
