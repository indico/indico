# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import yaml
from celery.schedules import crontab
from sqlalchemy.orm.attributes import flag_modified

from indico.core.celery import celery
from indico.core.config import config
from indico.core.db import db
from indico.core.notifications import email_sender, make_email
from indico.core.storage.backend import StorageError
from indico.modules.attachments.models.attachments import AttachmentFile
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.modules.files.models.files import File
from indico.modules.users import logger
from indico.modules.users.export import get_abstracts, get_attachments, get_papers, get_registration_data
from indico.modules.users.models.export import DataExportOptions, DataExportRequest, DataExportRequestState
from indico.modules.users.models.users import ProfilePictureSource, User
from indico.modules.users.util import get_gravatar_for_user, set_user_avatar
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.iterables import committing_iterator
from indico.util.string import crc32
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for


@celery.periodic_task(name='update_gravatars', run_every=crontab(minute='0', hour='0'))
def update_gravatars(user=None):
    if user is not None:
        # explicitly scheduled update (after an email change)
        if user.picture_source not in (ProfilePictureSource.gravatar, ProfilePictureSource.identicon):
            return
        users = [user]
    else:
        users = User.query.filter(~User.is_deleted, User.picture_source == ProfilePictureSource.gravatar).all()
    for u in committing_iterator(users):
        _do_update_gravatar(u)


def _do_update_gravatar(user):
    gravatar, lastmod = get_gravatar_for_user(user, identicon=False, lastmod=user.picture_metadata['lastmod'])
    if gravatar is None:
        logger.debug('Gravatar for %r did not change (not modified)', user)
        return
    if crc32(gravatar) == user.picture_metadata['hash']:
        logger.debug('Gravatar for %r did not change (same hash)', user)
        user.picture_metadata['lastmod'] = lastmod
        flag_modified(user, 'picture_metadata')
        return
    set_user_avatar(user, gravatar, 'gravatar', lastmod)
    logger.info('Gravatar of user %s updated', user)


def export_user_data(user, options):
    """Generate a zip file with all user data and save it in user.data_export_request."""
    export_request = user.data_export_request
    if export_request and export_request.is_running:
        return

    # ughh why isn't there an ORM upsert..
    if export_request:
        db.session.delete(export_request)
        db.session.commit()
    export_request = DataExportRequest(user=user, selected_options=options, state=DataExportRequestState.running)
    db.session.commit()

    temp_file = NamedTemporaryFile(suffix='.zip', dir=config.TEMP_DIR, delete=False)
    try:
        generate_zip(user, options, temp_file)
    except Exception:
        logger.exception('Could not create a zip file for export %r', export_request)
        export_request.state = DataExportRequestState.failed
        export_request.file = None
        Path(temp_file.name).unlink(missing_ok=True)
        notify_data_export_failure(export_request)

    file = File(filename='data-export.zip', content_type='application/zip')
    try:
        file.save(('user', user.id), temp_file)
        file.claim()
        export_request.file = file
        export_request.state = DataExportRequestState.success
        db.session.commit()
    except Exception:
        logger.exception('Could not create a user data export %r', export_request)
        export_request.state = DataExportRequestState.failed
        export_request.file = None
        file.delete()
        db.session.commit()
        notify_data_export_failure(export_request)
    else:
        notify_data_export_success(export_request)
    finally:
        Path(temp_file.name).unlink(missing_ok=True)


@celery.task(name='export_user_data')
def export_user_data_task(user, options):
    export_user_data(user, options)


def get_data(user, options):
    from indico.modules.users.schemas import UserDataExportSchema

    options_map = {
        DataExportOptions.contribs: ('contributions', 'subcontributions'),
        DataExportOptions.abstracts_papers: ('abstracts', 'papers'),
        DataExportOptions.misc: ('miscellaneous',),
    }
    fields = []
    for opt in options:
        fields += options_map.get(opt, (opt.name,))
    return UserDataExportSchema(only=fields).dump(user)


