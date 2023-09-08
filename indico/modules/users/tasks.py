# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from contextlib import suppress
from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4
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
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.modules.files.models.files import File
from indico.modules.users import logger
from indico.modules.users.export import get_abstracts, get_attachments, get_editables, get_papers, get_registration_data
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

    # If an export request already exists we delete it
    # along with the actual file (if any) and create a new request
    if export_request:
        f = export_request.file
        db.session.delete(export_request)
        if f:
            with suppress(Exception):
                f.delete(delete_from_db=True)
        db.session.commit()
    export_request = DataExportRequest(user=user, selected_options=options, state=DataExportRequestState.running)
    db.session.commit()

    temp_file = NamedTemporaryFile(suffix='.zip', dir=config.TEMP_DIR, delete=False)
    try:
        _export_user_data(export_request, temp_file)
    except Exception:
        logger.exception('Could not create a user data export %r', export_request)
        export_request.fail()
        db.session.commit()
        notify_data_export_failure(export_request)
    finally:
        Path(temp_file.name).unlink(missing_ok=True)


def _export_user_data(export_request, buffer):
    generate_zip(export_request, buffer, config.MAX_DATA_EXPORT_SIZE * 1024**2)
    buffer.seek(0)

    file = File(filename='data-export.zip', content_type='application/zip')
    try:
        file.save(('user', export_request.user.id), buffer)
        file.claim()
        export_request.succeed(file)
        db.session.commit()
    except Exception as exc:
        with suppress(Exception):
            file.delete()
        raise exc
    else:
        notify_data_export_success(export_request)


@celery.task(name='export_user_data')
def export_user_data_task(user, options):
    export_user_data(user, options)


def get_data(export_request):
    from indico.modules.users.export_schemas import UserDataExportSchema

    user = export_request.user
    options = export_request.selected_options

    options_map = {
        DataExportOptions.contribs: ('contributions', 'subcontributions'),
        DataExportOptions.abstracts_papers: ('abstracts', 'papers'),
        DataExportOptions.misc: ('miscellaneous',),
    }
    fields = []
    for opt in options:
        fields += options_map.get(opt, (opt.name,))
    return UserDataExportSchema(only=fields).dump(user)


def generate_zip(export_request, temp_file, max_size):
    data = get_data(export_request)
    with ZipFile(temp_file, 'w', allowZip64=True) as zip_file:
        for key, subdata in data.items():
            zip_file.writestr(f'{key}.yaml', yaml.dump(subdata, allow_unicode=True))
        size = 0
        for file in collect_files(export_request):
            size += getattr(file, 'file', file).size
            if size <= max_size:
                write_file(zip_file, file)
            else:
                export_request.max_size_exceeded = True
                logger.warning('User data export exceeds size limit, exporting only partial data: %r',
                               export_request)
                break


def collect_files(export_request):
    user = export_request.user
    options = export_request.selected_options

    if DataExportOptions.attachments in options:
        for attachment in get_attachments(user):
            yield attachment.file

    if DataExportOptions.abstracts_papers in options:
        for abstract in get_abstracts(user):
            yield from abstract.files

        for paper in get_papers(user):
            yield from paper.files

    if DataExportOptions.editables in options:
        for editable in get_editables(user):
            for revision in editable.revisions:
                yield from revision.files

    if DataExportOptions.registrations in options:
        yield from get_registration_data(user)


def write_file(zip_file, file):
    path = build_storage_path(file)
    file = getattr(file, 'file', file)
    with file.open() as f:
        zip_file.writestr(path, f.read())


def build_storage_path(file):
    if isinstance(file, RegistrationData):
        event = file.registration.event
        prefix = 'registrations'
        path = f'{event.id}_{event.title}'
    elif isinstance(file, AttachmentFile):
        prefix = 'attachments'
        path = ''
    elif isinstance(file, AbstractFile):
        event = file.abstract.event
        prefix = 'abstracts'
        path = f'{event.id}_{event.title}/{file.abstract.id}_{file.abstract.title}'
    elif isinstance(file, PaperFile):
        event = file._contribution.event
        prefix = 'papers'
        path = f'{event.id}_{event.title}/{file._contribution.id}_{file.paper.title}'
    else:
        editable = file.revision.editable
        event = editable.contribution.event
        prefix = f'editables/{editable.type.name}'
        path = f'{event.id}_{event.title}/{editable.id}_{editable.contribution.title}'

    path = secure_path(path)
    filename = build_filename(file)
    return str(Path() / prefix / path / filename)


def build_filename(file):
    file = getattr(file, 'file', file)
    if isinstance(file, RegistrationData):
        id = f'{file.registration_id}_{file.field_data_id}'
    else:
        id = file.id

    filename = secure_filename(Path(file.filename).stem, '')
    return f'{id}_{filename}.{file.extension}'


def secure_path(path):
    parts = (secure_filename(p, uuid4()) for p in Path(path).parts)
    return Path(*parts)


@email_sender
def notify_data_export_success(export_request):
    """Send an email to the user when a data export is completed"""
    with export_request.user.force_user_locale():
        template = get_template_module('users/emails/data_export_success.txt',
                                       user=export_request.user, link=export_request.url,
                                       max_size_exceeded=export_request.max_size_exceeded)
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
