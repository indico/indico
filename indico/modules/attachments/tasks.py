# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from indico.core.celery import celery
from indico.core.config import config
from indico.core.db import db
from indico.modules.attachments.models.attachments import Attachment
from indico.modules.files.models.files import File


@celery.task(ignore_result=False)
def generate_materials_package(attachment_ids, event):
    from indico.modules.attachments.controllers.event_package import AttachmentPackageGeneratorMixin
    attachments = Attachment.query.filter(Attachment.id.in_(attachment_ids)).all()
    attachment_package_mixin = AttachmentPackageGeneratorMixin()
    attachment_package_mixin.event = event
    generated_zip = attachment_package_mixin._generate_zip_file(attachments, return_file=True)
    f = File(filename='material-package.zip', content_type='application/zip', meta={'event_id': event.id})
    context = ('event', event.id, 'attachment-package')
    f.save(context, generated_zip, backend=config.STATIC_SITE_STORAGE)
    db.session.add(f)
    db.session.commit()
    os.unlink(generated_zip.name)
    return f.signed_download_url
