# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from enum import Enum

from markupsafe import Markup

from indico.core import signals
from indico.util.date_time import format_human_timedelta
from indico.util.i18n import force_locale, orig_string
from indico.util.signals import named_objects_from_signal


def get_log_renderers():
    return named_objects_from_signal(signals.event.get_log_renderers.send(), plugin_attr='plugin')


def make_diff_log(changes, fields):
    """Create a value for log data containing change information.

    :param changes: a dict mapping attributes to ``(old, new)`` tuples
    :param fields: a dict mapping attributes to field metadata.  for
            simple cases this may be a string with the human-friendly
            title, for more advanced fields it should be a dict
            containing ``title``, a ``type`` string and a ``convert``
            callback which will be invoked with a tuple containing the
            old and new value
    """
    data = {'_diff': True}
    for key, field_data in fields.items():
        try:
            change = changes[key]
        except KeyError:
            continue
        if isinstance(field_data, str):
            field_data = {'title': field_data}
        title = field_data['title']
        convert = field_data.get('convert')
        attr = field_data.get('attr')
        default = field_data.get('default')
        type_ = field_data.get('type')
        not_none_change = [x for x in change if x is not None]
        if attr:
            change = [getattr(x, attr) if x is not None else '' for x in change]
        if convert:
            change = convert(change)
        if type_ is not None:
            # when we have an explicit type specified don't do any
            # guessing/conversions
            pass
        elif not_none_change and all(isinstance(x, Enum) for x in not_none_change):
            type_ = 'enum'
            change = [orig_string(getattr(x, 'title', x.name))
                      if x is not None else default
                      for x in change]
        elif all(isinstance(x, bool) for x in change):
            type_ = 'bool'
        elif all(isinstance(x, (int, float)) for x in change):
            type_ = 'number'
        elif all(isinstance(x, (list, tuple)) for x in change):
            type_ = 'list'
        elif all(isinstance(x, set) for x in change):
            type_ = 'list'
            change = list(map(sorted, change))
        elif all(isinstance(x, datetime) for x in change):
            type_ = 'datetime'
            change = [x.isoformat() for x in change]
        elif not_none_change and all(isinstance(x, timedelta) for x in not_none_change):
            type_ = 'timedelta'
            with force_locale(None):
                change = [format_human_timedelta(x) if x is not None else default for x in change]
        else:
            type_ = 'text'
            change = list(map(str, map(orig_string, change)))
        data[title] = list(change) + [type_]
    return data


def render_changes(a, b, type_):
    """Render the comparison of `a` and `b` as HTML.

    :param a: old value
    :param b: new value
    :param type_: the type determining how the values should be compared
    """
    if type_ in ('number', 'enum', 'bool', 'datetime', 'timedelta'):
        if a in (None, ''):
            a = '\N{EMPTY SET}'
        if b in (None, ''):
            b = '\N{EMPTY SET}'
        return f'{a} \N{RIGHTWARDS ARROW} {b}'
    elif type_ == 'string':
        return '{} \N{RIGHTWARDS ARROW} {}'.format(a or '\N{EMPTY SET}', b or '\N{EMPTY SET}')
    elif type_ == 'list':
        return _diff_list(a or [], b or [])
    elif type_ == 'struct_list':
        return _diff_list([repr(x) for x in a or []], [repr(x) for x in b or []])
    elif type_ == 'text':
        return _diff_text(a or '', b or '')
    else:
        raise NotImplementedError(f'Unexpected diff type: {type_}')


def _clean(strings, _linebreak_re=re.compile(r'\A(\n*)(.*?)(\n*)\Z', re.DOTALL)):
    # make linebreak changes more visible by adding an arrow indicating
    # the linebreak in addition to the linebreak itself
    leading_nl, string, trailing_nl = _linebreak_re.match(''.join(strings)).groups()
    _linebreak_symbol = Markup('<strong>\N{RETURN SYMBOL}</strong>\n')
    return Markup('').join((_linebreak_symbol * len(leading_nl),
                            string,
                            _linebreak_symbol * len(trailing_nl)))


def _diff_text(a, b, _noword_re=re.compile(r'(\W)')):
    # split the strings into words so we don't get changes involving
    # partial words.  this makes the diff much more readable to humans
    # as you don't end up with large deletions/insertions inside a word
    a = _noword_re.split(a)
    b = _noword_re.split(b)
    seqm = SequenceMatcher(a=a, b=b)
    output = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(''.join(seqm.a[a0:a1]))
        elif opcode == 'insert':
            inserted = _clean(seqm.b[b0:b1])
            output.append(Markup('<ins>{}</ins>').format(inserted))
        elif opcode == 'delete':
            deleted = _clean(seqm.a[a0:a1])
            output.append(Markup('<del>{}</del>').format(deleted))
        elif opcode == 'replace':
            deleted = _clean(seqm.a[a0:a1])
            inserted = _clean(seqm.b[b0:b1])
            output.append(Markup('<del>{}</del>').format(deleted))
            output.append(Markup('<ins>{}</ins>').format(inserted))
        else:
            raise RuntimeError('unexpected opcode: ' + opcode)
    return Markup('').join(output)


def _diff_list(a, b):
    seqm = SequenceMatcher(a=a, b=b)
    output = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output += seqm.a[a0:a1]
        elif opcode == 'insert':
            inserted = seqm.b[b0:b1]
            output += list(map(Markup('<ins>{}</ins>').format, inserted))
        elif opcode == 'delete':
            deleted = seqm.a[a0:a1]
            output += list(map(Markup('<del>{}</del>').format, deleted))
        elif opcode == 'replace':
            deleted = seqm.a[a0:a1]
            inserted = seqm.b[b0:b1]
            output += list(map(Markup('<del>{}</del>').format, deleted))
            output += list(map(Markup('<ins>{}</ins>').format, inserted))
        else:
            raise RuntimeError('unexpected opcode: ' + opcode)
    return Markup(', ').join(output)


def serialize_log_entry(entry):
    return {
        'id': entry.id,
        'type': entry.type,
        'realm': entry.realm.name,
        'kind': entry.kind.name,
        'module': entry.module,
        'description': entry.summary,
        'meta': entry.meta,
        'time': entry.logged_dt.astimezone(entry.event.tzinfo).isoformat(),
        'payload': entry.data,
        'user': {
            'fullName': entry.user.full_name if entry.user else None,
            'avatarURL': entry.user.avatar_url if entry.user else None
        }
    }
