"""Apply naming convention

Revision ID: 4ae6d2113a2b
Revises: 573faf4ac644
Create Date: 2015-03-09 15:49:20.566037
"""

from alembic import op

from indico.core.db.sqlalchemy.util.bulk_rename import bulk_rename


# revision identifiers, used by Alembic.
revision = '4ae6d2113a2b'
down_revision = '573faf4ac644'


mapping = {
    # indico
    'indico.category_index': {
        'indexes': {
            'category_index_pkey': 'pk_category_index',
            'title_vector_idx': 'ix_category_index_title_vector'
        }
    },
    'indico.settings': {
        'indexes': {
            'settings_pkey': 'pk_settings',
            'ix_indico_settings_module': 'ix_settings_module',
            'ix_indico_settings_name': 'ix_settings_name',
        },
        'constraints': {
            'settings_module_check': 'ck_settings_lowercase_module',
            'settings_name_check': 'ck_settings_lowercase_name',
            'settings_module_name_key': 'uq_settings_module_name',
        }
    },
    # events
    'events.agreements': {
        'indexes': {
            'agreements_pkey': 'pk_agreements',
        },
        'constraints': {
            'agreements_state_check': 'ck_agreements_valid_enum_state',
            'agreements_event_id_type_identifier_key': 'uq_agreements_event_id_type_identifier',
        }
    },
    'events.event_index': {
        'indexes': {
            'event_index_pkey': 'pk_event_index',
            'ix_events_event_index_end_date': 'ix_event_index_end_date',
            'ix_events_event_index_start_date': 'ix_event_index_start_date',
            'title_vector_idx': 'ix_event_index_title_vector'
        }
    },
    'events.payment_transactions': {
        'indexes': {
            'payment_transactions_pkey': 'pk_payment_transactions',
            'ix_events_payment_transactions_event_id': 'ix_payment_transactions_event_id',
            'ix_events_payment_transactions_timestamp': 'ix_payment_transactions_timestamp',
        },
        'constraints': {
            'payment_transactions_amount_check': 'ck_payment_transactions_positive_amount',
            'payment_transactions_status_check': 'ck_payment_transactions_valid_enum_status',
            'payment_transactions_event_id_registrant_id_timestamp_key':
                'uq_payment_transactions_event_id_registrant_id_timestamp',
        }
    },
    'events.requests': {
        'indexes': {
            'requests_pkey': 'pk_requests',
            'ix_events_requests_created_dt': 'ix_requests_created_dt',
            'ix_events_requests_event_id': 'ix_requests_event_id',
        },
        'constraints': {
            'requests_state_check': 'ck_requests_valid_enum_state'
        }
    },
    'events.settings': {
        'indexes': {
            'settings_pkey': 'pk_settings',
            'ix_events_settings_event_id': 'ix_settings_event_id',
            'ix_events_settings_module': 'ix_settings_module',
            'ix_events_settings_name': 'ix_settings_name',
        },
        'constraints': {
            'settings_module_check': 'ck_settings_lowercase_module',
            'settings_name_check': 'ck_settings_lowercase_name',
            'settings_event_id_module_name_key': 'uq_settings_event_id_module_name',
        }
    },
    'events.vc_room_events': {
        'indexes': {
            'vc_room_events_pkey': 'pk_vc_room_events',
            'ix_events_vc_room_events_event_id': 'ix_vc_room_events_event_id',
            'ix_events_vc_room_events_vc_room_id': 'ix_vc_room_events_vc_room_id',
        },
        'constraints': {
            'vc_room_events_link_type_check': 'ck_vc_room_events_valid_enum_link_type',
            'vc_room_events_vc_room_id_fkey': 'fk_vc_room_events_vc_room_id_vc_rooms',
        }
    },
    'events.vc_rooms': {
        'indexes': {
            'vc_rooms_pkey': 'pk_vc_rooms',
            'ix_events_vc_rooms_created_by_id': 'ix_vc_rooms_created_by_id',
        },
        'constraints': {
            'vc_rooms_status_check': 'ck_vc_rooms_valid_enum_status',
        }
    },
    # roombooking
    'roombooking.aspects': {
        'indexes': {
            'aspects_pkey': 'pk_aspects',
        },
        'constraints': {
            'aspects_location_id_fkey': 'fk_aspects_location_id_locations',
        }
    },
    'roombooking.blocked_rooms': {
        'indexes': {
            'blocked_rooms_pkey': 'pk_blocked_rooms',
            'ix_roombooking_blocked_rooms_room_id': 'ix_blocked_rooms_room_id',
        },
        'constraints': {
            'blocked_rooms_state_check': 'ck_blocked_rooms_valid_enum_state',
            'blocked_rooms_blocking_id_fkey': 'fk_blocked_rooms_blocking_id_blockings',
            'blocked_rooms_room_id_fkey': 'fk_blocked_rooms_room_id_rooms',
        }
    },
    'roombooking.blocking_principals': {
        'indexes': {
            'blocking_principals_pkey': 'pk_blocking_principals',
        },
        'constraints': {
            'blocking_principals_blocking_id_fkey': 'fk_blocking_principals_blocking_id_blockings',
        }
    },
    'roombooking.blockings': {
        'indexes': {
            'blockings_pkey': 'pk_blockings',
            'ix_roombooking_blockings_end_date': 'ix_blockings_end_date',
            'ix_roombooking_blockings_start_date': 'ix_blockings_start_date',
        },
    },
    'roombooking.equipment_types': {
        'indexes': {
            'equipment_types_pkey': 'pk_equipment_types',
            'ix_roombooking_equipment_types_name': 'ix_equipment_types_name',
        },
        'constraints': {
            'equipment_types_location_id_fkey': 'fk_equipment_types_location_id_locations',
            'equipment_types_parent_id_fkey': 'fk_equipment_types_parent_id_equipment_types',
            'equipment_types_name_location_id_key': 'uq_equipment_types_name_location_id',
        }
    },
    'roombooking.holidays': {
        'indexes': {
            'holidays_pkey': 'pk_holidays',
            'ix_roombooking_holidays_date': 'ix_holidays_date',
        },
        'constraints': {
            'holidays_location_id_fkey': 'fk_holidays_location_id_locations',
            'holidays_date_location_id_key': 'uq_holidays_date_location_id',
        }
    },
    'roombooking.locations': {
        'indexes': {
            'locations_pkey': 'pk_locations',
            'ix_roombooking_locations_name': 'ix_locations_name',
        },
        'constraints': {
            'fk_default_aspect_id': 'fk_locations_default_aspect_id',
        }
    },
    'roombooking.photos': {
        'indexes': {
            'photos_pkey': 'pk_photos',
        },
    },
    'roombooking.reservation_edit_logs': {
        'indexes': {
            'reservation_edit_logs_pkey': 'pk_reservation_edit_logs',
            'ix_roombooking_reservation_edit_logs_reservation_id': 'ix_reservation_edit_logs_reservation_id',
        },
        'constraints': {
            'reservation_edit_logs_reservation_id_fkey': 'fk_reservation_edit_logs_reservation_id_reservations',
        }
    },
    'roombooking.reservation_equipment': {
        'indexes': {
            'reservation_equipment_pkey': 'pk_reservation_equipment',
        },
        'constraints': {
            'reservation_equipment_equipment_id_fkey': 'fk_reservation_equipment_equipment_id_equipment_types',
            'reservation_equipment_reservation_id_fkey': 'fk_reservation_equipment_reservation_id_reservations',
        }
    },
    'roombooking.reservation_occurrences': {
        'indexes': {
            'reservation_occurrences_pkey': 'pk_reservation_occurrences',
            'ix_roombooking_reservation_occurrences_end_dt': 'ix_reservation_occurrences_end_dt',
            'ix_roombooking_reservation_occurrences_start_dt': 'ix_reservation_occurrences_start_dt',
        },
        'constraints': {
            'reservation_occurrences_reservation_id_fkey': 'fk_reservation_occurrences_reservation_id_reservations',
        }
    },
    'roombooking.reservations': {
        'indexes': {
            'reservations_pkey': 'pk_reservations',
            'ix_roombooking_reservations_end_dt': 'ix_reservations_end_dt',
            'ix_roombooking_reservations_event_id': 'ix_reservations_event_id',
            'ix_roombooking_reservations_room_id': 'ix_reservations_room_id',
            'ix_roombooking_reservations_start_dt': 'ix_reservations_start_dt',
        },
        'constraints': {
            'reservations_repeat_frequency_check': 'ck_reservations_valid_enum_repeat_frequency',
            'reservations_room_id_fkey': 'fk_reservations_room_id_rooms',
        }
    },
    'roombooking.room_attribute_values': {
        'indexes': {
            'room_attribute_values_pkey': 'pk_room_attribute_values',
        },
        'constraints': {
            'room_attribute_values_attribute_id_fkey': 'fk_room_attribute_values_attribute_id_room_attributes',
            'room_attribute_values_room_id_fkey': 'fk_room_attribute_values_room_id_rooms',
        }
    },
    'roombooking.room_attributes': {
        'indexes': {
            'room_attributes_pkey': 'pk_room_attributes',
            'ix_roombooking_room_attributes_name': 'ix_room_attributes_name',
        },
        'constraints': {
            'room_attributes_location_id_fkey': 'fk_room_attributes_location_id_locations',
            'room_attributes_parent_id_fkey': 'fk_room_attributes_parent_id_room_attributes',
            'room_attributes_name_location_id_key': 'uq_room_attributes_name_location_id',
        }
    },
    'roombooking.room_bookable_hours': {
        'indexes': {
            'room_bookable_hours_pkey': 'pk_room_bookable_hours',
        },
        'constraints': {
            'room_bookable_hours_room_id_fkey': 'fk_room_bookable_hours_room_id_rooms',
        }
    },
    'roombooking.room_equipment': {
        'indexes': {
            'room_equipment_pkey': 'pk_room_equipment',
        },
        'constraints': {
            'room_equipment_equipment_id_fkey': 'fk_room_equipment_equipment_id_equipment_types',
            'room_equipment_room_id_fkey': 'fk_room_equipment_room_id_rooms',
        }
    },
    'roombooking.room_nonbookable_periods': {
        'indexes': {
            'room_nonbookable_periods_pkey': 'pk_room_nonbookable_periods',
        },
        'constraints': {
            'room_nonbookable_periods_room_id_fkey': 'fk_room_nonbookable_periods_room_id_rooms',
        }
    },
    'roombooking.rooms': {
        'indexes': {
            'rooms_pkey': 'pk_rooms',
            'ix_roombooking_rooms_is_active': 'ix_rooms_is_active',
        },
        'constraints': {
            'rooms_location_id_fkey': 'fk_rooms_location_id_locations',
            'rooms_photo_id_fkey': 'fk_rooms_photo_id_photos',
        }
    },
}


def upgrade():
    for stmt in bulk_rename(mapping):
        op.execute(stmt)


def downgrade():
    for stmt in bulk_rename(mapping, True):
        op.execute(stmt)
