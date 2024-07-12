# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict

from celery.schedules import crontab

from indico.core import signals
from indico.core.celery import celery
from indico.core.db import db
from indico.core.storage.backend import get_storage
from indico.modules.events import Event
from indico.modules.events.registration import logger
from indico.modules.events.registration.models.form_fields import RegistrationFormField, RegistrationFormFieldData
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.events.registration.util import close_registration
from indico.modules.receipts.models.files import ReceiptFile
from indico.util.date_time import now_utc
from indico.util.string import snakify_keys


def _delete_file(reg_data):
    if reg_data.storage_file_id is None:
        return
    logger.debug('Deleting file: %s', reg_data.filename)
    try:
        reg_data.delete()
    except Exception as e:
        logger.error('Failed to delete file for %r: %s', reg_data, e)


def _group_by_regform(registration_data):
    data_by_regform = defaultdict(list)
    for data in registration_data:
        data_by_regform[data.field_data.field.registration_form].append(data)
    return data_by_regform


@celery.periodic_task(name='registration_fields_retention_period', run_every=crontab(minute='0', hour='3'))
def delete_field_data():
    today = now_utc().date()
    registration_data = (RegistrationData.query
                         .join(RegistrationFormFieldData)
                         .join(RegistrationFormField, RegistrationFormFieldData.field_id == RegistrationFormField.id)
                         .join(RegistrationForm, RegistrationFormField.registration_form_id == RegistrationForm.id)
                         .join(Event)
                         .filter(~RegistrationFormField.is_purged,
                                 RegistrationFormField.retention_period.isnot(None),
                                 db.cast(Event.end_dt, db.Date) + RegistrationFormField.retention_period <= today)
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
            data.data = snakify_keys(data.field_data.field.field_impl.default_value)
            if data.field_data.field.field_impl.is_file_field:
                _delete_file(data)
            data.field_data.field.is_purged = True
    db.session.commit()


@celery.periodic_task(name='registration_retention_period', run_every=crontab(minute='30', hour='3'))
def delete_registrations():
    is_expired = db.and_(RegistrationForm.retention_period.isnot(None),
                         db.cast(Event.end_dt, db.Date) + RegistrationForm.retention_period <= now_utc().date())
    registrations = (Registration.query
                     .join(RegistrationForm, RegistrationForm.id == Registration.registration_form_id)
                     .join(Event)
                     .filter(is_expired)
                     .all())
    regforms = RegistrationForm.query.join(Event).filter(is_expired).all()

    for reg in registrations:
        logger.info('Purging registration: %r', reg)
        signals.event.registration_deleted.send(reg, permanent=True)
        for data in reg.data:
            if data.field_data.field.field_impl.is_file_field:
                _delete_file(data)
        # We need to query all receipts, even those that are soft-deleted
        for receipt in ReceiptFile.query.filter_by(registration=reg):
            # Unclaimed files are cleaned up periodically
            receipt.file.claimed = False
        db.session.delete(reg)

    for regform in regforms:
        close_registration(regform)
        regform.is_purged = True

    db.session.commit()


@celery.task(name='delete_previous_registration_file')
def delete_previous_registration_file(reg_data, storage_backend, storage_file_id):
    if reg_data.storage_backend == storage_backend and reg_data.storage_file_id == storage_file_id:
        return
    logger.debug('Deleting registration file: %s from %s storage', storage_file_id, storage_backend)
    storage = get_storage(storage_backend)
    storage.delete(storage_file_id)
