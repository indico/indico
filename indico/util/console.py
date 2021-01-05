# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, division, print_function

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

from indico.util.string import to_unicode, validate_email


def prompt_email(prompt=u'Email', default=None, confirm=False):
    conv = convert_type(None)

    def _proc_email(val):
        val = conv(val).strip()
        if not validate_email(val):
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
            click.echo(u"Password is too short (must be at least {} chars)".format(min_length))
            continue
        return password


def terminal_size():
    h, w, hp, wp = struct.unpack(b'HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack(b'HHHH', 0, 0, 0, 0)))
    return w, h


def clear_line():
    """Clear the current line in the terminal."""
    print('\r', ' ' * terminal_size()[0], '\r', end='', sep='')


def verbose_iterator(iterable, total, get_id, get_title, print_every=10):
    """Iterate large iterables verbosely.

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
    """Replace %{color} and %{color,bgcolor} with ansi colors.

    Bold foreground can be achieved by suffixing the color with a '!'.
    """
    reset = colored(u'')
    string = string.replace(u'%{reset}', reset)
    string = re.sub(r'%\{(?P<fg>[a-z]+)(?P<fg_bold>!?)(?:,(?P<bg>[a-z]+))?}', _cformat_sub, string)
    if not string.endswith(reset):
        string += reset
    return Color(string)
