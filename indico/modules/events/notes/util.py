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

import itertools

from flask import render_template

from MaKaC.conference import SessionSlot, Contribution


def _get_all_notes(obj):
    """Gets all notes linked to the object and its nested objects.

    :param obj: A :class:`SessionSlot`, :class:`Contribution` or
                :class:`SubContribution` object.
    """
    notes = [obj.note] if obj.note else []
    nested_obj = []
    if isinstance(obj, SessionSlot):
        nested_obj = obj.getContributionList()
    elif isinstance(obj, Contribution):
        nested_obj = obj.getSubContributionList()
    return itertools.chain(notes, *map(_get_all_notes, nested_obj))


def compile_notes(event):
    """Compiles the text of all notes for a given event."""
    objects = [e.getOwner() for e in event.getSchedule().getEntries()]
    notes = itertools.chain.from_iterable(map(_get_all_notes, objects))
    return render_template('events/notes/compiled_notes.html', notes=notes)
