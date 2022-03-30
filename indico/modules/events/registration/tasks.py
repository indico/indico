# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.registration import logger
from indico.modules.events.registration.models.form_fields import RegistrationFormField, RegistrationFormFieldData
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import RegistrationFormItem
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.util.date_time import now_utc


def _group_by_regform(registration_data):
    data_by_regform = defaultdict(list)
    for data in registration_data:
        data_by_regform[data.field_data.field.registration_form].append(data)
    return data_by_regform


@celery.periodic_task(name='registration_fields_retention_period', run_every=crontab(minute='0', hour='3'))
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

    data_by_regform = _group_by_regform(registration_data)
    for regform, regform_data in data_by_regform.items():
        fields = [data.field_data.field for data in regform_data]
        logger.info('Purging fields from regform %r: %r', regform, fields)
        for data in regform_data:
            logger.debug('Deleting registration field data: %r', data)
            # Overwrite with the field's default value.
            # This is cleaner than setting the data to 'None' since some fields
            # expect structured data e.g. Accommodation & {Single,Multi}Choice.
            # This makes the React code relatively simple and we can always distinguish
            # purged fields since they have the 'is_purged' flag set to True
            data.data = data.field_data.field.field_impl.default_value
            if data.field_data.field.field_impl.is_file_field:
                logger.debug('Deleting file: %s', data.filename)
                try:
                    data.delete()
                except Exception as e:
                    logger.error('Failed to delete file for %r: %s', data, e)
            data.field_data.field.is_purged = True
    db.session.commit()
