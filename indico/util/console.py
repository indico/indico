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

from __future__ import division, absolute_import, print_function

import fcntl
import re
import struct
import sys
import termios
import time
from operator import itemgetter
from getpass import getpass

from colorclass import Color

from indico.util.string import is_valid_mail, to_unicode


def strip_ansi(s, _re=re.compile(r'\x1b\[[;\d]*[A-Za-z]')):
    return _re.sub('', s)


def yesno(message):
    """
    A simple yes/no question (returns True/False)
    """
    inp = raw_input("%s [y/N] " % message)
    if inp == 'y' or inp == 'Y':
        return True
    else:
        return False


def prompt_email(prompt="Enter email: "):
    while True:
        try:
            email = unicode(raw_input(prompt.encode(sys.stderr.encoding)), sys.stdin.encoding).strip()
        except (EOFError, KeyboardInterrupt):  # ^D or ^C
            print()
            return None
        if is_valid_mail(email):
            return email
        else:
            warning(u"Email format is invalid")


def prompt_pass(prompt=u"Enter password: ", confirm_prompt=u"Confirm password: ", min_length=8, confirm=True):
    while True:
        try:
            password = unicode(getpass(prompt.encode(sys.stderr.encoding)), sys.stdin.encoding).strip()
        except (EOFError, KeyboardInterrupt):  # ^D or ^C
            print()
            return None
        # Empty, just prompt again
        if not password:
            continue
        # Too short, tell the user about the fact
        if min_length and len(password) < min_length:
            warning(u"Password is too short (must be at least {} chars)".format(min_length))
            continue
        # Confirm password if requested
        if not confirm:
            return password
        while True:
            confirmation = prompt_pass(confirm_prompt, min_length=0, confirm=False)
            if not confirmation:
                return None
            elif confirmation == password:
                return password
            else:
                warning(u"Passwords don't match")


def terminal_size():
    h, w, hp, wp = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
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
            title = to_unicode(get_title(item).replace('\n', ' '))
            text = fmt.format(i, total, (i / total * 100.0), remaining, get_id(item), title)
            print('\r', ' ' * term_width, end='', sep='')
            # terminal width + ansi control code length - trailing reset code (4)
            print('\r', text[:term_width + len(text.value_colors) - len(text.value_no_colors) - 4], cformat('%{reset}'),
                  end='', sep='')
            sys.stdout.flush()

        yield item

    print()


def conferenceHolderIterator(ch, verbose=True, deepness='subcontrib'):
    """
    Goes over all conferences, printing a status message (ideal for scripts)
    """

    def _eventIterator(conference, tabs):
        for contrib in conference.getContributionList():
            yield ('contrib', contrib)

            if deepness == 'subcontrib':
                for scontrib in contrib.getSubContributionList():
                    yield ('subcontrib', scontrib)

    idx = ch._getIdx()
    iterator = idx.iteritems()
    if verbose:
        iterator = verbose_iterator(iterator, len(idx.keys()), itemgetter(0), lambda x: x[1].getTitle())

    for id_, conf in iterator:
        yield 'event', conf
        if deepness in {'contrib', 'subcontrib'}:
            for contrib in _eventIterator(conf, 0):
                yield contrib


# Coloring

try:
    from termcolor import colored
except ImportError:
    def colored(text, *__, **___):
        """
        just a dummy function that returns the same string
        (in case termcolor is not available)
        """
        return text


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


# Error/warning/info message util methods

def error(message):
    """
    Print a red error message
    """
    print(colored(message, 'red'))


def warning(message):
    """
    Print a yellow warning message
    """
    print(colored(message, 'yellow'))


def info(message):
    """
    Print a blue information message
    """
    print(colored(message, 'cyan', attrs=['bold']))


def success(message):
    """
    Print a green success message
    """
    print(colored(message, 'green'))
