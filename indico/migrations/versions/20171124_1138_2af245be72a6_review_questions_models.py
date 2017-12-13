"""Add columns to review questions and review ratings tables.

Revision ID: 2af245be72a6
Revises: 566d5de4e0e5
Create Date: 2017-11-24 11:38:33.292283
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '2af245be72a6'
down_revision = '566d5de4e0e5'
branch_labels = None
depends_on = None

tables = (('event_abstracts', 'abstract_review_ratings', 'abstract_review_questions'),
          ('event_paper_reviewing', 'review_ratings', 'review_questions'))


def upgrade():
    for schema, ratings_table, questions_table in tables:
        op.alter_column(questions_table, 'text', new_column_name='title', schema=schema)
        op.add_column(questions_table, sa.Column('field_type', sa.String(), nullable=False, server_default='rating'),
                      schema=schema)
        op.alter_column(questions_table, 'field_type', server_default=None, schema=schema)
        op.add_column(questions_table, sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true'),
                      schema=schema)
        op.alter_column(questions_table, 'is_required', server_default=None, schema=schema)
        op.add_column(questions_table, sa.Column('field_data', sa.JSON(), nullable=False, server_default='{}'),
                      schema=schema)
        op.alter_column(questions_table, 'field_data', server_default=None, schema=schema)
        op.add_column(questions_table, sa.Column('description', sa.Text(), nullable=False, server_default=''),
                      schema=schema)
        op.alter_column(questions_table, 'description', server_default=None, schema=schema)
        op.execute('ALTER TABLE {0}.{1} ALTER COLUMN "value" TYPE JSON USING to_json(value)'.format(schema,
                                                                                                    ratings_table))


def downgrade():
    for schema, ratings_table, questions_table in tables:
        op.alter_column(questions_table, 'title', new_column_name='text', schema=schema)
        op.execute("DELETE FROM {0}.{1} WHERE question_id IN(SELECT id FROM {0}.{2} "
                   "WHERE field_type != 'rating' OR NOT is_required)".format(schema, ratings_table, questions_table))
        op.execute("DELETE FROM {0}.{1} WHERE field_type != 'rating'".format(schema, questions_table))
        op.execute('ALTER TABLE {0}.{1} ALTER COLUMN "value" TYPE INT USING value::TEXT::INT'.format(schema,
                                                                                                     ratings_table))

        op.drop_column(questions_table, 'field_type', schema=schema)
        op.drop_column(questions_table, 'is_required', schema=schema)
        op.drop_column(questions_table, 'field_data', schema=schema)
        op.drop_column(questions_table, 'description', schema=schema)