def generate_zip(user, options, temp_file):
    data = get_data(user, options)

    with ZipFile(temp_file.name, 'w', allowZip64=True) as zip_file:
        zip_file.writestr('/data.yml', yaml.dump(data))

        if DataExportOptions.registrations in options:
            registration_data = get_registration_data(user)
            write_registration_files(zip_file, registration_data)

        if DataExportOptions.attachments in options:
            attachments = get_attachments(user)
            write_attachment_files(zip_file, attachments)

        if DataExportOptions.abstracts_papers in options:
            abstracts = get_abstracts(user)
            papers = get_papers(user)
            write_abstract_files(zip_file, abstracts)
            write_paper_files(zip_file, papers)


def write_registration_files(zip_file, registration_data):
    for data in registration_data:
        write_file(zip_file, data)


def write_attachment_files(zip_file, attachments):
    for attachment in attachments:
        write_file(zip_file, attachment.file)


def write_abstract_files(zip_file, abstracts):
    for abstract in abstracts:
        for file in abstract.files:
            write_file(zip_file, file)


def write_paper_files(zip_file, papers):
    for paper in papers:
        for file in paper.files:
            write_file(zip_file, file)


def write_file(zip_file, object):
    path = build_storage_path(object)
    with object.open() as f:
        zip_file.writestr(path, f.read())


def build_storage_path(object):
    if isinstance(object, RegistrationData):
        event = object.registration.event
        prefix = 'registrations'
        folder = f'{event.id}_{event.title}'
    elif isinstance(object, AttachmentFile):
        prefix = 'attachments'
        folder = ''
    elif isinstance(object, AbstractFile):
        prefix = 'abstracts'
        folder = f'{object.abstract.id}_{object.abstract.title}'
    else:
        prefix = 'papers'
        folder = f'{object._contribution.id}_{object.paper.title}'

    folder = secure_filename(folder, '')
    filename = build_filename(object)
    return str(Path() / prefix / folder / filename)


def build_filename(file):
    if isinstance(file, RegistrationData):
        id = f'{file.registration_id}_{file.field_data_id}'
    else:
        id = file.id

    filename = secure_filename(Path(file.filename).stem, '')
    return f'{id}_{filename}.{file.extension}'


@email_sender
def notify_data_export_success(export_request):
    """Send an email to the user when a data export is completed"""
    with export_request.user.force_user_locale():
        template = get_template_module('users/emails/data_export_success.txt',
                                       user=export_request.user, link=export_request.url)
        return make_email({export_request.user.email}, template=template, html=False)


@email_sender
def notify_data_export_failure(export_request):
    """Send an email to the user when a data export has failed"""
    with export_request.user.force_user_locale():
        user = export_request.user
        template = get_template_module('users/emails/data_export_failure.txt', user=user,
                                       link=url_for('users.user_data_export', user, _external=True))
        return make_email({export_request.user.email}, template=template, html=False)


@celery.periodic_task(name='user_data_export_cleanup', run_every=crontab(hour='4', day_of_week='monday'))
def user_data_export_cleanup(days=30):
    """Clean up old user data exports.

    :param days: number of days after which to remove the data exports
    """
    old_requests = _get_old_requests(days)

    logger.info('Removing %d expired user data exports from the past %d days', len(old_requests), days)
    for request in old_requests:
        request.state = DataExportRequestState.expired
        if not request.file:
            continue
        try:
            request.file.delete()
        except StorageError as exc:
            logger.warning('Could not delete user data export %r: %s', request, exc)
        else:
            logger.info('Removed user data export %r', request)
        finally:
            # This will automatically delete the File object associated with the request
            request.file = None
    db.session.commit()


def _get_old_requests(days):
    return (DataExportRequest.query
            .filter(DataExportRequest.requested_dt < (now_utc() - timedelta(days=days)),
                    DataExportRequest.state == DataExportRequestState.success)
            .all())
