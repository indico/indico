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

from MaKaC.conference import Conference, Contribution, SessionSlot


def get_all_notes(obj):
    """Gets all notes linked to the object and its nested objects.

    :param obj: A :class:`SessionSlot`, :class:`Contribution` or
                :class:`SubContribution` object.
    """
    notes = [obj.note] if obj.note else []
    nested_objects = []
    if isinstance(obj, Conference):
        nested_objects = [e.getOwner() for e in obj.getSchedule().getEntries()]
    if isinstance(obj, SessionSlot):
        nested_objects = obj.getContributionList()
    elif isinstance(obj, Contribution):
        nested_objects = obj.getSubContributionList()
    return itertools.chain(notes, *map(get_all_notes, nested_objects))
