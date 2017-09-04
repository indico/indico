"""Add oauth system_app_type

Revision ID: 09fd62e56097
Revises: dc2c2fa6f5be
Create Date: 2017-08-30 11:58:34.857558
"""

import sqlalchemy as sa
from alembic import context, op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.oauth.models.applications import OAuthApplication, SystemAppType


# revision identifiers, used by Alembic.
revision = '09fd62e56097'
down_revision = 'dc2c2fa6f5be'
branch_labels = None
depends_on = None


def _create_app(system_app_type):
    insert = OAuthApplication.__table__.insert()
    op.execute(insert.values(system_app_type=system_app_type, **system_app_type.default_data))


def _update_app(app_id, system_app_type):
    update = OAuthApplication.__table__.update()
    if app_id.isdigit():
        update = update.where(OAuthApplication.__table__.c.id == int(app_id))
    else:
        update = update.where(OAuthApplication.__table__.c.client_id == app_id)
    op.execute(update.values(system_app_type=system_app_type, **system_app_type.enforced_data))


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    xargs = context.get_x_argument(as_dictionary=True)
    checkin_app_id = xargs.get('checkin_app_id')
    flower_app_id = xargs.get('flower_app_id')
    op.add_column('applications',
                  sa.Column('system_app_type', PyIntEnum(SystemAppType), nullable=False, server_default='0'),
                  schema='oauth')
    op.alter_column('applications', 'system_app_type', server_default=None, schema='oauth')
    op.create_index(None, 'applications', ['system_app_type'], unique=True, schema='oauth',
                    postgresql_where=sa.text('system_app_type != 0'))
    if checkin_app_id is None:
        _create_app(SystemAppType.checkin)
    else:
        _update_app(checkin_app_id, SystemAppType.checkin)
    if flower_app_id is None:
        _create_app(SystemAppType.flower)
    else:
        _update_app(flower_app_id, SystemAppType.flower)


def downgrade():
    op.drop_column('applications', 'system_app_type', schema='oauth')
