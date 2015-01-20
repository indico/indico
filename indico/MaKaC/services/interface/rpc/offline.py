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

from indico.util.json import dumps

import MaKaC

def jsonDescriptor(object):

    # TODO: Merge with locators?

    if isinstance(object, MaKaC.conference.Conference):
        return {'conference': object.getId()}
    elif isinstance(object, MaKaC.conference.Contribution):
        return {'conference': object.getConference().getId(),
                'contribution': object.getId()}
    elif isinstance(object, MaKaC.conference.Session):
        return {'conference': object.getConference().getId(),
                'session': object.getId()}
    elif isinstance(object, MaKaC.conference.SessionSlot):
        return {'conference': object.getConference().getId(),
                'session': object.getSession().getId(),
                'slot': object.getId()}
    elif isinstance(object, MaKaC.schedule.BreakTimeSchEntry):
        info = {'conference': object.getOwner().getConference().getId(),
                     'break': object.getId()}
        if isinstance(object.getOwner(), MaKaC.conference.SessionSlot):
            info['slot'] = object.getOwner().getId()
            info['session'] = object.getOwner().getSession().getId()
        return info

    return None

def jsonDescriptorType(descriptor):

    if 'break' in descriptor:
        return MaKaC.schedule.BreakTimeSchEntry
    elif 'slot' in descriptor:
        return MaKaC.conference.SessionSlot
    elif 'contribution' in descriptor:
        return MaKaC.conference.Contribution
    elif 'session' in descriptor:
        return MaKaC.conference.Session
    elif 'conference' in descriptor:
        return MaKaC.conference.Conference
    else:
        return None

def decideInheritanceText(event):
    if isinstance(event, MaKaC.conference.SessionSlot):
        text = _("Inherit from parent slot")
    elif isinstance(event, MaKaC.conference.Session):
        text = _("Inherit from parent session")
    elif isinstance(event, MaKaC.conference.Conference):
        text = _("Inherit from parent event")
    else:
        text = str(repr(parent))
    return text


def roomInfo(event, level='real'):
    # gets inherited/real/own location/room properties

    if level == 'inherited':
        room = event.getInheritedRoom()
        location = event.getInheritedLocation()
        text = decideInheritanceText(event.getLocationParent())

    elif level == 'real':
        room = event.getRoom()
        location = event.getLocation()
        text = decideInheritanceText(event)

    elif level == 'own':
        room = event.getOwnRoom()
        location = event.getOwnLocation()
        text = ''

    locationName, roomName, address = None, None, None

    if location:
        locationName = location.getName()
        address = location.getAddress()
    if room:
        roomName = room.getName()

    return {'location': locationName,
            'room': roomName,
            'address': address,
            'text': text}
