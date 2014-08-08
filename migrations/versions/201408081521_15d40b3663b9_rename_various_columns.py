"""Rename various columns

Revision ID: 15d40b3663b9
Revises: 22b58de5f40f
Create Date: 2014-08-08 15:21:48.482445
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '15d40b3663b9'
down_revision = '22b58de5f40f'


def upgrade():
    op.alter_column('blockings', 'created_at', new_column_name='created_dt')
    op.alter_column('blockings', 'created_by', new_column_name='created_by_id')
    op.alter_column('photos', 'small_content', new_column_name='thumbnail')
    op.alter_column('photos', 'large_content', new_column_name='data')
    op.alter_column('reservation_occurrences', 'is_sent', new_column_name='notification_sent')
    op.alter_column('reservation_occurrences', 'start', new_column_name='start_dt')
    op.alter_column('reservation_occurrences', 'end', new_column_name='end_dt')
    op.alter_column('reservations', 'created_at', new_column_name='created_dt')
    op.alter_column('reservations', 'created_by', new_column_name='created_by_id')
    op.alter_column('reservations', 'uses_video_conference', new_column_name='uses_vc')
    op.alter_column('reservations', 'needs_video_conference_setup', new_column_name='needs_vc_assistance')
    op.alter_column('reservations', 'needs_general_assistance', new_column_name='needs_assistance')
    op.alter_column('reservations', 'start_date', new_column_name='start_dt')
    op.alter_column('reservations', 'end_date', new_column_name='end_dt')
    op.alter_column('room_nonbookable_dates', 'start_date', new_column_name='start_dt')
    op.alter_column('room_nonbookable_dates', 'end_date', new_column_name='end_dt')
    op.alter_column('rooms', 'notification_for_start', new_column_name='notification_before_days')


def downgrade():
    op.alter_column('rooms', 'notification_before_days', new_column_name='notification_for_start')
    op.alter_column('room_nonbookable_dates', 'end_dt', new_column_name='end_date')
    op.alter_column('room_nonbookable_dates', 'start_dt', new_column_name='start_date')
    op.alter_column('reservations', 'end_dt', new_column_name='end_date')
    op.alter_column('reservations', 'start_dt', new_column_name='start_date')
    op.alter_column('reservations', 'needs_assistance', new_column_name='needs_general_assistance')
    op.alter_column('reservations', 'needs_vc_assistance', new_column_name='needs_video_conference_setup')
    op.alter_column('reservations', 'uses_vc', new_column_name='uses_video_conference')
    op.alter_column('reservations', 'created_by_id', new_column_name='created_by')
    op.alter_column('reservations', 'created_dt', new_column_name='created_at')
    op.alter_column('reservation_occurrences', 'end_dt', new_column_name='end')
    op.alter_column('reservation_occurrences', 'start_dt', new_column_name='start')
    op.alter_column('reservation_occurrences', 'notification_sent', new_column_name='is_sent')
    op.alter_column('photos', 'data', new_column_name='large_content')
    op.alter_column('photos', 'thumbnail', new_column_name='small_content')
    op.alter_column('blockings', 'created_by_id', new_column_name='created_by')
    op.alter_column('blockings', 'created_dt', new_column_name='created_at')
