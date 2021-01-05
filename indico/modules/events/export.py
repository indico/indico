# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os
import posixpath
import re
import tarfile
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from io import BytesIO
from operator import itemgetter
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
from indico.core.storage.backend import get_storage
from indico.modules.events import Event, EventLogKind, EventLogRealm
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.users import User
from indico.modules.users.util import get_user_by_email
from indico.util.console import cformat
from indico.util.date_time import now_utc
from indico.util.string import strict_unicode


_notset = object()


def export_event(event, target_file):
    """Export the specified event with all its data to a file.

    :param event: the `Event` to export
    :param target_file: a file object to write the data to
    """
    exporter = EventExporter(event, target_file)
    exporter.serialize()


def import_event(source_file, category_id=0, create_users=None, verbose=False, force=False):
    """Import a previously-exported event.

    It is up to the caller of this function to commit the transaction.

    :param source_file: An open file object containing the exported event.
    :param category_id: ID of the category in which to create the event.
    :param create_users: Whether to create missing users or skip them.
                         If set to None, an interactive prompt is shown
                         when such users are encountered.
    :param verbose: Whether to enable verbose output.
    :param force: Whether to ignore version conflicts.
    :return: The imported event.
    """
    importer = EventImporter(source_file, category_id, create_users, verbose, force)
    return importer.deserialize()


def _model_to_table(name):
    """Resolve a model name to a full table name (unless it's already one)."""
    return getattr(db.m, name).__table__.fullname if name[0].isupper() else name


def _make_globals(**extra):
    """
    Build a globals dict for the exec/eval environment that contains
    all the models and whatever extra data is needed.
    """
    globals_ = {name: cls for name, cls in db.Model._decl_class_registry.iteritems()
                if hasattr(cls, '__table__')}
    globals_.update(extra)
    return globals_


def _exec_custom(code, **extra):
    """Execute a custom code snippet and return all non-underscored values."""
    globals_ = _make_globals(**extra)
    locals_ = {}
    exec code in globals_, locals_
    return {unicode(k): v for k, v in locals_.iteritems() if k[0] != '_'}


def _resolve_col(col):
    """Resolve a string or object to a column.

    :param col: A string containing a Python expression, a model
                attribute or a Column instance.
    """
    attr = eval(col, _make_globals()) if isinstance(col, basestring) else col
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
    pks = inspect(table).primary_key.columns.values()
    assert len(pks) == 1
    return pks[0]


def _has_single_pk(table):
    """Check if the table has a single PK."""
    return len(inspect(table).primary_key.columns.values()) == 1


def _get_inserted_pk(result):
    """Get the single PK value inserted by a query."""
    assert len(result.inserted_primary_key) == 1
    return result.inserted_primary_key[0]


