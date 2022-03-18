# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.registration.models.form_fields import RegistrationFormField, RegistrationFormFieldData
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import RegistrationFormItem
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.modules.events.reminders import logger
from indico.util.date_time import now_utc


@celery.periodic_task(name='registration_fields_retention_period', run_every=crontab(hour='*/24'))
def delete_field_data():
    registration_data = (RegistrationData.query
                         .join(RegistrationFormFieldData)
                         .join(RegistrationFormField, RegistrationFormFieldData.field_id == RegistrationFormField.id)
                         .join(RegistrationForm)
                         .join(Event)
                         .filter(~RegistrationFormItem.is_purged,
                                 RegistrationFormItem.retention_period.isnot(None),
                                 Event.end_dt + RegistrationFormItem.retention_period <= now_utc())
                         .all())

    for data in registration_data:
        logger.info(f'Deleting registration field data: {data}')
        data.data = None
        if data.field_data.field.field_impl.is_file_field:
            try:
                data.delete()
            except Exception as e:
                logger.error(f'Failed to delete file: {e}')
        data.field_data.field.is_purged = True
    db.session.commit()
