# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

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
        if verbose:
            text = "[%d/%d %f%%] %s %s" % \
                   (i, total, (float(i) / total * 100.0), id, conf.getTitle())
            print text[:80].ljust(80), '\r',
        i += 1

        yield ('event', conf)
        if deepness in ['contrib', 'subcontrib']:
            for contrib in _eventIterator(conf, 0):
                yield contrib


# Coloring

# pylint: disable-msg=W0611

try:
    from termcolor import colored
except ImportError:
    def colored(text, *__, **___):
        """
        just a dummy function that returns the same string
        (in case termcolor is not available)
        """
        return text