class EventExporter(object):
    def __init__(self, event, target_file):
        self.event = event
        self.target_file = target_file
        self.archive = tarfile.open(mode='w|', fileobj=self.target_file)
        self.id_map = defaultdict(dict)
        self.used_uuids = set()
        self.seen_rows = set()
        self.fk_map = self._get_reverse_fk_map()
        self.spec = self._load_spec()
        self.users = {}

    def _add_file(self, name, size, data):
        if isinstance(data, basestring):
            data = BytesIO(data)
        info = tarfile.TarInfo(name)
        info.size = size
        self.archive.addfile(info, data)

    def serialize(self):
        metadata = {
            'timestamp': now_utc(),
            'indico_version': indico.__version__,
            'objects': list(self._serialize_objects(Event.__table__, Event.id == self.event.id)),
            'users': self.users
        }
        yaml_data = yaml.dump(metadata, indent=2)
        self._add_file('data.yaml', len(yaml_data), yaml_data)

    def _load_spec(self):
        def _process_tablespec(tablename, tablespec):
            tablespec.setdefault('cols', {})
            tablespec.setdefault('fks', {})
            tablespec.setdefault('fks_out', {})
            tablespec.setdefault('skipif', None)
            tablespec.setdefault('order', None)
            tablespec.setdefault('allow_duplicates', False)
            fks = OrderedDict()
            for fk_name in tablespec['fks']:
                col = _resolve_col(fk_name)
                fk = _get_single_fk(col)
                fks.setdefault(fk.column.name, []).append(col)
            tablespec['fks'] = fks
            tablespec['fks_out'] = OrderedDict((fk, _get_single_fk(db.metadata.tables[tablename].c[fk]).column)
                                               for fk in tablespec['fks_out'])
            return tablespec

        with open(os.path.join(current_app.root_path, 'modules', 'events', 'export.yaml')) as f:
            spec = yaml.safe_load(f)

        return {_model_to_table(k): _process_tablespec(_model_to_table(k), v) for k, v in spec['export'].iteritems()}

    def _get_reverse_fk_map(self):
        """Build a mapping between columns and incoming FKs."""
        legacy_tables = {'events.legacy_contribution_id_map', 'events.legacy_subcontribution_id_map',
                         'attachments.legacy_attachment_id_map', 'event_registration.legacy_registration_map',
                         'events.legacy_session_block_id_map', 'events.legacy_image_id_map',
                         'events.legacy_session_id_map', 'events.legacy_page_id_map', 'categories.legacy_id_map',
                         'events.legacy_id_map', 'attachments.legacy_folder_id_map'}
        fk_targets = defaultdict(set)
        for name, table in db.metadata.tables.iteritems():
            if name in legacy_tables:
                continue
            for column in table.columns:
                for fk in column.foreign_keys:
                    fk_targets[fk.target_fullname].add(fk.parent)
        return dict(fk_targets)

    def _get_uuid(self):
        uuid = unicode(uuid4())
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
        when the new row is isnerted.

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
            fullname = '{}.{}'.format(column.table.fullname, column.name)
            type_ = 'idref_set'
        else:
            if target_column is not None:
                fullname = '{}.{}'.format(target_column.table.fullname, target_column.name)
            else:
                fk = _get_single_fk(column)
                fullname = fk.target_fullname
                target_column = fk.column
            if target_column is User.__table__.c.id and value is not None:
                type_ = 'userref'
            else:
                type_ = 'idref'
        uuid = self.id_map[fullname].setdefault(value, self._get_uuid())
        if type_ == 'userref' and uuid not in self.users:
            user = User.get(value)
            self.users[uuid] = None if user.is_system else {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'title': user._title,
                'affiliation': user.affiliation,
                'phone': user.phone,
                'address': user.address,
                'email': user.email,
                'all_emails': list(user.all_emails)
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
        with get_storage(storage_backend).open(storage_file_id) as f:
            self._add_file(uuid, size, f)
        data['__file__'] = ('file', {'uuid': uuid, 'filename': filename, 'content_type': content_type, 'size': size,
                                     'md5': md5})

    def _serialize_objects(self, table, filter_):
        spec = self.spec[table.fullname]
        query = db.session.query(table).filter(filter_)
        if spec['order']:
            # Use a custom order instead of whatever the DB uses by default.
            # This is mainly needed for self-referential FKs and CHECK
            # constraints that require certain objects to be exported before
            # the ones referencing them
            order = eval(spec['order'], _make_globals())
            if not isinstance(order, tuple):
                order = (order,)
            query = query.order_by(*order)
        query = query.order_by(*table.primary_key.columns)
        cascaded = []
        for row in query:
            if spec['skipif'] and eval(spec['skipif'], _make_globals(ROW=row)):
                continue
            rowdict = row._asdict()
            pk = tuple(v for k, v in rowdict.viewitems() if table.c[k].primary_key)
            if (table.fullname, pk) in self.seen_rows:
                if spec['allow_duplicates']:
                    continue
                else:
                    raise Exception('Trying to serialize already-serialized row')
            self.seen_rows.add((table.fullname, pk))
            data = {}
            for col, value in rowdict.viewitems():
                col = unicode(col)  # col names are `quoted_name` objects
                col_fullname = '{}.{}'.format(table.fullname, col)
                col_custom = spec['cols'].get(col, _notset)
                colspec = table.c[col]
                if col_custom is None:
                    # column is explicitly excluded
                    continue
                elif col_custom is not _notset:
                    # column has custom code to process its value (and possibly name)
                    if value is not None:
                        def _get_event_idref():
                            key = '{}.{}'.format(Event.__table__.fullname, Event.id.name)
                            assert key in self.id_map
                            return 'idref', self.id_map[key][self.event.id]

                        def _make_id_ref(target, id_):
                            return self._make_idref(None, id_, target_column=_resolve_col(target))

                        data.update(_exec_custom(col_custom, VALUE=value, MAKE_EVENT_REF=_get_event_idref,
                                                 MAKE_ID_REF=_make_id_ref))
                elif col_fullname in self.fk_map:
                    # an FK references this column -> generate a uuid
                    data[col] = self._make_idref(colspec, value, incoming=colspec.primary_key)
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
            # export objects referenced in outgoing FKs before the row
            # itself as the FK column might not be nullable
            for col, fk in spec['fks_out'].iteritems():
                value = rowdict[col]
                for x in self._serialize_objects(fk.table, value == fk):
                    yield x
            yield table.fullname, data
            # serialize objects referencing the current row, but don't export them yet
            for col, fks in spec['fks'].iteritems():
                value = rowdict[col]
                cascaded += [x for fk in fks for x in self._serialize_objects(fk.table, value == fk)]
        # we only add incoming fks after being done with all objects in case one
        # of the referenced objects references another object from the current table
        # that has not been serialized yet (e.g. abstract reviews proposing as duplicate)
        for x in cascaded:
            yield x


class EventImporter(object):
    def __init__(self, source_file, category_id=0, create_users=None, verbose=False, force=False):
        self.source_file = source_file
        self.category_id = category_id
        self.create_users = create_users
        self.verbose = verbose
        self.force = force
        self.archive = tarfile.open(fileobj=source_file)
        self.data = yaml.unsafe_load(self.archive.extractfile('data.yaml'))
        self.id_map = {}
        self.user_map = {}
        self.event_id = None
        self.system_user_id = User.get_system_user().id
        self.spec = self._load_spec()
        self.deferred_idrefs = defaultdict(set)

    def _load_spec(self):
        def _resolve_col_name(col):
            colspec = _resolve_col(col)
            return '{}.{}'.format(colspec.table.fullname, colspec.name)

        def _process_format(fmt, _re=re.compile(r'<([^>]+)>')):
            fmt = _re.sub(r'%{reset}%{cyan}\1%{reset}%{blue!}', fmt)
            return cformat('- %{blue!}' + fmt)

        with open(os.path.join(current_app.root_path, 'modules', 'events', 'export.yaml')) as f:
            spec = yaml.safe_load(f)

        spec = spec['import']
        spec['defaults'] = {_model_to_table(k): v for k, v in spec.get('defaults', {}).iteritems()}
        spec['custom'] = {_model_to_table(k): v for k, v in spec.get('custom', {}).iteritems()}
        spec['missing_users'] = {_resolve_col_name(k): v for k, v in spec.get('missing_users', {}).iteritems()}
        spec['verbose'] = {_model_to_table(k): _process_format(v) for k, v in spec.get('verbose', {}).iteritems()}
        return spec

    def _load_users(self, data):
        if not data['users']:
            return
        missing = {}
        for uuid, userdata in data['users'].iteritems():
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
            table_data = [['First Name', 'Last Name', 'Email', 'Affiliation']]
            for userdata in sorted(missing.itervalues(), key=itemgetter('first_name', 'last_name', 'email')):
                table_data.append([userdata['first_name'], userdata['last_name'], userdata['email'],
                                   userdata['affiliation']])
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
                for uuid, userdata in missing.iteritems():
                    user = User(first_name=userdata['first_name'],
                                last_name=userdata['last_name'],
                                email=userdata['email'],
                                secondary_emails=set(userdata['all_emails']) - {userdata['email']},
                                address=userdata['address'],
                                phone=userdata['phone'],
                                affiliation=userdata['affiliation'],
                                title=userdata['title'],
                                is_pending=True)
                    db.session.add(user)
                    db.session.flush()
                    self.user_map[uuid] = user.id
                    if self.verbose:
                        click.echo(cformat("- %{cyan}User%{blue!} '{}' ({})").format(user.full_name, user.email))
            else:
                click.secho('Skipping missing users', fg='magenta')

    def deserialize(self):
        if not self.force and self.data['indico_version'] != indico.__version__:
            click.secho('Version mismatch: trying to import event exported with {} to version {}'
                        .format(self.data['indico_version'], indico.__version__), fg='red')
            return None
        self._load_users(self.data)
        # we need the event first since it generates the event id, which may be needed
        # in case of outgoing FKs on the event model
        objects = sorted(self.data['objects'], key=lambda x: x[0] != 'events.events')
        for tablename, tabledata in objects:
            self._deserialize_object(db.metadata.tables[tablename], tabledata)
        if self.deferred_idrefs:
            # Any reference to an ID that was exported need to be replaced
            # with an actual ID at some point - either immediately (if the
            # referenced row was already imported) or later (usually in case
            # of circular dependencies where one of the IDs is not available
            # when the row is inserted).
            click.secho('BUG: Not all deferred idrefs have been consumed', fg='red')
            for uuid, values in self.deferred_idrefs.iteritems():
                click.secho('{}:'.format(uuid), fg='yellow', bold=True)
                for table, col, pk_value in values:
                    click.secho('  - {}.{} ({})'.format(table.fullname, col, pk_value), fg='yellow')
            raise Exception('Not all deferred idrefs have been consumed')
        event = Event.get(self.event_id)
        event.log(EventLogRealm.event, EventLogKind.other, 'Event', 'Event imported from another Indico instance')
        self._associate_users_by_email(event)
        db.session.flush()
        return event

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
        query = EventPerson.query.with_parent(event).filter(EventPerson.user_id.is_(None), EventPerson.email != '')
        for person in query:
            person.user = get_user_by_email(person.email)

        # registrations
        for registration in Registration.query.with_parent(event).filter(Registration.user_id.is_(None)):
            registration.user = get_user_by_email(registration.email)

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
                mode = self.spec['missing_users']['{}.{}'.format(colspec.table.fullname, colspec.name)]
                if mode == 'system':
                    return self.system_user_id
                elif mode == 'none':
                    return None
                elif mode == 'skip':
                    raise MissingUser(self.data['users'][value], skip=True)
                else:
                    raise MissingUser(self.data['users'][value], run=mode)
        else:
            raise ValueError('unknown type: ' + type_)

    def _get_file_storage_path(self, id_, filename):
        # we use a generic path to store all imported files since we
        # are on the table level here and thus cannot use relationships
        # and the orignal models' logic to construct paths
        path_segments = ['event', strict_unicode(self.event_id), 'imported']
        filename = '{}-{}'.format(id_, filename)
        path = posixpath.join(*(path_segments + [filename]))
        return path

    def _process_file(self, id_, data):
        storage_backend = config.ATTACHMENT_STORAGE
        storage = get_storage(storage_backend)
        extracted = self.archive.extractfile(data['uuid'])
        path = self._get_file_storage_path(id_, data['filename'])
        storage_file_id, md5 = storage.save(path, data['content_type'], data['filename'], extracted)
        assert data['size'] == storage.getsize(storage_file_id)
        if data['md5']:
            assert data['md5'] == md5
        return {
            'storage_backend': storage_backend,
            'storage_file_id': storage_file_id,
            'content_type': data['content_type'],
            'filename': data['filename'],
            'size': data['size'],
            'md5': md5
        }

    def _deserialize_object(self, table, data):
        is_event = (table == Event.__table__)
        import_defaults = self.spec['defaults'].get(table.fullname, {})
        import_custom = self.spec['custom'].get(table.fullname, {})
        set_idref = None
        file_data = None
        insert_values = dict(import_defaults)
        deferred_idrefs = {}
        missing_user_skip = False
        missing_user_exec = set()
        if is_event:
            # the exported data may contain only one event
            assert self.event_id is None
            insert_values['category_id'] = self.category_id
        for col, value in data.iteritems():
            if isinstance(value, tuple):
                if value[0] == 'idref_set':
                    assert set_idref is None
                    set_idref = value[1]
                    continue
                elif value[0] == 'file':
                    # import files later in case we end up skipping the column due to a missing user
                    assert file_data is None
                    file_data = value[1]
                    continue
            colspec = table.c[col]
            if col in import_custom:
                # custom python code to process the imported value
                def _resolve_id_ref(value):
                    return self._convert_value(colspec, value)
                rv = _exec_custom(import_custom[col], VALUE=value, RESOLVE_ID_REF=_resolve_id_ref)
                assert rv.keys() == [col]
                insert_values[col] = rv[col]
                continue
            try:
                insert_values[col] = self._convert_value(colspec, value)
            except IdRefDeferred as exc:
                deferred_idrefs[col] = exc.uuid
            except MissingUser as exc:
                if exc.skip:
                    click.secho('! Skipping row in {} due to missing user ({})'.format(table.fullname, exc.username),
                                fg='yellow')
                    missing_user_skip = True
                else:
                    missing_user_exec.add(exc.run)
            except MissingUserCascaded:
                click.secho('! Skipping row in {} as parent row was skipped due to a missing user'
                            .format(table.fullname), fg='yellow')
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
                insert_values.update(self._process_file(pk_value, file_data))
            else:
                insert_values.update(self._process_file(unicode(uuid4()), file_data))
        if self.verbose and table.fullname in self.spec['verbose']:
            fmt = self.spec['verbose'][table.fullname]
            click.echo(fmt.format(**insert_values))
        res = db.session.execute(table.insert(), insert_values)
        if set_idref is not None:
            # if a column was marked as having incoming FKs, store
            # the ID so the reference can be resolved to the ID
            self._set_idref(set_idref, _get_inserted_pk(res))
        if is_event:
            self.event_id = _get_inserted_pk(res)
        for col, uuid in deferred_idrefs.iteritems():
            # store all the data needed to resolve a deferred ID reference
            # later once the ID is available
            self.deferred_idrefs[uuid].add((table, col, _get_inserted_pk(res)))

    def _set_idref(self, uuid, id_):
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
