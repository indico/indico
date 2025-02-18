# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import ast
import os
import pickle
import posixpath
import re
import sys
import tarfile
from collections import defaultdict
from datetime import date, datetime
from importlib import import_module
from io import BytesIO
from itertools import batched
from operator import attrgetter, itemgetter
from uuid import uuid4

import click
import dateutil.parser
import yaml
from flask import current_app
from sqlalchemy import inspect
from terminaltables import AsciiTable

import indico
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.util.models import get_all_models
from indico.core.storage.backend import get_storage, get_storage_backends
from indico.modules.auth.models.identities import Identity
from indico.modules.categories import Category, CategoryLogRealm
from indico.modules.events import Event, EventLogRealm
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.logs.models.entries import LogKind
from indico.modules.users import User
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.util import get_user_by_email
from indico.util.console import cformat, verbose_iterator
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.iterables import materialize_iterable
from indico.util.string import strict_str


CURRENT_EXPORT_VERSION = 2  # only bump this for backwards-incompatible changes to the export format itself
_notset = object()
_skip = object()


class _NoAliasesDumper(yaml.Dumper):
    def ignore_aliases(self, *args, **kwargs):
        # Never generate `&id...` refs for duplicte data, it's not a huge
        # space saver, but makes things harder to read.
        return True


class _YamlBackend:
    ext = 'yaml'

    @staticmethod
    def dump(data):
        return yaml.dump(data, indent=2, Dumper=_NoAliasesDumper)

    @staticmethod
    def load(data):
        return yaml.unsafe_load(data)


class _PickleBackend:
    ext = 'pickle'

    @staticmethod
    def dump(data):
        return pickle.dumps(data)

    @staticmethod
    def load(fileobj):
        return pickle.load(fileobj)  # noqa: S301


BACKENDS = {'yaml': _YamlBackend, 'pickle': _PickleBackend}


def export_event(event_or_category, target_file, *, keep_uuids=False, use_pickle=False, dummy_files=False,
                 external_files=False, identities=None):
    """Export the specified event/category with all its data to a file.

    :param event_or_category: the `Event` to export, or a `Category` to export with all
                              its events and subcategories
    :param target_file: a file object to write the data to
    :param keep_uuids: preserve uuids between the exported and imported events
    :param use_pickle: use pickle instead of yaml for serializing
    :param dummy_files: replace actual file content with short dummy content
    :param external_files: keep a reference to the original file storage instead of
                           exporting file content
    """
    backend = 'pickle' if use_pickle else 'yaml'
    exporter = EventExporter(event_or_category, target_file, keep_uuids=keep_uuids, dummy_files=dummy_files,
                             external_files=external_files, backend=backend, identities=identities)
    exporter.serialize()


def import_event(source_file, category_id=0, create_users=None, create_affiliations=None, verbose=False, force=False,
                 skip_external_files=False):
    """Import a previously-exported event/category.

    It is up to the caller of this function to commit the transaction.

    :param source_file: An open file object containing the exported event.
    :param category_id: ID of the category in which to create the event.
    :param create_users: Whether to create missing users or skip them.
                         If set to None, an interactive prompt is shown
                         when such users are encountered.
    :param create_affiliations: Whether to create missing predefined affiliations
                                or keep them as unstructured text. If set to None,
                                an interactive prompt is shown when such
                                affiliations are encountered.
    :param verbose: Whether to enable verbose output.
    :param force: Whether to ignore database version conflicts.
    :param skip_external_files: Whether to skip copying external files, and write
                                them to the file mapping instead.
    :return: The imported event/category, the ID mapping and the file mapping.
    """
    importer = EventImporter(source_file, category_id, create_users, create_affiliations, verbose, force,
                             skip_external_files)
    event_or_category = importer.deserialize()
    return event_or_category, dict(importer.source_id_map), list(importer.files_to_copy)


def import_event_files(handler_import_path, mapping_file):
    """Import files after an event import."""
    try:
        module_path, class_name = handler_import_path.rsplit('.', 1)
    except ValueError:
        print(f"{handler_import_path} doesn't look like a module path")
        return
    module = import_module(module_path)
    try:
        handler_func = getattr(module, class_name)
    except AttributeError:
        print(f'Module "{module_path}" does not define a "{class_name}" attribute')
        return

    mapping = pickle.load(mapping_file)  # noqa: S301
    backend_names = {x[0][0] for x in mapping}
    click.echo(f'Config is needed for external storage backends: {', '.join(sorted(backend_names))}')
    backends = _prompt_storage_backend_config(backend_names)
    handler_func(mapping, backends)


def _prompt_storage_backend_config(backend_names):
    all_backends = get_storage_backends()
    while True:
        click.echo('Paste a Python dict literal with the config of those backends, and confirm with CTRL+D.')
        click.echo("You may be able to take it from the source instance's STORAGE_BACKENDS config setting.")
        mapping = ast.literal_eval(sys.stdin.read())
        if not isinstance(mapping, dict):
            click.echo('Invalid data, not a dict')
            click.echo()
            continue
        elif missing := sorted(backend_names - set(mapping)):
            click.echo(f'Missing keys: {', '.join(missing)}')
            click.echo()
            continue

        backends = {}
        for name in backend_names:
            storage_name, storage_config = mapping[name].split(':', 1)
            if not (backend := all_backends.get(storage_name)):
                click.echo(f'Invalid backend: {storage_name}')
                click.echo()
                backends = None
                break
            backends[name] = backend(storage_config)
        # This is a bit ugly, but we can't `continue` the outer loop above so we use this trick instead...
        if backends is not None:
            return backends


