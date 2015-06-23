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

from __future__ import unicode_literals

from flask import request


def get_object_from_args(args=None):
    """Retrieves an event object from request arguments.

    This utility is meant to be used in cases where the same controller
    can deal with objects attached to various parts of an event which
    use different URLs to indicate which object to use.

    :param args: The request arguments. If unspecified,
                 ``request.view_args`` is used.
    :return: An ``(object_type, event, object)`` tuple.  The event is
             always the :class:`Conference` associated with the object.
             The object may be a `Conference`, `Session`, `Contribution`
             or `SubContribution`.  If the object does not exist,
             ``(object_type, None, None)`` is returned.
    """
    from MaKaC.conference import ConferenceHolder
    if args is None:
        args = request.view_args
    object_type = args['object_type']
    event = ConferenceHolder().getById(args['confId'], True)
    obj = None
    if event is None:
        obj = None
    elif object_type == 'event':
        obj = event
    elif object_type == 'session':
        obj = event.getSessionById(args['sessionId'])
    elif object_type == 'contribution':
        obj = event.getContributionById(args['contribId'])
    elif object_type == 'subcontribution':
        contrib = event.getContributionById(args['contribId'])
        if contrib is not None:
            obj = contrib.getSubContributionById(args['subContId'])
    else:
        raise ValueError('Unexpected object type: {}'.format(object_type))
    if obj is not None:
        return object_type, event, obj
    else:
        return object_type, None, None
