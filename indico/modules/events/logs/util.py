# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

import re
from difflib import SequenceMatcher

from enum import Enum
from markupsafe import Markup

from indico.core import signals
from indico.util.i18n import orig_string
from indico.util.signals import named_objects_from_signal


def get_log_renderers():
    return named_objects_from_signal(signals.event.get_log_renderers.send(), plugin_attr='plugin')


def make_diff_log(changes, fields, types=None):
    """Create a value for log data containing change information.

    :param: a dict mapping attributes to ``(old, new)`` tuples
    :param: a dict mapping attributes to human-friendly titles
    :param: a dict overriding type information for attributes. can be
            a string or a function that takes a tuple with the old/new
            value and returns a ``(type, changes)`` tuple
    """
    data = {'_diff': True}
    for key, title in fields.iteritems():
        try:
            change = changes[key]
        except KeyError:
            continue
        if types and key in types:
            type_ = types[key]
            if callable(type_):
                type_, change = type_(change)
        elif all(isinstance(x, Enum) for x in change):
            type_ = 'enum'
            change = [orig_string(getattr(x, 'title', x.name)) for x in change]
        elif all(isinstance(x, (int, long, float)) for x in change):
            type_ = 'number'
        elif all(isinstance(x, (list, tuple)) for x in change):
            type_ = 'list'
        elif all(isinstance(x, set) for x in change):
            type_ = 'list'
            change = map(sorted, change)
        elif all(isinstance(x, bool) for x in change):
            type_ = 'bool'
        else:
            type_ = 'text'
            change = map(unicode, change)
        data[title] = list(change) + [type_]
    return data


def render_changes(a, b, type_):
    """Render the comparison of `a` and `b` as HTML.

    :param a: old value
    :param b: new value
    :param type_: the type determining how the values should be compared
    """
    if type_ in ('number', 'enum', 'string', 'bool'):
        return '{} \N{RIGHTWARDS ARROW} {}'.format(a, b)
    elif type_ == 'list':
        return _diff_list(a, b)
    elif type_ == 'text':
        return _diff_text(a, b)
    else:
        raise NotImplementedError('Unexpected diff type: {}'.format(type_))


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
            output += map(Markup('<ins>{}</ins>').format, inserted)
        elif opcode == 'delete':
            deleted = seqm.a[a0:a1]
            output += map(Markup('<del>{}</del>').format, deleted)
        elif opcode == 'replace':
            deleted = seqm.a[a0:a1]
            inserted = seqm.b[b0:b1]
            output += map(Markup('<del>{}</del>').format, deleted)
            output += map(Markup('<ins>{}</ins>').format, inserted)
        else:
            raise RuntimeError('unexpected opcode: ' + opcode)
    return Markup(', ').join(output)
