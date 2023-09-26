# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4
from zipfile import ZipFile

import yaml
from sqlalchemy.orm import joinedload

from indico.core.config import config
from indico.core.db import db
from indico.core.notifications import email_sender, make_email
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.models.revisions import EditingRevision
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.revisions import PaperRevision
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.files.models.files import File
from indico.modules.users import logger
from indico.modules.users.models.export import DataExportOptions, DataExportRequest, DataExportRequestState
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for


def export_user_data(user, options):
    """Generate a zip file containing user data and files and save it in `user.data_export_request`."""
    export_request = user.data_export_request
    if export_request and export_request.is_running:
        return

    try:
        export_request = initialize_new_request(user, options)
        data = serialize_user_data(export_request)
        files = get_user_files(export_request)
        file, max_size_exceeded = generate_zip(user, data, files, config.MAX_DATA_EXPORT_SIZE * 1024**2)
    except Exception as e:
        logger.exception('Could not create a user data export %r: %r', export_request, e)
        export_request.fail()
        db.session.commit()
        notify_data_export_failure(export_request)
    else:
        export_request.succeed(file)
        if max_size_exceeded:
            export_request.max_size_exceeded = True
            logger.warning('User data export exceeded size limit, exporting only partial data: %r', export_request)
        db.session.commit()
        notify_data_export_success(export_request)


def initialize_new_request(user, options):
    if user.data_export_request:
        user.data_export_request.delete()
        db.session.commit()
    DataExportRequest(user=user, selected_options=options, state=DataExportRequestState.running)
    db.session.commit()
    return user.data_export_request


def generate_zip(user, data, files, max_size):
    temp_file = NamedTemporaryFile(suffix='.zip', dir=config.TEMP_DIR, delete=False)
    try:
        return _generate_zip(user, data, files, max_size, temp_file)
    finally:
        Path(temp_file.name).unlink(missing_ok=True)


def _generate_zip(user, data, files, max_size, temp_file):
    max_size_exceeded = False
    with ZipFile(temp_file, 'w', allowZip64=True) as zip_file:
        for key, subdata in data.items():
            zip_file.writestr(f'{key}.yaml', convert_to_yaml(subdata))

        written = 0
        for file in files:
            written += getattr(file, 'file', file).size
            if written <= max_size:
                write_file(zip_file, file)
            else:
                max_size_exceeded = True
                break

    temp_file.seek(0)
    file = File(filename='data-export.zip', content_type='application/zip')
    file.save(('user', user.id), temp_file)
    file.claim()
    return file, max_size_exceeded


def serialize_user_data(export_request):
    from indico.modules.users.export_schemas import UserDataExportSchema

    user = export_request.user
    fields = options_to_fields(export_request.selected_options)
    return UserDataExportSchema(only=fields).dump(user)


def options_to_fields(options):
    options_map = {
        DataExportOptions.contribs: ('contributions', 'subcontributions'),
        DataExportOptions.abstracts_papers: ('abstracts', 'papers'),
        DataExportOptions.misc: ('miscellaneous',),
    }
    fields = []
    for opt in options:
        fields += options_map.get(opt, (opt.name,))
    return fields


def write_file(zip_file, file):
    path = build_storage_path(file)
    file = getattr(file, 'file', file)
    with file.open() as f:
        zip_file.writestr(path, f.read())


def get_user_files(export_request):
    """Get all files tied to a given user."""
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
            yield from dedup_editable_files(editable)

    if DataExportOptions.registrations in options:
        yield from get_registration_files(user)


def get_registration_files(user):
    """Get all files uploaded in registration file fields."""
    return (RegistrationData.query
            .join(Registration)
            .filter(Registration.user == user,
                    RegistrationData.filename.isnot(None))
            .all())


def get_attachments(user):
    """Get all attachments uploaded by the user."""
    return Attachment.query.filter(Attachment.user == user, Attachment.type == AttachmentType.file).all()


def get_contributions(user):
    """Get all contributions linked to the user (author, speaker or submitter)."""
    return (Contribution.query.options(joinedload('person_links'))
            .filter(Contribution.person_links.any(ContributionPersonLink.person.has(user=user)))
            .all())


def get_subcontributions(user):
    """Get all subcontributions linked to the user (speaker)."""
    return (SubContribution.query
            .options(joinedload('person_links'))
            .filter(SubContribution.person_links.any(SubContributionPersonLink.person.has(user=user)))
            .all())


def get_abstracts(user):
    """Get all abstracts where the user is either the submitter or is linked to the abstract."""
    return (Abstract.query.options(joinedload('person_links'))
            .filter(db.or_(Abstract.submitter == user,
                           Abstract.person_links.any(AbstractPersonLink.person.has(user=user))))
            .all())


def get_papers(user):
    """Get all papers where the user is either linked to the parent contribution or has submitted a paper revision."""
    contribs = (Contribution.query.options(joinedload('person_links'))
                .filter(db.or_(db.and_(Contribution.person_links.any(ContributionPersonLink.person.has(user=user)),
                                       Contribution._paper_revisions.any()),
                               Contribution._paper_revisions.any(PaperRevision.submitter == user)))
                .all())
    return [contrib.paper for contrib in contribs]


def get_editables(user):
    """
    Get all editables where the user is either linked to the parent contribution or has submitted an editing revision.
    """
    return (Editable.query
            .join(Contribution, Contribution.id == Editable.contribution_id)
            .outerjoin(ContributionPersonLink, ContributionPersonLink.contribution_id == Contribution.id)
            .outerjoin(EditingRevision, EditingRevision.editable_id == Editable.id)
            .filter(db.or_(Contribution.person_links.any(ContributionPersonLink.person.has(user=user)),
                           EditingRevision.user == user))
            .all())


def dedup_editable_files(editable):
    """Return a deduplicated list of editable files.

    When a file is not changed between revisions, multiple revisions might refer to
    the same physical file. We don't want to include duplicate files in the export.
    """
    files = {file.file_id: file for revision in editable.revisions for file in revision.files}
    return files.values()


def build_storage_path(file):
    """Build a path under which a given file be stored in the exported zip file.

    The path includes both the id (to ensure uniqueness) and the title/name for
    easy navigation.
    """
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


def convert_to_yaml(data):
    """Convert data to yaml with a nicer indentation style.

    Normal output does not indent lists, e.g.:
        key:
        - 1
        - 2

    Using this function, the list becomes indented:
        key:
          - 1
          - 2

    See: https://github.com/yaml/pyyaml/issues/234
    """
    class Dumper(yaml.Dumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, indentless=False)

    return yaml.dump(data, Dumper=Dumper, allow_unicode=True)


def get_old_requests(days):
    """Get successful export requests older than the specified number of days."""
    return (DataExportRequest.query
            .filter(DataExportRequest.requested_dt < (now_utc() - timedelta(days=days)),
                    DataExportRequest.state == DataExportRequestState.success)
            .all())


@email_sender
def notify_data_export_success(export_request):
    """Send an email to a user when a data export has finished."""
    with export_request.user.force_user_locale():
        template = get_template_module('users/emails/data_export_success.txt',
                                       user=export_request.user, link=export_request.url,
                                       max_size_exceeded=export_request.max_size_exceeded)
        return make_email({export_request.user.email}, template=template, html=False)


@email_sender
def notify_data_export_failure(export_request):
    """Send an email to a user when a data export has failed."""
    with export_request.user.force_user_locale():
        user = export_request.user
        template = get_template_module('users/emails/data_export_failure.txt', user=user,
                                       link=url_for('users.user_data_export', user, _external=True))
        return make_email({export_request.user.email}, template=template, html=False)
