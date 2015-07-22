# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import re

from wtforms.widgets import TextInput, TextArea
from wtforms.widgets.core import HTMLString

from indico.core.auth import multipass
from indico.web.util import inject_js
from indico.web.flask.templating import get_template_module

html_commment_re = re.compile(r'<!--.*?-->', re.MULTILINE)


class ConcatWidget(object):
    """Renders a list of fields as a simple string joined by an optional separator."""
    def __init__(self, separator='', prefix_label=True):
        self.separator = separator
        self.prefix_label = prefix_label

    def __call__(self, field, label_args=None, field_args=None, **kwargs):
        label_args = label_args or {}
        field_args = field_args or {}
        html = []
        for subfield in field:
            fmt = u'{0} {1}' if self.prefix_label else u'{1} {0}'
            html.append(fmt.format(subfield.label(**label_args), subfield(**field_args)))
        return HTMLString(self.separator.join(html))


class JinjaWidget(object):
    """Renders a field using a custom Jinja template

    :param template: The template to render
    :param plugin: The plugin or plugin name containing the template
    :param single_line: If the field should be rendered in single-line
                        style.
    :param single_kwargs: If kwargs should be passed to the template as
                          ``input_args`` instead of being passed as
                          separate kwargs.
    """

    def __init__(self, template, plugin=None, single_line=False, single_kwargs=False, **context):
        self.template = template
        self.plugin = plugin
        self.context = context
        self.single_line = single_line
        self.single_kwargs = single_kwargs

    def __call__(self, field, **kwargs):
        if self.plugin:
            plugin = self.plugin
            if hasattr(plugin, 'name'):
                plugin = plugin.name
            template = '{}:{}'.format(plugin, self.template)
        else:
            template = self.template
        if self.single_kwargs:
            kwargs = {'input_args': kwargs}
        template_module = get_template_module(template, field=field, **dict(self.context, **kwargs))
        javascript = template_module.javascript()
        if '<script' in javascript:
            inject_js(template_module.javascript())
        elif html_commment_re.sub('', javascript).strip():
            raise ValueError("Template did not provide valid javascript")
        return HTMLString(template_module.html())


class PasswordWidget(JinjaWidget):
    """Renders a password input"""

    single_line = True

    def __init__(self):
        super(PasswordWidget, self).__init__('forms/password_widget.html')

    def __call__(self, field, **kwargs):
        return super(PasswordWidget, self).__call__(field, input_args=kwargs)


class CKEditorWidget(JinjaWidget):
    """Renders a CKEditor WYSIWYG editor"""
    def __init__(self, simple=False):
        super(CKEditorWidget, self).__init__('forms/ckeditor_widget.html', simple=simple)


class SwitchWidget(JinjaWidget):
    """Renders a switch widget

    :param on_label: Text to override default ON label
    :param off_label: Text to override default OFF label
    """

    def __init__(self, on_label=None, off_label=None):
        super(SwitchWidget, self).__init__('forms/switch_widget.html')
        self.on_label = on_label
        self.off_label = off_label

    def __call__(self, field, **kwargs):
        kwargs.update({
            'checked': getattr(field, 'checked', field.data),
            'on_label': self.on_label,
            'off_label': self.off_label
        })
        return super(SwitchWidget, self).__call__(field, kwargs=kwargs)


class SyncedInputWidget(JinjaWidget):
    """Renders a text input with a sync button when needed."""

    def __init__(self, textarea=False):
        super(SyncedInputWidget, self).__init__('forms/synced_input_widget.html', single_line=not textarea)
        self.textarea = textarea
        self.default_widget = TextArea() if textarea else TextInput()

    def __call__(self, field, **kwargs):
        # Render a sync button for fields which can be synced, if the identity provider provides a value for the field.
        if field.short_name in multipass.synced_fields and field.synced_value is not None:
            return super(SyncedInputWidget, self).__call__(field, textarea=self.textarea, kwargs=kwargs)
        else:
            return self.default_widget(field, **kwargs)


class TypeaheadWidget(JinjaWidget):
    """Renders a selectizer-based widget"""

    def __init__(self, typeahead_options=None, min_trigger_length=0):
        super(TypeaheadWidget, self).__init__('forms/typeahead_widget.html')
        self.typeahead_options = typeahead_options or {}
        self.min_trigger_length = min_trigger_length

    def __call__(self, field, **kwargs):
        choices = []

        if hasattr(field, 'choices'):
            choices.extend(field.choices)

        options = {
            'hint': True,
            'searchOnFocus': True,
            'display': 'name',
            'mustSelectItem': True,
            'source': {
                'data': choices
            }
        }

        options.update(kwargs.pop('options', {}))
        options.update(self.typeahead_options)
        return super(TypeaheadWidget, self).__call__(field, options=options)
