"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision}
Create Date: ${create_date}
"""

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

from indico.core.db import db


# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}


def upgrade():
    upgrade_schema()
    upgrade_data()


def downgrade():
    downgrade_data()
    downgrade_schema()


def upgrade_schema():
    ${upgrades if upgrades else "pass"}


def upgrade_data():
    pass
    # db.session.commit()


def downgrade_schema():
    ${downgrades if downgrades else "pass"}


def downgrade_data():
    pass
    # db.session.commit()
