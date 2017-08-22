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

import os
import posixpath
import tarfile
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from io import BytesIO
from operator import itemgetter
from uuid import uuid4

import click
import dateutil.parser
import yaml
import yaml.resolver
from flask import current_app
from sqlalchemy import inspect
from terminaltables import AsciiTable

import indico
from indico.core import Config
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


def import_event(source_file, category_id, force=False):
    """Import a previously-exported event.

    It is up to the caller of this function to commit the transaction.

    :param source_file: An open file object containing the exported event.
    :param category_id: ID of the category in which to create the event.
    :param force: Whether to ignore version conflicts.
    :return: The imported event.
    """
    importer = EventImporter(source_file, category_id)
    return importer.deserialize(force)


def _model_to_table(name):
    return getattr(db.m, name).__table__.fullname if name[0].isupper() else name


def _make_globals(**extra):
    globals_ = {name: cls for name, cls in db.Model._decl_class_registry.iteritems()
                if hasattr(cls, '__table__')}
    globals_.update(extra)
    return globals_


def _exec_custom(code, **extra):
    globals_ = _make_globals(**extra)
    locals_ = {}
    exec(code, globals_, locals_)
    return {unicode(k): v for k, v in locals_.iteritems() if k[0] != '_'}


def _resolve_col(col):
    attr = eval(col, _make_globals()) if isinstance(col, basestring) else col
    if isinstance(attr, db.Column):
        return attr
    assert len(attr.prop.columns) == 1
    return attr.prop.columns[0]


def _get_single_fk(col):
    # find the column-specific FK, not some compound fk containing this column
    fks = [x for x in col.foreign_keys if len(x.constraint.columns) == 1]
    assert len(fks) == 1
    return fks[0]


def _get_pk(table):
    pks = inspect(table).primary_key.columns.values()
    assert len(pks) == 1
    return pks[0]


