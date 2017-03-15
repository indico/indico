# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import division, absolute_import, print_function

import fcntl
import re
import struct
import sys
import termios
import time

import click
from click.types import convert_type
from colorclass import Color
from termcolor import colored

from indico.util.string import is_valid_mail, to_unicode


def prompt_email(prompt=u'Email', default=None, confirm=False):
    conv = convert_type(None)

    def _proc_email(val):
        val = conv(val).strip()
        if not is_valid_mail(val, multi=False):
            raise click.UsageError(u'invalid email')
        return val

    return click.prompt(prompt, default=default, confirmation_prompt=confirm, value_proc=_proc_email)


def prompt_pass(prompt=u'Password', min_length=8, confirm=True):
    while True:
        password = click.prompt(prompt, hide_input=True, confirmation_prompt=confirm).strip()
        # Empty, just prompt again
        if not password:
            continue
        # Too short, tell the user about the fact
        if min_length and len(password) < min_length:
            warning(u"Password is too short (must be at least {} chars)".format(min_length))
            continue
        return password


def terminal_size():
    h, w, hp, wp = struct.unpack(b'HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack(b'HHHH', 0, 0, 0, 0)))
    return w, h


def clear_line():
    """Clears the current line in the terminal"""
    print('\r', ' ' * terminal_size()[0], '\r', end='', sep='')


def verbose_iterator(iterable, total, get_id, get_title, print_every=10):
    """Iterates large iterables verbosely

    :param iterable: An iterable
    :param total: The number of items in `iterable`
    :param get_id: callable to retrieve the ID of an item
    :param get_title: callable to retrieve the title of an item
    """
    term_width = terminal_size()[0]
    start_time = time.time()
    fmt = cformat(
        '[%{cyan!}{:6}%{reset}/%{cyan}{}%{reset}  %{yellow!}{:.3f}%{reset}%  %{green!}{}%{reset}]  {:>8}  %{grey!}{}'
    )

    for i, item in enumerate(iterable, 1):
        if i % print_every == 0 or i == total:
            remaining_seconds = int((time.time() - start_time) / i * (total - i))
            remaining = '{:02}:{:02}'.format(remaining_seconds // 60, remaining_seconds % 60)
            id_ = get_id(item)
            title = to_unicode(get_title(item).replace('\n', ' '))
            text = fmt.format(i, total, (i / total * 100.0), remaining, id_, title)
            print('\r', ' ' * term_width, end='', sep='')
            # terminal width + ansi control code length - trailing reset code (4)
            print('\r', text[:term_width + len(text.value_colors) - len(text.value_no_colors) - 4], cformat('%{reset}'),
                  end='', sep='')
            sys.stdout.flush()

        yield item

    print()


def _cformat_sub(m):
    bg = u'on_{}'.format(m.group('bg')) if m.group('bg') else None
    attrs = ['bold'] if m.group('fg_bold') else None
    return colored(u'', m.group('fg'), bg, attrs=attrs)[:-4]


def cformat(string):
    """Replaces %{color} and %{color,bgcolor} with ansi colors.

    Bold foreground can be achieved by suffixing the color with a '!'
    """
    reset = colored(u'')
    string = string.replace(u'%{reset}', reset)
    string = re.sub(ur'%\{(?P<fg>[a-z]+)(?P<fg_bold>!?)(?:,(?P<bg>[a-z]+))?}', _cformat_sub, string)
    if not string.endswith(reset):
        string += reset
    return Color(string)
