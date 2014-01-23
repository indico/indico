# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Multiple CLI utils
"""


def yesno(message):
    """
    A simple yes/no question (returns True/False)
    """
    inp = raw_input("%s [y/N] " % message)
    if inp == 'y' or inp == 'Y':
        return True
    else:
        return False


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

    total = len(idx.keys())

    i = 1
    for id, conf in idx.iteritems():
        if verbose and i % 10 == 9:
            text = "[%d/%d %f%%] %s %s" % \
                   (i, total, (float(i) / total * 100.0), id, conf.getTitle())
            print text[:80].ljust(80), '\r',
        i += 1

        yield ('event', conf)
        if deepness in ['contrib', 'subcontrib']:
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


# Error/warning/info message util methods

def error(message):
    """
    Print a red error message
    """
    print colored(message, 'red')


def warning(message):
    """
    Print a yellow warning message
    """
    print colored(message, 'yellow')


def info(message):
    """
    Print a blue information message
    """
    print colored(message, 'cyan', attrs=['bold'])


def success(message):
    """
    Print a green success message
    """
    print colored(message, 'green')
