<% from flask_pluginengine import current_plugin %>"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision}
Create Date: ${create_date}
"""

import sqlalchemy as sa
from alembic import op
${imports + '\n' if imports else ""}
% if not down_revision:
from sqlalchemy.sql.ddl import CreateSchema, DropSchema
% endif


# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}


def upgrade():
% if not down_revision:
    op.execute(CreateSchema('plugin_${ current_plugin.name }'))
% endif
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
    % if not down_revision:
    op.execute(DropSchema('plugin_${ current_plugin.name }'))
    % endif