def _model_to_table(name):
    """Resolve a model name to a full table name (unless it's already one)."""
    return getattr(db.m, name).__table__.fullname if name[0].isupper() else name


def _make_globals(**extra):
    """
    Build a globals dict for the exec/eval environment that contains
    all the models and whatever extra data is needed.
    """
    globals_ = {cls.__name__: cls for cls in get_all_models() if hasattr(cls, '__table__')}
    globals_.update(extra)
    return globals_


def _exec_custom(code, **extra):
    """Execute a custom code snippet and return all non-underscored values."""
    globals_ = _make_globals(**extra)
    locals_ = {}
    exec(code, globals_, locals_)  # noqa: S102
    return {str(k): v for k, v in locals_.items() if k[0] != '_'}


def _resolve_col(col):
    """Resolve a string or object to a column.

    :param col: A string containing a Python expression, a model
                attribute or a Column instance.
    """
    attr = eval(col, _make_globals()) if isinstance(col, str) else col  # noqa: S307
    if isinstance(attr, db.Column):
        return attr
    assert len(attr.prop.columns) == 1
    return attr.prop.columns[0]


def _get_single_fk(col):
    """Get the single-column FK constraint of the specified column."""
    # find the column-specific FK, not some compound fk containing this column
    fks = [x for x in col.foreign_keys if len(x.constraint.columns) == 1]
    assert len(fks) == 1
    return fks[0]


def _get_pk(table):
    """Get the single column that is the table's PK."""
    pks = list(inspect(table).primary_key.columns.values())
    assert len(pks) == 1
    return pks[0]


def _has_single_pk(table):
    """Check if the table has a single PK."""
    return len(list(inspect(table).primary_key.columns.values())) == 1


def _get_inserted_pk(result):
    """Get the single PK value inserted by a query."""
    assert len(result.inserted_primary_key) == 1
    return result.inserted_primary_key[0]


def _get_alembic_version() -> list[str]:
    return [rev for rev, in db.session.execute('SELECT version_num FROM alembic_version').fetchall()]


