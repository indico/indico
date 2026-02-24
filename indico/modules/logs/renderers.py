# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import render_template

from indico.modules.logs.util import render_changes


class EventLogRendererBase:
    """Base class for event log renderers."""

    #: unique name of the log renderer (matches EventLogEntry.type)
    name = None
    #: plugin containing this renderer - assigned automatically
    plugin = None
    #: template used to render the log entry
    template_name = None
    #: extra kwargs passed to `render_template`
    template_kwargs = {}

    @classmethod
    def render_entry(cls, entry):
        """Render the log entry row.

        :param entry: A :class:`.EventLogEntry`
        """
        template = f'{cls.plugin.name}:{cls.template_name}' if cls.plugin is not None else cls.template_name
        return render_template(template, entry=entry, data=cls.get_data(entry), **cls.template_kwargs)

    @classmethod
    def get_data(cls, entry):
        """Return the entry data in a format suitable for the template.

        This method may be overridden if the entry's data needs to be
        preprocessed before being passed to the template.

        It MUST NOT modify `entry.data` directly.
        """
        return entry.data


class SimpleRenderer(EventLogRendererBase):
    name = 'simple'
    template_name = 'logs/entry_simple.html'
    template_kwargs = {'compare': render_changes}

    @classmethod
    def get_data(cls, entry):
        data = entry.data
        if isinstance(entry.data, dict):
            data = dict(sorted(entry.data.items()))
        return data


class EmailRenderer(EventLogRendererBase):
    name = 'email'
    template_name = 'logs/entry_email.html'

    @classmethod
    def get_data(cls, entry):
        data = dict(entry.data)
        stored_attachments = data.get('stored_attachments') or []
        if data.get('content_type') != 'text/html' or not stored_attachments:
            return data

        replacements = {
            att.get('content_id'): entry.get_email_attachment_url(idx)
            for idx, att in enumerate(stored_attachments)
            if att.get('content_id')
        }
        if not replacements:
            return data

        body = data.get('body', '')
        for content_id, url in replacements.items():
            body = body.replace(f'cid:{content_id}', url)
        data['body'] = body
        return data
