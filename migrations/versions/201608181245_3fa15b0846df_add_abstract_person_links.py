"""Add abstract person links

Revision ID: 3fa15b0846df
Revises: 11890f58b1df
Create Date: 2016-08-18 12:45:47.549559
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.abstracts.models.persons import AuthorType
from indico.modules.users.models.users import UserTitle


# revision identifiers, used by Alembic.
revision = '3fa15b0846df'
down_revision = '11890f58b1df'


def upgrade():
    op.create_table(
        'abstract_person_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('person_id', sa.Integer(), nullable=False, index=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('title', PyIntEnum(UserTitle), nullable=True),
        sa.Column('affiliation', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('is_speaker', sa.Boolean(), nullable=False),
        sa.Column('author_type', PyIntEnum(AuthorType), nullable=False),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['person_id'], ['events.persons.id']),
        sa.UniqueConstraint('person_id', 'abstract_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )


def downgrade():
    op.drop_table('abstract_person_links', schema='event_abstracts')