class EventExporter:
    def __init__(self, obj, target_file, *, keep_uuids=False, dummy_files=False, external_files=False, backend='yaml',
                 identities=None):
        self.obj = obj
        self.target_file = target_file
        self.keep_uuids = keep_uuids
        self.dummy_files = dummy_files
        self.external_files = external_files
        self.used_storage_backends = set()
        self.backend = BACKENDS[backend]
        self.identities = frozenset(identities or set())
        self.categories = frozenset(self._fetch_categories())
        # XXX we're not using a context manager here since changing that would probably require
        # some refactoring of how this class is used
        self.archive = tarfile.open(mode='w|', fileobj=self.target_file)  # noqa: SIM115
        self.id_map = defaultdict(dict)
        self.orig_ids = defaultdict(dict)
        self.used_uuids = set()
        self.seen_rows = set()
        self.fk_map = self._get_reverse_fk_map()
        self.spec = self._load_spec()
        self.users = {}
        self.affiliations = {}

    def _fetch_categories(self):
        if not isinstance(self.obj, Category):
            return set()
        return {id_ for id_, in self.obj.deep_children_query.with_entities(Category.id).all()} | {self.obj.id}

    def _add_file(self, name, size, data):
        if isinstance(data, bytes):
            data = BytesIO(data)
        elif isinstance(data, str):
            data = BytesIO(data.encode())
        info = tarfile.TarInfo(name)
        info.size = size
        self.archive.addfile(info, data)

    def serialize(self):
        model = type(self.obj)
        all_objects = list(self._serialize_objects(model.__table__, model.id == self.obj.id, is_root_object=True))
        metadata = {
            'timestamp': now_utc(),
            'export_version': CURRENT_EXPORT_VERSION,
            'indico_version': indico.__version__,
            'db_version': _get_alembic_version(),
            'dummy_files': self.dummy_files,
            'object_files': [],
            'external_storage_backends': sorted(self.used_storage_backends),
            'users': self.users,
            'affiliations': self.affiliations,
        }
        for i, objects in enumerate(batched(all_objects, 5000), 1):
            object_data = self.backend.dump(objects)
            filename = f'objects-{i}.{self.backend.ext}'
            metadata['object_files'].append(filename)
            self._add_file(filename, len(object_data), object_data)
        dumped_metadata = self.backend.dump(metadata)
        self._add_file(f'data.{self.backend.ext}', len(dumped_metadata), dumped_metadata)
        dumped_ids = self.backend.dump(dict(self.orig_ids))
        self._add_file(f'ids.{self.backend.ext}', len(dumped_ids), dumped_ids)
        self.archive.close()

    def _load_spec(self):
        def _process_tablespec(tablename, tablespec):
            tablespec.setdefault('cols', {})
            tablespec.setdefault('fks', {})
            tablespec.setdefault('fks_out', {})
            tablespec.setdefault('skipif', None)
            tablespec.setdefault('order', None)
            tablespec.setdefault('python_order', None)
            tablespec.setdefault('allow_duplicates', False)
            tablespec.setdefault('show_progress', False)
            fks = {}
            for fk_name in tablespec['fks']:
                col = _resolve_col(fk_name)
                fk = _get_single_fk(col)
                fks.setdefault(fk.column.name, []).append(col)
            tablespec['fks'] = fks
            tablespec['fks_out'] = {fk: _get_single_fk(db.metadata.tables[tablename].c[fk]).column
                                    for fk in tablespec['fks_out']}
            return tablespec

        with open(os.path.join(current_app.root_path, 'modules', 'events', 'export.yaml')) as f:
            spec = yaml.safe_load(f)

        return {_model_to_table(k): _process_tablespec(_model_to_table(k), v) for k, v in spec['export'].items()}

    def _get_reverse_fk_map(self):
        """Build a mapping between columns and incoming FKs."""
        legacy_tables = {'events.legacy_contribution_id_map', 'events.legacy_subcontribution_id_map',
                         'attachments.legacy_attachment_id_map', 'event_registration.legacy_registration_map',
                         'events.legacy_session_block_id_map', 'events.legacy_image_id_map',
                         'events.legacy_session_id_map', 'events.legacy_page_id_map', 'categories.legacy_id_map',
                         'events.legacy_id_map', 'attachments.legacy_folder_id_map'}
        fk_targets = defaultdict(set)
        for name, table in db.metadata.tables.items():
            if name in legacy_tables:
                continue
            for column in table.columns:
                for fk in column.foreign_keys:
                    fk_targets[fk.target_fullname].add(fk.parent)
        return dict(fk_targets)

    def _get_uuid(self):
        uuid = str(uuid4())
        if uuid in self.used_uuids:
            # VERY unlikely but just in case...
            return self._get_uuid()
        self.used_uuids.add(uuid)
        return uuid

    def _make_idref(self, column, value, incoming=False, target_column=None):
        """Generate a ID reference.

        When generating an incoming ID reference, `column` must be a PK
        and point to the column that is referenced by FKs.  In this case
        the `value` is ignored since it will be auto-generated by the db
        when the new row is inserted.

        Otherwise, exactly one of `column` or `target_column` must be set.
        `column` is the column in the current table that has a FK referencing
        some other column.
        `target_column` is already the column that is referenced by a FK
        in the current table.
        """
        assert (column is None) != (target_column is None)

        if value is None:
            return None

        if incoming:
            assert column.primary_key
            assert target_column is None
            fullname = f'{column.table.fullname}.{column.name}'
            type_ = 'idref_set'
        else:
            if target_column is not None:
                fullname = f'{target_column.table.fullname}.{target_column.name}'
            else:
                fk = _get_single_fk(column)
                fullname = fk.target_fullname
                target_column = fk.column
            if target_column is User.__table__.c.id and value is not None:
                type_ = 'userref'
            elif target_column is Affiliation.__table__.c.id and value is not None:
                type_ = 'affilref'
            else:
                type_ = 'idref'
        uuid = self.id_map[fullname].setdefault(value, self._get_uuid())
        if incoming:
            assert uuid not in self.orig_ids[fullname]
            self.orig_ids[fullname][uuid] = value
        if type_ == 'userref' and uuid not in self.users:
            user = User.get(value)
            if user.is_deleted:
                click.secho(f'! Found reference to deleted user in {column}: {user}', fg='yellow')
            self.users[uuid] = None if user.is_system else {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'title': user._title,
                'affiliation': user.affiliation,
                'affiliation_id': self._make_idref(None, user.affiliation_id,
                                                   target_column=_resolve_col('Affiliation.id')),
                'phone': user.phone,
                'address': user.address,
                'email': user.email,
                'all_emails': list(user.all_emails),
                'is_deleted': user.is_deleted,
                'merged_into_id': self._make_idref(None, user.merged_into_id, target_column=_resolve_col('User.id')),
                'identities': [
                    {
                        'provider': identity.provider,
                        'identifier': identity.identifier,
                        'multipass_data': identity.multipass_data,
                        '_data': identity._data,
                        'password_hash': identity.password_hash,
                    }
                    for identity in user.identities
                    if identity.provider in self.identities
                ],
            }
        elif type_ == 'affilref' and uuid not in self.affiliations:
            affiliation = Affiliation.get(value)
            self.affiliations[uuid] = {
                'name': affiliation.name,
                'alt_names': affiliation.alt_names,
                'street': affiliation.street,
                'postcode': affiliation.postcode,
                'city': affiliation.city,
                'country_code': affiliation.country_code,
                'meta': affiliation.meta,
            }
        return type_, uuid

    def _make_value(self, value):
        """Convert values that need extra handling."""
        if isinstance(value, (date, datetime)):
            # YAML loses timezone information for datatime objects so
            # we serialize/deserialize it manually
            return type(value).__name__, value.isoformat()
        elif isinstance(value, bytes) and len(value) > 1000:
            # bytestrings (usually binary data, e.g. an event logo) go into
            # separate files - YAML handles them well (base64) but it just
            # makes the YAML file larger, which is kind of ugly
            uuid = self._get_uuid()
            self._add_file(uuid, len(value), value)
            return 'binary', uuid
        elif isinstance(value, tuple):
            # XXX: We don't expect any columns to have tuple data, but
            # if we do we need to convert them to `('tuple', value)`
            # since we expect any tuple to indicate `(type, value)`
            # instead of a plain value that can be used directly
            raise ValueError('tuples not handled')
        else:
            return value

    def _process_file(self, data):
        """Copy a file from storage into the export archive."""
        if data.get('storage_file_id') is None:
            return
        assert '__file__' not in data  # only one file per row allowed
        storage_backend = data.pop('storage_backend')
        storage_file_id = data.pop('storage_file_id')
        filename = data.pop('filename')
        content_type = data.pop('content_type')
        size = data.pop('size')
        md5 = data.pop('md5')
        uuid = self._get_uuid()
        storage_data = {}
        if self.dummy_files:
            size = 1
            md5 = '9dd4e461268c8034f5c8564e155c67a6'  # md5('x')
            self._add_file(uuid, size, 'x')
        elif self.external_files:
            storage_data = {'storage': {'backend': storage_backend, 'file_id': storage_file_id}}
            self.used_storage_backends.add(storage_backend)
        else:
            with get_storage(storage_backend).open(storage_file_id) as f:
                self._add_file(uuid, size, f)
        data['__file__'] = ('file', {'uuid': uuid, 'filename': filename, 'content_type': content_type, 'size': size,
                                     'md5': md5, **storage_data})

    def _serialize_objects(self, table, filter_, *, is_root_object=False, parent_scope=None):
        spec = self.spec[table.fullname]
        query = db.session.query(table).filter(filter_)
        if spec['order']:
            # Use a custom order instead of whatever the DB uses by default.
            # This is mainly needed for self-referential FKs and CHECK
            # constraints that require certain objects to be exported before
            # the ones referencing them
            order = eval(spec['order'], _make_globals())  # noqa: S307
            if not isinstance(order, tuple):
                order = (order,)
            query = query.order_by(*order)
        query = query.order_by(*table.primary_key.columns)
        rows = query.all()
        if spec['python_order']:
            rows = _exec_custom(spec['python_order'], ROWS=rows)['rows']
        cascaded = []
        cat_role = ('category_role',) if self.categories else ()
        if spec['show_progress'] and len(rows) > 1:
            rows_iter = verbose_iterator(rows, len(rows), get_id=attrgetter('id'), get_title=attrgetter('title'),
                                         print_every=1, print_total_time=True)
        else:
            rows_iter = iter(rows)
        for row in rows_iter:
            if spec['skipif'] and eval(spec['skipif'], _make_globals(ROW=row, CAT_ROLE=cat_role)):  # noqa: S307
                continue
            rowdict = row._asdict()
            pk = tuple(v for k, v in rowdict.items() if table.c[k].primary_key)
            if (table.fullname, pk) in self.seen_rows:
                if spec['allow_duplicates']:
                    continue
                else:
                    raise Exception('Trying to serialize already-serialized row')
            self.seen_rows.add((table.fullname, pk))
            data = {}
            scope = None
            for col, value in rowdict.items():
                col = str(col)  # col names are `quoted_name` objects
                col_fullname = f'{table.fullname}.{col}'
                col_custom = spec['cols'].get(col, _notset)
                colspec = table.c[col]
                if col_custom is None:
                    # column is explicitly excluded
                    continue
                elif col_custom is not _notset:
                    # column has custom code to process its value (and possibly name)
                    if value is not None:
                        def _get_root_idref():
                            key = f'{type(self.obj).__table__.fullname}.{type(self.obj).id.name}'
                            assert key in self.id_map
                            return 'idref', self.id_map[key][self.obj.id]

                        def _make_id_ref(target, id_):
                            return self._make_idref(None, id_, target_column=_resolve_col(target))

                        res = _exec_custom(col_custom, VALUE=value, SKIP=_skip, KEEP_UUIDS=self.keep_uuids,
                                           MAKE_ROOT_REF=_get_root_idref, MAKE_ID_REF=_make_id_ref,
                                           IS_ROOT_OBJECT=is_root_object, CATEGORIES=self.categories)
                        if res.get(col) is _skip:
                            continue
                        data.update(res)
                elif col_fullname in self.fk_map:
                    # an FK references this column -> generate a uuid
                    data[col] = self._make_idref(colspec, value, incoming=colspec.primary_key)
                    if colspec.primary_key:
                        assert scope is None
                        scope = data[col][1]
                elif colspec.foreign_keys:
                    # column is an FK
                    data[col] = self._make_idref(colspec, value)
                elif colspec.primary_key:
                    # column is a PK with no incoming FKs -> no need to track the ID
                    pass
                else:
                    # not an fk
                    data.setdefault(col, self._make_value(value))
            self._process_file(data)
            # generate new scope if needed or keep parent scope
            if table in {Event.__table__, Category.__table__}:
                new_scope = True
            else:
                new_scope = False
                scope = parent_scope
            assert scope is not None
            # export objects referenced in outgoing FKs before the row
            # itself as the FK column might not be nullable
            for col, fk in spec['fks_out'].items():
                value = rowdict[col]
                yield from self._serialize_objects(fk.table, value == fk, parent_scope=scope)
            yield table.fullname, (new_scope, scope), data
            # serialize objects referencing the current row, but don't export them yet
            for col, fks in spec['fks'].items():
                value = rowdict[col]
                cascaded += [
                    x
                    for fk in fks
                    for x in self._serialize_objects(fk.table, value == fk, parent_scope=scope)
                ]
        # we only add incoming fks after being done with all objects in case one
        # of the referenced objects references another object from the current table
        # that has not been serialized yet (e.g. abstract reviews proposing as duplicate)
        yield from cascaded


