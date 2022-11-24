# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from operator import attrgetter

from flask import render_template
from markupsafe import Markup, escape

from indico.core import signals
from indico.util.decorators import classproperty
from indico.util.signals import named_objects_from_signal


class Placeholder:
    """Base class for placeholders.

    Placeholders allow you to insert data in texts provided by users
    while remaining flexible when it comes to HTML escaping and making
    placeholders required or optional.
    """

    #: The name of the placeholder. Must be unique within the context
    #: where the placeholder is used
    name = None
    #: Whether the placeholder must be used at least once.
    required = False
    #: A short description of the placeholder.
    description = None
    #: Whether the placeholder should not be shown by default
    advanced = False

    @classproperty
    @classmethod
    def friendly_name(cls):
        return '{%s}' % cls.name

    @classmethod
    def get_regex(cls, **kwargs):
        return re.compile(r'\{%s}' % re.escape(cls.name))

    @classmethod
    def replace(cls, text, escape_html=True, **kwargs):
        """Replace all occurrences of the placeholder in a string.

        :param text: The text to replace placeholders in
        :param escape_html: whether HTML escaping should be done
        :param kwargs: arguments specific to the placeholder's context
        """
        rendered = []

        def _replace(m):
            if rendered:
                return rendered[0]
            rendered.append(cls.render(**kwargs))
            if escape_html:
                rendered[0] = escape(rendered[0])
            return rendered[0]

        return cls.get_regex(**kwargs).sub(_replace, text)

    @classmethod
    def is_in(cls, text, **kwargs):
        """Check whether the placeholder is used in a string."""
        return cls.get_regex(**kwargs).search(text) is not None

    @classmethod
    def is_empty(cls, text, **kwargs):
        """Check whether the placeholder renders an empty string.

        :param text: The text to replace placeholders in
        :param kwargs: arguments specific to the placeholder's context
        """
        empty = [False]

        def _replace(m):
            if not cls.render(**kwargs):
                empty[0] = True
            return ''

        cls.get_regex(**kwargs).sub(_replace, text)
        return empty[0]

    @classmethod
    def render(cls, **kwargs):
        """Convert the placeholder to a string.

        When a placeholder contains HTML that should not be escaped,
        the returned value should be returned as a
        :class:`markupsafe.Markup` instance instead of a plain string.

        Subclasses are encouraged to explicitly specify the arguments
        they expect instead of using ``**kwargs``.

        :param kwargs: arguments specific to the placeholder's context
        """
        raise NotImplementedError

    @classmethod
    def serialize(cls, **kwargs):
        return {
            'name': cls.name,
            'required': cls.required,
            'description': cls.description,
            'advanced': cls.advanced,
            'parametrized': False,
        }


class ParametrizedPlaceholder(Placeholder):
    """Base class for placeholders that can take an argument.

    Such placeholders are used like this: ``{something:arg}`` with
    ``:arg`` being optional; if omitted the argument will be ``None``.

    If you use `iter_param_info` to show parameter-specific
    descriptions and do not want a generic info line (with just the
    `param_friendly_name` in place of an actual param), set the
    `description` of the placeholder to ``None``.
    """

    #: Whether the param is required
    param_required = False
    #: The human-friendly name of the param
    param_friendly_name = 'param'
    #: Whether only params defined in ``iter_param_info`` are allowed
    param_restricted = False

    @classproperty
    @classmethod
    def friendly_name(cls):
        fmt = '{%s:%s}' if cls.param_required else '{%s[:%s]}'
        return fmt % (cls.name, cls.param_friendly_name)

    @classmethod
    def get_regex(cls, **kwargs):
        param_regex = ('|'.join(re.escape(x[0]) for x in cls.iter_param_info(**kwargs) if x[0] is not None)
                       if cls.param_restricted else '[^}]+')
        regex = r'\{%s:(%s)}' if cls.param_required else r'\{%s(?::(%s))?}'
        return re.compile(regex % (re.escape(cls.name), param_regex))

    @classmethod
    def iter_param_info(cls, **kwargs):
        """Yield information for known params.

        Each item yielded must be a ``(value, description)`` tuple.

        :param kwargs: arguments specific to the placeholder's context
        """
        return iter([])

    @classmethod
    def replace(cls, text, escape_html=True, **kwargs):
        def _replace(m):
            rendered_text = cls.render(m.group(1), **kwargs)
            if escape_html:
                rendered_text = escape(rendered_text)
            return rendered_text

        return cls.get_regex(**kwargs).sub(_replace, text)

    @classmethod
    def is_empty(cls, text, **kwargs):
        """Check whether the placeholder renders an empty string.

        :param text: The text to replace placeholders in
        :param kwargs: arguments specific to the placeholder's context
        """
        empty = [False]

        def _replace(m):
            if not cls.render(m.group(1), **kwargs):
                empty[0] = True
            return ''

        cls.get_regex(**kwargs).sub(_replace, text)
        return empty[0]

    @classmethod
    def render(cls, param, **kwargs):
        raise NotImplementedError

    @classmethod
    def serialize(cls, **kwargs):
        params = [{'param': param, 'description': description}
                  for param, description in cls.iter_param_info(**kwargs)]
        return dict(super().serialize(), parametrized=True, params=params)


def get_placeholders(context, **kwargs):
    return named_objects_from_signal(signals.core.get_placeholders.send(context, **kwargs))


def get_sorted_placeholders(context, **kwargs):
    return sorted(list(get_placeholders(context, **kwargs).values()), key=attrgetter('name'))


def replace_placeholders(context, text, escape_html=True, **kwargs):
    """Replace placeholders in a string.

    :param context: the context where the placeholders are used
    :param text: the text to replace placeholders in
    :param escape_html: whether HTML escaping should be done
    :param kwargs: arguments specific to the context
    """
    for placeholder in get_placeholders(context, **kwargs).values():
        text = placeholder.replace(text, escape_html=escape_html, **kwargs)
    return text


def get_empty_placeholders(context, text, **kwargs):
    """Get a list of placeholders that evaluate to an empty string.

    :param context: the context where the placeholders are used
    :param text: the text containing some placeholders
    :param kwargs: arguments specific to the context
    """
    return {
        placeholder.friendly_name
        for placeholder in get_placeholders(context, **kwargs).values()
        if placeholder.is_in(text, **kwargs) and placeholder.is_empty(text, **kwargs)
    }


def get_missing_placeholders(context, text, **kwargs):
    """Get the set of missing required placeholders.

    :param context: the context where the placeholders are used
    :param text: the text to check
    :param kwargs: arguments specific to the context
    """
    placeholders = {p for p in get_placeholders(context, **kwargs).values() if p.required}
    return {p.friendly_name for p in placeholders if not p.is_in(text, **kwargs)}


def render_placeholder_info(context, **kwargs):
    """Render the list of available placeholders.

    :param context: the context where the placeholders are used
    :param kwargs: arguments specific to the context
    """
    return Markup(render_template('placeholder_info.html', placeholder_kwargs=kwargs,
                                  placeholders=get_sorted_placeholders(context, **kwargs),
                                  ParametrizedPlaceholder=ParametrizedPlaceholder))
