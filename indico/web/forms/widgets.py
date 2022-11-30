# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from markupsafe import Markup
from wtforms.widgets import CheckboxInput, HiddenInput

from indico.core.config import config
from indico.core.db import db
from indico.util.string import natural_sort_key
from indico.web.flask.templating import get_template_module
from indico.web.util import inject_js


html_comment_re = re.compile(r'<!--.*?-->', re.MULTILINE)


class ConcatWidget:
    """Render a list of fields as a simple string joined by an optional separator."""

    def __init__(self, separator='', prefix_label=True):
        self.separator = separator
        self.prefix_label = prefix_label

    def __call__(self, field, label_args=None, field_args=None, **kwargs):
        label_args = label_args or {}
        field_args = field_args or {}
        html = []
        for subfield in field:
            fmt = '{0} {1}' if self.prefix_label else '{1} {0}'
            html.append(fmt.format(subfield.label(**label_args), subfield(**field_args)))
        return Markup(self.separator.join(html))


class HiddenInputs(HiddenInput):
    """Render hidden inputs for list elements."""

    item_widget = HiddenInput()

    def __call__(self, field, **kwargs):
        items = field._value() or []
        return Markup('\n'.join(self.item_widget(field, value=item) for item in items))


class HiddenCheckbox(CheckboxInput, HiddenInput):
    """Render an invisible checkbox.

    This widget also inherits from HiddenInput to avoid creating
    a form row when rendering the form containing it.
    """

    def __call__(self, field, **kwargs):
        kwargs['style'] = 'display: none;'
        return super().__call__(field, **kwargs)


class JinjaWidget:
    """Render a field using a custom Jinja template

    :param template: The template to render
    :param plugin: The plugin or plugin name containing the template
    :param single_line: If the field should be rendered in single-line
                        style.
    :param single_kwargs: If kwargs should be passed to the template as
                          ``input_args`` instead of being passed as
                          separate kwargs.
    """

    def __init__(self, template, plugin=None, single_line=False, single_kwargs=False, inline_js=False, **context):
        self.template = template
        self.plugin = plugin
        self.context = context
        self.single_line = single_line
        self.single_kwargs = single_kwargs
        self.inline_js = inline_js

    def __call__(self, field, **kwargs):
        if self.plugin:
            plugin = self.plugin
            if hasattr(plugin, 'name'):
                plugin = plugin.name
            template = f'{plugin}:{self.template}'
        else:
            template = self.template
        if self.single_kwargs:
            kwargs = {'input_args': kwargs}
        template_module = get_template_module(template, field=field, **(self.context | kwargs))
        javascript = template_module.javascript()
        html = template_module.html()
        if self.inline_js:
            html += '\n' + javascript
        elif '<script' in javascript:
            inject_js(template_module.javascript())
        elif html_comment_re.sub('', javascript).strip():
            raise ValueError('Template did not provide valid javascript')
        return Markup(html)


class PasswordWidget(JinjaWidget):
    """Render a password input."""

    def __init__(self):
        super().__init__('forms/password_widget.html', single_line=True)

    def __call__(self, field, **kwargs):
        return super().__call__(field, input_args=kwargs)


class CKEditorWidget(JinjaWidget):
    """Render a CKEditor WYSIWYG editor.

    :param images: Whether to allow images.
    :param html_embed: Whether to enable raw HTML embedding.
    :param height: The height of the editor.

    If the form has a ``ckeditor_upload_url`` attribute and images are enabled,
    the editor will allow pasting/selecting images and upload them using that URL.
    """

    def __init__(self, *, images=False, html_embed=False, height=475):
        super().__init__('forms/ckeditor_widget.html', images=images, html_embed=html_embed, height=height)


class SwitchWidget(JinjaWidget):
    """Render a switch widget.

    :param confirm_enable: Text to prompt when enabling the switch
    :param confirm_disable: Text to prompt when disabling the switch
    """

    def __init__(self, confirm_enable=None, confirm_disable=None):
        super().__init__('forms/switch_widget.html')
        self.confirm_enable = confirm_enable
        self.confirm_disable = confirm_disable

    def __call__(self, field, **kwargs):
        kwargs.update({
            'checked': getattr(field, 'checked', field.data)
        })
        return super().__call__(field, kwargs=kwargs, confirm_enable=self.confirm_enable,
                                confirm_disable=self.confirm_disable)


