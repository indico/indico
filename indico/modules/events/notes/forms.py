# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import TextAreaField

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import CKEditorWidget


class NoteForm(IndicoForm):
    # TODO: use something switchable
    source = TextAreaField(_("Minutes"), widget=CKEditorWidget())
