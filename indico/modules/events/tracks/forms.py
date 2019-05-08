# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import StringField
from wtforms.validators import DataRequired

from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.modules.events.sessions.models.sessions import Session
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import IndicoMarkdownField


class TrackForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()])
    code = StringField(_('Code'))
    default_session = QuerySelectField(_('Default session'), default='', allow_blank=True, get_label='title',
                                       description=_('Indico will preselect this session whenever an abstract is '
                                                     'accepted for the track'))
    description = IndicoMarkdownField(_('Description'), editor=True)

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(TrackForm, self).__init__(*args, **kwargs)
        self.default_session.query = Session.query.with_parent(event)


class ProgramForm(IndicoForm):
    program = IndicoMarkdownField(_('Programme'), editor=True, mathjax=True)

    @generated_data
    def program_render_mode(self):
        return RenderMode.markdown