class RemoteDropdownWidget(JinjaWidget):
    """Render a SUI Dropdown which can dynamically fetch results.

    :param search_url: The URL used to retrieve items.
    :param search_method: The method used to retrieve items.
    :param min_trigger_length: Number of characters needed to start
                               searching for suggestions.
    :param allow_by_id: Whether to allow `#123` searches regardless of
                        the trigger length.  Such searches will be sent
                        as 'id' instead of 'q' in the AJAX request.
    :param preload: Whether to load all choices with a single AJAX
                    request instead of sending requests when searching.
    :param value_field: The attribute of the response used as the
                        field value.
    :param label_field: The attribute of the response used as the
                        item label.
    :param search_field: The attribute of the response used to search
                         in locally available data.
    """

    def __init__(self, search_url=None, search_method='GET', min_trigger_length=3, allow_by_id=False, preload=False,
                 value_field='id', label_field='name', search_field='name', inline_js=False):
        self.min_trigger_length = min_trigger_length
        self.allow_by_id = allow_by_id
        self.preload = preload
        self.search_url = search_url
        self.search_method = search_method
        self.value_field = value_field
        self.label_field = label_field
        self.search_field = search_field
        super().__init__('forms/sui_remote_search_dropdown_widget.html', inline_js=inline_js)

    def __call__(self, field, **kwargs):
        return super().__call__(field,
                                search_url=getattr(field, 'search_url', self.search_url),
                                search_method=self.search_method,
                                search_payload=getattr(field, 'search_payload', None),
                                min_trigger_length=self.min_trigger_length, preload=self.preload,
                                allow_by_id=self.allow_by_id, value_field=self.value_field,
                                label_field=self.label_field, search_field=self.search_field, input_args=kwargs)


class TypeaheadWidget(JinjaWidget):
    """Render a text field enhanced with jquery-typeahead.

    :param search_url: The URL used to retrieve AJAX-based suggestions.
    :param min_trigger_length: Number of characters needed to start
                               searching for suggestions.
    :param typeahead_options: Params passed to the typeahead js
                              initialization.
    :param choices: Choices passed to the typeahead js initialization.
    """

    def __init__(self, search_url=None, min_trigger_length=1, typeahead_options=None, choices=None):
        super().__init__('forms/typeahead_widget.html')
        self.search_url = search_url
        self.min_trigger_length = min_trigger_length
        self.typeahead_options = typeahead_options
        self.choices = choices

    def __call__(self, field, **kwargs):
        options = {}
        if self.typeahead_options:
            options.update(self.typeahead_options)
        options.update(kwargs.pop('options', {}))
        choices = self.choices if self.choices is not None else getattr(field, 'choices', [])
        return super().__call__(field, options=options, min_trigger_length=self.min_trigger_length,
                                search_url=self.search_url, choices=choices, input_args=kwargs)


class LocationWidget(JinjaWidget):
    """Render a collection of fields to represent location."""

    def __init__(self):
        super().__init__('forms/location_widget.html', single_line=True)

    def __call__(self, field, **kwargs):
        rooms = {'data': []}
        venues = {'data': []}
        venue_map = {}
        if config.ENABLE_ROOMBOOKING and field.locations:
            rooms = {loc.name: {'data': self.get_sorted_rooms(loc)} for loc in field.locations}
            venues = {'data': [{'id': loc.id, 'name': loc.name} for loc in field.locations]}
            venue_map = {loc['id']: loc['name'] for loc in venues['data']}
        parent = (self._get_parent_info(field.object_data['source'], field.object_data['inheriting'])
                  if field.object_data and field.object_data.get('source') and field.allow_location_inheritance
                  else ('', ''))
        return super().__call__(field, rooms=rooms, venues=venues, parent=parent,
                                source=field.object_data.get('source'), venue_map=venue_map,
                                init_inheritance=field.object_data.get('inheriting'))

    def _get_parent_info(self, obj, inheriting):
        parent = obj.location_parent if not inheriting else obj
        if isinstance(parent, db.m.Contribution):
            return 'Contribution', parent.title
        elif isinstance(parent, db.m.Break):
            return 'Break', parent.title
        elif isinstance(parent, db.m.SessionBlock):
            return 'Block', parent.title
        elif isinstance(parent, db.m.Session):
            return 'Session', parent.title
        elif isinstance(parent, db.m.Event):
            return 'Event', parent.title
        else:
            raise TypeError(f'Unexpected parent type {type(parent)}')

    def get_sorted_rooms(self, location):
        result = [{'name': room.full_name, 'id': room.id, 'venue_id': room.location_id}
                  for room in location.rooms]
        return sorted(result, key=lambda x: natural_sort_key(x['name']))


class ColorPickerWidget(JinjaWidget):
    """Render a colorpicker input field."""

    def __init__(self, show_field=True):
        super().__init__('forms/color_picker_widget.html', single_line=True, show_field=show_field)

    def __call__(self, field, **kwargs):
        return super().__call__(field, input_args=kwargs)


class PrefixedTextWidget(JinjaWidget):
    """Render a TextInput with a prefix"""

    def __init__(self, prefix=None, show_field=True):
        super().__init__('forms/prefixed_text_widget.html', single_line=True, single_kwargs=True,
                         show_field=show_field, prefix=prefix)
