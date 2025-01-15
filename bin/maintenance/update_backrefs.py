# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import sys
from collections import defaultdict
from operator import itemgetter

import click
from sqlalchemy import inspect

from indico.core.db.sqlalchemy.util.models import get_all_models, import_all_models


def _find_backrefs():
    backrefs = defaultdict(list)
    for cls in get_all_models():
        if not hasattr(cls, '__table__'):
            continue
        mapper = inspect(cls)
        for rel in mapper.relationships:
            if rel.backref is None:
                continue
            backref_name = rel.backref if isinstance(rel.backref, str) else rel.backref[0]
            if cls != rel.class_attribute.class_:
                # skip relationships defined on a parent class
                continue
            backrefs[rel.mapper.class_].append((backref_name, cls.__name__, rel.key))
    return backrefs


def _get_source_file(cls):
    return cls.__module__.replace('.', '/') + '.py'


def _write_backrefs(rels, new_source):
    for backref_name, target, target_rel_name in sorted(rels, key=itemgetter(0)):
        new_source.append(f'    # - {backref_name} ({target}.{target_rel_name})')


@click.command()
@click.option('--ci', is_flag=True, help='Indicate that the script is running during CI and should use a non-zero '
                                         'exit code unless all backrefs were already up to date.')
def main(ci):
    import_all_models()
    has_missing = has_updates = False
    for cls, rels in sorted(_find_backrefs().items(), key=lambda x: x[0].__name__):
        path = _get_source_file(cls)
        with open(path) as f:
            source = [line.rstrip('\n') for line in f]
        new_source = []
        in_class = in_backrefs = backrefs_written = False
        for line in source:
            if in_backrefs:
                if not backrefs_written:
                    _write_backrefs(rels, new_source)
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
            elif line.startswith(f'class {cls.__name__}('):
                in_class = True
            new_source.append(line)
        if in_backrefs and not backrefs_written:
            _write_backrefs(rels, new_source)
        if not backrefs_written:
            click.secho(f'Class {cls.__name__} has no comment for backref information', fg='yellow')
            has_missing = True
        if source != new_source:
            click.secho(f'Updating backref info for {cls.__name__} in {path}', fg='green', bold=True)
            has_updates = True
            with open(path, 'w') as f:
                f.writelines(line + '\n' for line in new_source)
    sys.exit(1 if (has_missing or (ci and has_updates)) else 0)


if __name__ == '__main__':
    main()
