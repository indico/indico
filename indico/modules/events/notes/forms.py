# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms.fields import TextAreaField

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import CKEditorWidget


class NoteForm(IndicoForm):
    # TODO: use something switchable
    source = TextAreaField(_('Minutes'), widget=CKEditorWidget(images=True))

    def __init__(self, *args, ckeditor_upload_url, **kwargs):
        self.ckeditor_upload_url = ckeditor_upload_url
        super().__init__(*args, **kwargs)