class EventImporter:
    def __init__(self, source_file, category_id=0, create_users=None, create_affiliations=None, verbose=False,
                 force=False, skip_external_files=False):
        self.source_file = source_file
        self.category_id = category_id
        self.create_users = create_users
        self.create_affiliations = create_affiliations
        self.source_backends = {}
        self.verbose = verbose
        self.force = force
        self.skip_external_files = skip_external_files
        self.archive = tarfile.open(fileobj=source_file)  # noqa: SIM115
        archive_files = set(self.archive.getnames())
        self.backend = BACKENDS['yaml' if 'data.yaml' in archive_files else 'pickle']
        self.data = self.backend.load(self.archive.extractfile(f'data.{self.backend.ext}'))
        try:
            self.source_ids = self.backend.load(self.archive.extractfile(f'ids.{self.backend.ext}'))
        except KeyError:
            self.source_ids = None
        self.source_id_map = defaultdict(dict)
        self.id_map = {}
        self.scope_id_map = {}
        self.user_map = {}
        self.affiliation_map = {}
        self.top_level = None
        self.system_user_id = User.get_system_user().id
        self.spec = self._load_spec()
        self.deferred_idrefs = defaultdict(set)
        self.files_to_copy = set()

    def _load_spec(self):
        def _resolve_col_name(col):
            colspec = _resolve_col(col)
            return f'{colspec.table.fullname}.{colspec.name}'

        def _process_format(fmt, _re=re.compile(r'<([^>]+)>')):
            fmt = _re.sub(r'%{reset}%{cyan}\1%{reset}%{blue!}', fmt)
            return cformat('- %{blue!}' + fmt)

        with open(os.path.join(current_app.root_path, 'modules', 'events', 'export.yaml')) as f:
            spec = yaml.safe_load(f)

        spec = spec['import']
        spec['defaults'] = {_model_to_table(k): v for k, v in spec.get('defaults', {}).items()}
        spec['custom'] = {_model_to_table(k): v for k, v in spec.get('custom', {}).items()}
        spec['missing_users'] = {_resolve_col_name(k): v for k, v in spec.get('missing_users', {}).items()}
        spec['verbose'] = {_model_to_table(k): _process_format(v) for k, v in spec.get('verbose', {}).items()}
        return spec

    def _setup_external_storage(self, data):
        if self.skip_external_files:
            return
        if not (backend_names := set(data['external_storage_backends'])):
            return
        click.echo(f'Some files reference external storage backends: {', '.join(sorted(backend_names))}')
        self.source_backends = _prompt_storage_backend_config(backend_names)
        click.echo('Storage backends configured')

    def _load_users(self, data):
        if not data['users']:
            return
        missing = {}
        for uuid, userdata in data['users'].items():
            if userdata is None:
                self.user_map[uuid] = self.system_user_id
                continue
            user = (User.query
                    .filter(User.all_emails.in_(userdata['all_emails']),
                            ~User.is_deleted)
                    .first())
            if user is None:
                missing[uuid] = userdata
            else:
                self.user_map[uuid] = user.id
        if missing:
            click.secho('The following users from the import data could not be mapped to existing users:', fg='yellow')
            if len(missing) > 1000:
                click.echo(f'({len(missing)} users are a lot; not displaying table)')
            else:
                table_data = [['First Name', 'Last Name', 'Email', 'Affiliation']]
                table_data.extend(
                    [userdata['first_name'], userdata['last_name'], userdata['email'], userdata['affiliation']]
                    for userdata in sorted(missing.values(), key=itemgetter('first_name', 'last_name', 'email'))
                )
                table = AsciiTable(table_data)
                click.echo(table.table)
            if self.create_users is None:
                click.echo('Do you want to create these users now?')
                click.echo('If you choose to not create them, the behavior depends on where the user would be used:')
                click.echo('- If the user is not required, it will be omitted.')
                click.echo('- If a user is required but using the system user will not cause any problems or look '
                           'weird, the system user will be used.')
                click.echo('- In case neither is possible, e.g. in abstract reviews or ACLs, these objects will '
                           'be skipped altogether!')
                create_users = click.confirm('Create the missing users?', default=True)
            else:
                create_users = self.create_users
            if create_users:
                click.secho('Creating missing users', fg='magenta')
                for uuid, userdata in verbose_iterator(missing.items(), len(missing)):
                    user = User(first_name=userdata['first_name'],
                                last_name=userdata['last_name'],
                                email=userdata['email'],
                                secondary_emails=set(userdata['all_emails']) - {userdata['email']},
                                address=userdata['address'],
                                phone=userdata['phone'],
                                affiliation=userdata['affiliation'],
                                affiliation_id=self._convert_value(None, userdata['affiliation_id']),
                                title=userdata['title'],
                                is_deleted=userdata['is_deleted'],
                                is_pending=True)
                    if identities := userdata['identities']:
                        user.is_pending = False
                        user.identities = {Identity(**identitydata) for identitydata in identities}
                    db.session.add(user)
                    db.session.flush()
                    self.user_map[uuid] = user.id
                    if self.verbose:
                        click.echo(cformat("- %{cyan}User%{blue!} '{}' ({})").format(user.full_name, user.email))
                if (merged_users := {k: v for k, v in missing.items() if v['merged_into_id'] is not None}):
                    # Usually there shouldn't be any, but in case we end up having exported a deleted user,
                    # we want to keep the link between the two
                    click.secho('Linking merged users', fg='magenta')
                    for uuid, userdata in verbose_iterator(merged_users.items(), len(merged_users)):
                        source_user = User.get(self.user_map[uuid])
                        target_user = User.get(self.user_map[userdata['merged_into_id'][1]])
                        source_user.merged_into_user = target_user
                    db.session.flush()
            else:
                click.secho('Skipping missing users', fg='magenta')

    def _load_affiliations(self, data):
        if not data['affiliations']:
            return
        missing = {}
        for uuid, affildata in data['affiliations'].items():
            affiliation = (Affiliation.query
                           .filter_by(name=affildata['name'], city=affildata['city'],
                                      country_code=affildata['country_code'], is_deleted=False)
                           .first())
            if affiliation is None:
                missing[uuid] = affildata
            else:
                self.affiliation_map[uuid] = affiliation.id
        if missing:
            click.secho('The following affiliations from the import data could not be mapped to existing ones:',
                        fg='yellow')
            table_data = [['Name', 'City', 'Country']]
            table_data.extend(
                [affildata['name'], affildata['city'], affildata['country_code']]
                for affildata in sorted(missing.values(), key=itemgetter('name', 'city', 'country_code'))
            )
            table = AsciiTable(table_data)
            click.echo(table.table)
            if self.create_affiliations is None:
                click.echo('Do you want to create these affiliations now?')
                click.echo('If you choose to not create them, users/persons will simply lack the extra affiliation '
                           'metadata.')
                create_affiliations = click.confirm('Create the missing affiliations?', default=True)
            else:
                create_affiliations = self.create_affiliations
            if create_affiliations:
                click.secho('Creating missing affiliations', fg='magenta')
                for uuid, affildata in missing.items():
                    affiliation = Affiliation(**affildata)
                    db.session.add(affiliation)
                    db.session.flush()
                    self.affiliation_map[uuid] = affiliation.id
                    if self.verbose:
                        click.echo(cformat("- %{cyan}Affiliation%{blue!} '{}' ({})").format(affiliation.name,
                                                                                            affiliation.country_code))
            else:
                click.secho('Skipping missing affiliations', fg='magenta')

    @materialize_iterable()
    def _load_objects(self, data):
        filenames = data['object_files']
        click.echo('Loading data files')
        it = verbose_iterator(filenames, len(filenames), get_title=lambda x: x, print_every=1, print_total_time=True)
        for filename in it:
            yield from self.backend.load(self.archive.extractfile(filename))

    def deserialize(self) -> Event | Category | None:
        export_version = self.data.get('export_version', 1)
        if export_version != CURRENT_EXPORT_VERSION:
            click.secho(f'Unsupported data format: Expected version {CURRENT_EXPORT_VERSION}, but import archive is '
                        f'version {export_version}', fg='red')
            return None
        if self.data['indico_version'] != indico.__version__:
            click.secho('Indico version mismatch: importing event exported with {} to version {}'
                        .format(self.data['indico_version'], indico.__version__), fg='yellow')
        alembic_version = _get_alembic_version()
        if not self.force and self.data['db_version'] != alembic_version:
            click.secho('Database schema version mismatch: exported on {}, current schema is {}'
                        .format(','.join(self.data['db_version']), ','.join(alembic_version)), fg='red')
            return None
        if self.data['dummy_files']:
            click.secho('Archive has been exported using dummy file content', fg='yellow', bold=True)
            if not config.DEBUG and not self.force:
                click.secho('This instance is not running in debug mode, use --force if you really want to import '
                            'an archive with dummy file content', fg='yellow')
                return None
        self._setup_external_storage(self.data)
        self._load_affiliations(self.data)
        self._load_users(self.data)
        objects = self._load_objects(self.data)
        objects = sorted(objects, key=lambda x: (
            # Import objects that define a new scope first, since their IDs may be needed to generate
            # storage file IDs
            not x[1][0],
            # Import log entries last, since they may reference ids from other objects but will never
            # be referenced themselves. And by putting them last we avoid having deferred idrefs
            x[0] in ('categories.logs', 'events.logs')
        ))
        click.echo('Importing data')
        objects_iter = verbose_iterator(objects, len(objects), print_total_time=True)
        for i, (tablename, (new_scope, scope), tabledata) in enumerate(objects_iter):
            self._deserialize_object(db.metadata.tables[tablename], tabledata, scope, new_scope, is_top_level=(i == 0))
        if self.deferred_idrefs:
            # Any reference to an ID that was exported need to be replaced
            # with an actual ID at some point - either immediately (if the
            # referenced row was already imported) or later (usually in case
            # of circular dependencies where one of the IDs is not available
            # when the row is inserted).
            click.secho('BUG: Not all deferred idrefs have been consumed', fg='red')
            for uuid, values in self.deferred_idrefs.items():
                click.secho(f'{uuid}:', fg='yellow', bold=True)
                for table, col, pk_value in values:
                    click.secho(f'  - {table.fullname}.{col} ({pk_value})', fg='yellow')
            raise Exception('Not all deferred idrefs have been consumed')
        obj = self.top_level[0].get(self.top_level[1])
        click.echo('Associating users by email')
        match obj:
            case Event() as event:
                event.log(EventLogRealm.event, LogKind.other, 'Event', 'Event imported from another Indico instance')
                self._associate_users_by_email(event)
            case Category() as cat:
                cat.log(CategoryLogRealm.category, LogKind.other, 'Category',
                        'Category imported from another Indico instance')
                events = Event.query.filter(Event.category_chain_overlaps([cat.id])).all()
                for event in verbose_iterator(events, len(events), attrgetter('id'), attrgetter('title'),
                                              print_total_time=True):
                    event.log(EventLogRealm.event, LogKind.other, 'Event',
                              'Event imported from another Indico instance')
                    self._associate_users_by_email(event)
        db.session.flush()
        return obj

    def _associate_users_by_email(self, event):
        # link objects to users by email where possible
        # event principals
        emails = [p.email for p in EventPrincipal.query.with_parent(event).filter_by(type=PrincipalType.email)]
        for user in User.query.filter(~User.is_deleted, User.all_emails.in_(emails)):
            EventPrincipal.replace_email_with_user(user, 'event')

        # session principals
        query = (SessionPrincipal.query
                 .filter(SessionPrincipal.session.has(Session.event == event),
                         SessionPrincipal.type == PrincipalType.email))
        emails = [p.email for p in query]
        for user in User.query.filter(~User.is_deleted, User.all_emails.in_(emails)):
            SessionPrincipal.replace_email_with_user(user, 'session')

        # contribution principals
        query = (ContributionPrincipal.query
                 .filter(ContributionPrincipal.contribution.has(Contribution.event == event),
                         ContributionPrincipal.type == PrincipalType.email))
        emails = [p.email for p in query]
        for user in User.query.filter(~User.is_deleted, User.all_emails.in_(emails)):
            ContributionPrincipal.replace_email_with_user(user, 'contribution')

        # event persons
        query = EventPerson.query.with_parent(event).filter(EventPerson.user_id.isnot(None))
        eventperson_users_seen = {person.user for person in query}
        query = EventPerson.query.with_parent(event).filter(EventPerson.user_id.is_(None),
                                                            EventPerson.email != '')  # noqa: PLC1901
        for person in query:
            if not (user := get_user_by_email(person.email)):
                continue
            if user in eventperson_users_seen:
                click.secho(f'! Cannot link additional EventPerson to same user ({user})', fg='yellow')
                continue
            person.user = user
            eventperson_users_seen.add(user)

        # registrations
        regform_users_seen = defaultdict(set)
        for registration in Registration.query.with_parent(event).filter(Registration.user_id.isnot(None)):
            regform_users_seen[registration.registration_form].add(registration.user)
        query = (Registration.query
                 .with_parent(event)
                 .filter(Registration.user_id.is_(None))
                 .order_by(Registration.is_deleted))
        for registration in query:
            if not (user := get_user_by_email(registration.email)):
                continue
            if user in regform_users_seen[registration.registration_form]:
                click.secho(f'! Cannot link additional registration to same user ({user})', fg='yellow')
                continue
            registration.user = user
            regform_users_seen[registration.registration_form].add(user)

    def _convert_value(self, colspec, value):
        if not isinstance(value, tuple):
            return value
        type_, value = value
        if type_ == 'datetime':
            return dateutil.parser.parse(value)
        elif type_ == 'date':
            return dateutil.parser.parse(value).date()
        elif type_ == 'binary':
            return self.archive.extractfile(value).read()
        elif type_ == 'idref':
            try:
                rv = self.id_map[value]
            except KeyError:
                raise IdRefDeferred(value)
            if rv is None:
                raise MissingUserCascaded
            return rv
        elif type_ == 'userref':
            try:
                return self.user_map[value]
            except KeyError:
                mode = self.spec['missing_users'][f'{colspec.table.fullname}.{colspec.name}']
                if mode == 'system':
                    return self.system_user_id
                elif mode == 'none':
                    return None
                elif mode == 'skip':
                    raise MissingUser(self.data['users'][value], skip=True)
                else:
                    raise MissingUser(self.data['users'][value], run=mode)
        elif type_ == 'affilref':
            return self.affiliation_map.get(value)
        else:
            raise ValueError('unknown type: ' + type_)

    def _get_file_storage_path(self, id_, filename, scope, tablename):
        # we use a generic path to store all imported files since we
        # are on the table level here and thus cannot use relationships
        # and the orignal models' logic to construct paths
        scope_type, scope_id = self.scope_id_map[scope]
        path_segments = [scope_type, strict_str(scope_id), 'imported', tablename]
        filename = secure_filename(filename, 'file')
        return posixpath.join(*path_segments, f'{id_}-{filename}')

    def _process_file(self, id_, data, scope, tablename):
        storage_backend = config.ATTACHMENT_STORAGE
        storage = get_storage(storage_backend)
        if source_storage_data := data.get('storage'):
            if self.skip_external_files:
                extracted = None
            else:
                source_storage = self.source_backends[source_storage_data['backend']]
                with source_storage.open(source_storage_data['file_id']) as f:
                    extracted = f.read()
        else:
            extracted = self.archive.extractfile(data['uuid'])
        path = self._get_file_storage_path(id_, data['filename'], scope, tablename)
        if extracted is not None:
            storage_file_id, md5 = storage.save(path, data['content_type'], data['filename'], extracted)
            assert data['size'] == storage.getsize(storage_file_id)
            if data['md5']:
                assert data['md5'] == md5
        else:
            md5 = data['md5']
            storage_file_id = storage.save(path, data['content_type'], data['filename'], b'', dry_run=True)[0]
            self.files_to_copy.add(((source_storage_data['backend'], source_storage_data['file_id']),
                                    (storage_backend, storage_file_id)))
        return {
            'storage_backend': storage_backend,
            'storage_file_id': storage_file_id,
            'content_type': data['content_type'],
            'filename': data['filename'],
            'size': data['size'],
            'md5': md5,
        }

    def _deserialize_object(self, table, data, scope, new_scope, *, is_top_level=False):
        import_defaults = self.spec['defaults'].get(table.fullname, {})
        import_custom = self.spec['custom'].get(table.fullname, {})
        set_idref = None
        set_idref_fullname = None
        file_data = None
        insert_values = dict(import_defaults)
        deferred_idrefs = {}
        missing_user_skip = False
        missing_user_exec = set()
        top_level_model = None
        if is_top_level:
            # the exported data may contain only one event
            assert self.top_level is None
            match table:
                case Event.__table__:
                    insert_values['category_id'] = self.category_id
                    top_level_model = Event
                case Category.__table__:
                    insert_values['parent_id'] = self.category_id
                    top_level_model = Category
                case _:
                    raise Exception('Toplevel object is not event/category')
        for col, value in data.items():
            if isinstance(value, tuple):
                if value[0] == 'idref_set':
                    assert set_idref is None
                    set_idref = value[1]
                    set_idref_fullname = f'{table.fullname}.{col}'
                    continue
                elif value[0] == 'file':
                    # import files later in case we end up skipping the column due to a missing user
                    assert file_data is None
                    file_data = value[1]
                    continue
            colspec = table.c[col]
            if col in import_custom:
                # custom python code to process the imported value
                def _resolve_id_ref(value, deferred_fallback=_notset):
                    try:
                        return self._convert_value(colspec, value)  # noqa: B023
                    except IdRefDeferred:
                        if deferred_fallback is _notset:
                            raise
                        return deferred_fallback
                rv = _exec_custom(import_custom[col], VALUE=value, RESOLVE_ID_REF=_resolve_id_ref)
                assert list(rv.keys()) == [col]
                insert_values[col] = rv[col]
                continue
            try:
                insert_values[col] = self._convert_value(colspec, value)
            except IdRefDeferred as exc:
                deferred_idrefs[col] = exc.uuid
            except MissingUser as exc:
                if exc.skip:
                    click.secho(f'! Skipping row in {table.fullname} due to missing user ({exc.username})',
                                fg='yellow')
                    missing_user_skip = True
                else:
                    missing_user_exec.add(exc.run)
            except MissingUserCascaded:
                click.secho(f'! Skipping row in {table.fullname} as parent row was skipped due to a missing user',
                            fg='yellow')
                missing_user_skip = True
        if missing_user_skip:
            # skipped row due to a missing user? mark it as skipped so
            # anything referencing it will also be skipped
            if set_idref is not None:
                self.id_map[set_idref] = None
            return
        elif missing_user_exec:
            # run custom code to deal with missing users
            for code in missing_user_exec:
                insert_values.update(_exec_custom(code))
        if file_data is not None:
            if _has_single_pk(table):
                # restore a file from the import archive and save it in storage
                pk_name = _get_pk(table).name
                assert pk_name not in insert_values
                # get an ID early since we use it in the filename
                stmt = db.func.nextval(db.func.pg_get_serial_sequence(table.fullname, pk_name))
                insert_values[pk_name] = pk_value = db.session.query(stmt).scalar()
                insert_values.update(self._process_file(pk_value, file_data, scope, table.fullname))
            else:
                insert_values.update(self._process_file(str(uuid4()), file_data, scope, table.fullname))
        if self.verbose and table.fullname in self.spec['verbose']:
            fmt = self.spec['verbose'][table.fullname]
            click.echo(fmt.format(**insert_values))
        res = db.session.execute(table.insert(), insert_values)
        if set_idref is not None:
            # if a column was marked as having incoming FKs, store
            # the ID so the reference can be resolved to the ID
            self._set_idref(set_idref, _get_inserted_pk(res), set_idref_fullname)
        if is_top_level:
            self.top_level = (top_level_model, _get_inserted_pk(res))
        if new_scope:
            assert scope not in self.scope_id_map
            scope_type = {Event.__table__: 'event', Category.__table__: 'category'}[table]
            self.scope_id_map[scope] = (scope_type, _get_inserted_pk(res))
        for col, uuid in deferred_idrefs.items():
            # store all the data needed to resolve a deferred ID reference
            # later once the ID is available
            self.deferred_idrefs[uuid].add((table, col, _get_inserted_pk(res)))

    def _set_idref(self, uuid, id_, fullname):
        if self.source_ids is not None:
            self.source_id_map[fullname][self.source_ids[fullname][uuid]] = id_
        self.id_map[uuid] = id_
        # update all the previously-deferred ID references
        for table, col, pk_value in self.deferred_idrefs.pop(uuid, ()):
            pk = _get_pk(table)
            db.session.execute(table.update().where(pk == pk_value).values({col: id_}))


class IdRefDeferred(Exception):
    def __init__(self, uuid):
        self.uuid = uuid


class MissingUser(Exception):
    def __init__(self, userdata, skip=False, run=None):
        self.skip = skip
        self.run = run
        assert self.skip != bool(self.run)
        self.userdata = userdata

    @property
    def username(self):
        return '{} {} <{}>'.format(self.userdata['first_name'], self.userdata['last_name'], self.userdata['email'])


class MissingUserCascaded(Exception):
    pass
