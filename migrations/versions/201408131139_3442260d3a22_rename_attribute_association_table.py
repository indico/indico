"""Rename attribute association table

Revision ID: 3442260d3a22
Revises: 9a8776f2ec2
Create Date: 2014-08-13 11:39:46.358842
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3442260d3a22'
down_revision = '9a8776f2ec2'


def upgrade():
    op.rename_table('rooms_attributes_association', 'room_attribute_values', schema='roombooking')


def downgrade():
    op.rename_table('room_attribute_values', 'rooms_attributes_association', schema='roombooking')
