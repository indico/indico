# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import fcntl
import re
import struct
import sys
import termios
import time
from datetime import timedelta

import click
from click.types import convert_type
from colorclass import Color
from termcolor import colored

from indico.util.date_time import format_human_timedelta
from indico.util.string import validate_email


def prompt_email(prompt='Email', default=None, confirm=False):
    conv = convert_type(None)

    def _proc_email(val):
        val = conv(val).strip()
        if not validate_email(val):
            raise click.UsageError('invalid email')
        return val

    return click.prompt(prompt, default=default, confirmation_prompt=confirm, value_proc=_proc_email)


def prompt_pass(prompt='Password', min_length=8, confirm=True):
    while True:
        password = click.prompt(prompt, hide_input=True, confirmation_prompt=confirm).strip()
        # Empty, just prompt again
        if not password:
            continue
        # Too short, tell the user about the fact
        if min_length and len(password) < min_length:
            click.echo(f'Password is too short (must be at least {min_length} chars)')
            continue
        return password


def terminal_size():
    h, w, hp, wp = struct.unpack(b'HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack(b'HHHH', 0, 0, 0, 0)))
    return w, h


def clear_line():
    """Clear the current line in the terminal."""
    print('\r', ' ' * terminal_size()[0], '\r', end='', sep='')


def verbose_iterator(iterable, total, get_id, get_title=None, print_every=10, print_total_time=False):
    """Iterate large iterables verbosely.

    :param iterable: An iterable
    :param total: The number of items in `iterable`
    :param get_id: callable to retrieve the ID of an item
    :param get_title: callable to retrieve the title of an item
    :param print_every: after which number of items to update the progress
    :param print_total_time: whether to print the total time spent at the end
    """
    term_width = terminal_size()[0]
    start_time = time.time()
    fmt = cformat(
        '[%{cyan!}{:6}%{reset}/%{cyan}{}%{reset}  %{yellow!}{:.3f}%{reset}%  %{green!}{}%{reset}]  {:>8}  %{grey!}{}'
    )
    end_fmt = cformat(
        '[%{cyan!}{:6}%{reset}/%{cyan}{}%{reset}  %{yellow!}{:.3f}%{reset}%  %{green!}{}%{reset}]  '
        'Total duration: %{green}{}'
    )

    def _print_text(text):
        print('\r', ' ' * term_width, end='', sep='')
        # terminal width + ansi control code length - trailing reset code (4)
        print('\r', text[:term_width + len(text.value_colors) - len(text.value_no_colors) - 4], cformat('%{reset}'),
              end='', sep='')
        sys.stdout.flush()

    for i, item in enumerate(iterable, 1):
        if i % print_every == 0 or i == total:
            remaining_seconds = int((time.time() - start_time) / i * (total - i))
            minutes, seconds = divmod(remaining_seconds, 60)
            remaining = f'{minutes:02}:{seconds:02}'
            id_ = get_id(item)
            title = get_title(item).replace('\n', ' ') if get_title else ''
            text = fmt.format(i, total, (i / total * 100.0), remaining, id_, title)
            _print_text(text)

        yield item

    if print_total_time:
        total_duration = timedelta(seconds=(time.time() - start_time))
        _print_text(end_fmt.format(total, total, 100, '00:00', format_human_timedelta(total_duration)))

    print()


def _cformat_sub(m):
    bg = 'on_{}'.format(m.group('bg')) if m.group('bg') else None
    attrs = ['bold'] if m.group('fg_bold') else None
    return colored('', m.group('fg'), bg, attrs=attrs)[:-4]


def cformat(string):
    """Replace %{color} and %{color,bgcolor} with ansi colors.

    Bold foreground can be achieved by suffixing the color with a '!'.
    """
    reset = colored('')
    string = string.replace('%{reset}', reset)
    string = re.sub(r'%\{(?P<fg>[a-z]+)(?P<fg_bold>!?)(?:,(?P<bg>[a-z]+))?}', _cformat_sub, string)
    if not string.endswith(reset):
        string += reset
    return Color(string)