def _get_inserted_pk(result):
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
            self.users[uuid] = {
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
        if isinstance(value, (date, datetime)):
            return type(value).__name__, value.isoformat()
        elif isinstance(value, bytes) and len(value) > 1000:
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
        if data.get('storage_file_id') is None:
            return
        assert '__file__' not in data
        storage_backend = data.pop('storage_backend')
        storage_file_id = data.pop('storage_file_id')
        filename = data.pop('filename')
        content_type = data.pop('content_type')
        size = data.pop('size')
        uuid = self._get_uuid()
        with get_storage(storage_backend).open(storage_file_id) as f:
            self._add_file(uuid, size, f)
        data['__file__'] = ('file', {'uuid': uuid, 'filename': filename, 'content_type': content_type, 'size': size})

    def _serialize_objects(self, table, filter_):
        spec = self.spec[table.fullname]
        query = db.session.query(table).filter(filter_)
        if spec['order']:
            order = eval(spec['order'], _make_globals())
            if not isinstance(order, tuple):
                order = (order,)
            query = query.order_by(*order)
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
            for col, fk in spec['fks_out'].iteritems():
                value = rowdict[col]
                for x in self._serialize_objects(fk.table, value == fk):
                    yield x
            yield table.fullname, data
            for col, fks in spec['fks'].iteritems():
                value = rowdict[col]
                cascaded += [x for fk in fks for x in self._serialize_objects(fk.table, value == fk)]
        # we only add incoming fks after being done with all objects in case one
        # of the referenced objects references another object from the current table
        # that has not been serialized yet (e.g. abstract reviews proposing as duplicate)
        for x in cascaded:
            yield x


class EventImporter(object):
    def __init__(self, source_file, category_id):
        self.source_file = source_file
        self.category_id = category_id
        self.archive = tarfile.open(fileobj=source_file)
        self.data = yaml.load(self.archive.extractfile('data.yaml'))
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

        with open(os.path.join(current_app.root_path, 'modules', 'events', 'export.yaml')) as f:
            spec = yaml.safe_load(f)

        spec = spec['import']
        spec['defaults'] = {_model_to_table(k): v for k, v in spec.get('defaults', {}).iteritems()}
        spec['custom'] = {_model_to_table(k): v for k, v in spec.get('custom', {}).iteritems()}
        spec['missing_users'] = {_resolve_col_name(k): v for k, v in spec.get('missing_users', {}).iteritems()}
        return spec

    def _load_users(self, data):
        if not data['users']:
            return
        missing = {}
        for uuid, userdata in data['users'].iteritems():
            user = (User.query
                    .filter(User.all_emails.contains(db.func.any(userdata['all_emails'])),
                            ~User.is_deleted)
                    .one_or_none())
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
            click.echo('Do you want to create these users now?')
            click.echo('If you choose to not create them, the behavior depends on where the user would be used:')
            click.echo('- If the user is not required, it will be omitted.')
            click.echo('- If a user is required but using the system user will not cause any problems or look '
                       'weird, the system user will be used.')
            click.echo('- In case neither is possible, e.g. in abstract reviews or ACLs, these objects will '
                       'be skipped altogether!')
            if click.confirm('Create the missing users?', default=False):  # TODO default=True
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

    def deserialize(self, force):
        if not force and self.data['indico_version'] != indico.__version__:
            click.secho('Version mismatch: trying to import event exported with {} to version {}'
                        .format(self.data['indico_version'], indico.__version__), fg='red')
            return None
        self._load_users(self.data)
        for tablename, tabledata in self.data['objects']:
            self._deserialize_object(db.metadata.tables[tablename], tabledata)
        if self.deferred_idrefs:
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
        for user in User.query.filter(~User.is_deleted, User.all_emails.contains(db.func.any(emails))):
            EventPrincipal.replace_email_with_user(user, 'event')

        # session principals
        query = (SessionPrincipal.query
                 .filter(SessionPrincipal.session.has(Session.event == event),
                         SessionPrincipal.type == PrincipalType.email))
        emails = [p.email for p in query]
        for user in User.query.filter(~User.is_deleted, User.all_emails.contains(db.func.any(emails))):
            SessionPrincipal.replace_email_with_user(user, 'session')

        # contribution principals
        query = (ContributionPrincipal.query
                 .filter(ContributionPrincipal.contribution.has(Contribution.event == event),
                         ContributionPrincipal.type == PrincipalType.email))
        emails = [p.email for p in query]
        for user in User.query.filter(~User.is_deleted, User.all_emails.contains(db.func.any(emails))):
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
        path_segments = ['event', strict_unicode(self.event_id), 'imported']
        filename = '{}-{}'.format(id_, filename)
        path = posixpath.join(*(path_segments + [filename]))
        return path

    def _process_file(self, id_, data):
        storage_backend = Config.getInstance().getAttachmentStorage()
        storage = get_storage(storage_backend)
        extracted = self.archive.extractfile(data['uuid'])
        path = self._get_file_storage_path(id_, data['filename'])
        storage_file_id = storage.save(path, data['content_type'], data['filename'], extracted)
        assert data['size'] == storage.getsize(storage_file_id)
        return {
            'storage_backend': storage_backend,
            'storage_file_id': storage_file_id,
            'content_type': data['content_type'],
            'filename': data['filename'],
            'size': data['size']
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
            assert self.event_id is None
            insert_values['category_id'] = self.category_id
        for col, value in data.iteritems():
            if isinstance(value, tuple):
                if value[0] == 'idref_set':
                    assert set_idref is None
                    set_idref = value[1]
                    continue
                elif value[0] == 'file':
                    assert file_data is None
                    file_data = value[1]
                    continue
            colspec = table.c[col]
            if col in import_custom:
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
                    click.secho('Skipping row in {} due to missing user ({})'.format(table.fullname, exc.username),
                                fg='yellow')
                    missing_user_skip = True
                else:
                    missing_user_exec.add(exc.run)
            except MissingUserCascaded:
                click.secho('Skipping row in {} as parent row was skipped due to a missing user'
                            .format(table.fullname), fg='yellow')
                missing_user_skip = True
        if missing_user_skip:
            if set_idref is not None:
                self.id_map[set_idref] = None
            return
        elif missing_user_exec:
            for code in missing_user_exec:
                insert_values.update(_exec_custom(code))
        if file_data is not None:
            pk_name = _get_pk(table).name
            assert pk_name not in insert_values
            stmt = db.func.nextval(db.func.pg_get_serial_sequence(table.fullname, pk_name))
            insert_values[pk_name] = pk_value = db.session.query(stmt).scalar()
            insert_values.update(self._process_file(pk_value, file_data))
        res = db.session.execute(table.insert(), insert_values)
        if set_idref is not None:
            self._set_idref(set_idref, _get_inserted_pk(res))
        if is_event:
            self.event_id = _get_inserted_pk(res)
        for col, uuid in deferred_idrefs.iteritems():
            self.deferred_idrefs[uuid].add((table, col, _get_inserted_pk(res)))

    def _set_idref(self, uuid, id_):
        self.id_map[uuid] = id_
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
