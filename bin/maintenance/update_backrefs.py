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

from collections import defaultdict
from operator import itemgetter

from sqlalchemy import inspect

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import import_all_models
from indico.util.console import cformat


def _find_backrefs():
    backrefs = defaultdict(list)
    for cls in db.Model._decl_class_registry.itervalues():
        if not hasattr(cls, '__table__'):
            continue
        mapper = inspect(cls)
        for rel in mapper.relationships:
            if rel.backref is None:
                continue
            backref_name = rel.backref if isinstance(rel.backref, basestring) else rel.backref[0]
            if cls != rel.class_attribute.class_:
                # skip relationships defined on a parent class
                continue
            backrefs[rel.mapper.class_].append((backref_name, cls.__name__, rel.key))
    return backrefs


def _get_source_file(cls):
    return cls.__module__.replace('.', '/') + '.py'


def main():
    import_all_models()
    for cls, rels in sorted(_find_backrefs().iteritems(), key=lambda x: x[0].__name__):
        path = _get_source_file(cls)
        with open(path, 'r') as f:
            source = [line.rstrip('\n') for line in f]
        new_source = []
        in_class = in_backrefs = backrefs_written = False
        for i, line in enumerate(source):
            if in_backrefs:
                if not backrefs_written:
                    for backref_name, target, target_rel_name in sorted(rels, key=itemgetter(0)):
                        new_source.append('    # - {} ({}.{})'.format(backref_name, target, target_rel_name))
                    backrefs_written = True
                if not line.startswith('    # - '):
                    in_backrefs = False
                else:
                    continue
            elif in_class:
                if line == '    # relationship backrefs:':
                    in_backrefs = True
                elif line and not line.startswith(' ' * 4):
                    # end of the indented class block
                    in_class = False
            else:
                if line.startswith('class {}('.format(cls.__name__)):
                    in_class = True
            new_source.append(line)
        if not backrefs_written:
            print cformat('%{yellow}Class {} has no comment for backref information').format(cls.__name__)
        if source != new_source:
            print cformat('%{green!}Updating backref info for {} in {}').format(cls.__name__, path)
            with open(path, 'w') as f:
                f.writelines(line + '\n' for line in new_source)


if __name__ == '__main__':
    main()
