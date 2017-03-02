"""Store static sites properly

Revision ID: 4dd759c93728
Revises: 43430dd98afb
Create Date: 2017-02-03 18:04:43.387165
"""

import os

import sqlalchemy as sa
from alembic import context, op

from indico.core.config import Config
from indico.core.storage.backend import get_storage
from indico.modules.events.static.models.static import StaticSiteState


# revision identifiers, used by Alembic.
revision = '4dd759c93728'
down_revision = '43430dd98afb'


def _convert_path(path):
    # XXX: there's no cleaner way for this since our flask-migrate version does not forward alembic's x-args
    conv = os.environ.get('STORAGE_PATH_CONV')
    if conv:
        from_, to = conv.split('=', 1)
        if path.startswith(from_):
            path = path.replace(from_, to, 1)
    backends = {k: v.split(':', 1)[1] for k, v in Config.getInstance().getStorageBackends().iteritems()
                if (v.startswith('fs:') or v.startswith('fs-readonly:')) and path.startswith(v.split(':', 1)[1])}
    backend = max(backends.iteritems(), key=lambda x: len(x[1])) if backends else None
    if backend is None:
        if not conv:
            print 'You may need to set the STORAGE_PATH_CONV env var to a mapping from the ' \
                  'legacy storage path to one used in StorageBackends.'
        raise Exception('Could not convert path to a storage backend: ' + path)
    return backend[0], path.replace(backend[1], '', 1)


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    res = conn.execute("SELECT id, event_id, state, path FROM events.static_sites WHERE path IS NOT NULL")
    updates = {}
    for row in res:
        if row.state == StaticSiteState.expired.value:
            continue
        elif not os.path.exists(row.path):
            updates[row.id] = {'state': StaticSiteState.expired.value}
            continue
        storage_backend, storage_file_id = _convert_path(row.path)
        updates[row.id] = {
            'storage_backend': storage_backend,
            'storage_file_id': storage_file_id,
            'content_type': 'application/zip',
            'size': os.path.getsize(row.path),
            'filename': 'offline_site_{}.zip'.format(row.event_id)
        }
    op.add_column('static_sites', sa.Column('content_type', sa.String(), nullable=True), schema='events')
    op.add_column('static_sites', sa.Column('filename', sa.String(), nullable=True), schema='events')
    op.add_column('static_sites', sa.Column('size', sa.BigInteger(), nullable=True), schema='events')
    op.add_column('static_sites', sa.Column('storage_backend', sa.String(), nullable=True), schema='events')
    op.add_column('static_sites', sa.Column('storage_file_id', sa.String(), nullable=True), schema='events')
    for id_, values in updates.iteritems():
        values = sorted(values.items())
        stmt = 'UPDATE events.static_sites SET {} WHERE id = %s'.format(', '.join('{}=%s'.format(x[0]) for x in values))
        args = [x[1] for x in values] + [id_]
        conn.execute(stmt, args)
    op.drop_column('static_sites', 'path', schema='events')


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    op.add_column('static_sites', sa.Column('path', sa.String(), nullable=True), schema='events')
    conn = op.get_bind()
    res = conn.execute("""
        SELECT id, storage_backend, storage_file_id
        FROM events.static_sites
        WHERE storage_backend IS NOT NULL
    """)
    for row in res:
        with get_storage(row.storage_backend).get_local_path(row.storage_file_id) as path:
            conn.execute('UPDATE events.static_sites SET path=%s WHERE id=%s', (path, row.id))
    op.drop_column('static_sites', 'storage_file_id', schema='events')
    op.drop_column('static_sites', 'storage_backend', schema='events')
    op.drop_column('static_sites', 'size', schema='events')
    op.drop_column('static_sites', 'filename', schema='events')
    op.drop_column('static_sites', 'content_type', schema='events')
