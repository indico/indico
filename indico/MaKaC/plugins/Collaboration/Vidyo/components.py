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


from indico.core.extpoint import Component
from indico.core.extpoint.events import INavigationContributor
from MaKaC.plugins.util import PluginsWrapper
from indico.core.extpoint.index import ICatalogIndexProvider
from zope.interface import implements
from indico.core.index import Catalog
from MaKaC.plugins.Collaboration.Vidyo.indexes import BookingsByVidyoRoomIndex, BOOKINGS_BY_VIDYO_ROOMS_INDEX
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools

class VidyoContributor(Component):

    implements(INavigationContributor)

    @classmethod
    def addCheckBox2CloneConf(cls, obj, list):
        """ we show the clone checkbox if:
            * The Vidyo Plugin is active.
            * There are vidyo services in the event created by the user who wants to clone
        """
        #list of creators of the chat rooms
        if PluginsWrapper('Collaboration', 'Vidyo').isActive() and len(Catalog.getIdx("cs_bookingmanager_conference").get(obj._conf.getId()).getBookingList(filterByType="Vidyo")) !=0:
            list['cloneOptions'] += _("""<li><input type="checkbox" name="cloneVidyo" id="cloneVidyo" value="1" checked="checked"/>Vidyo</li>""")

    @classmethod
    def fillCloneDict(self, obj, params):
        options = params['options']
        paramNames = params['paramNames']
        options['vidyo'] = 'cloneVidyo' in paramNames

    @classmethod
    def cloneEvent(cls, confToClone, params):
        """ we'll clone only the vidyo services created by the user who is cloning the conference"""
        conf = params['conf']
        options = params['options']

        if options.get("vidyo", True):
            for vs in Catalog.getIdx("cs_bookingmanager_conference").get(confToClone.getId()).getBookingList(filterByType="Vidyo"):
                # Do not cloning the booking when were are NOT cloning the timetable (optionas has sessions and contribs)
                # and the booking is linked to a contrib/session
                if (options.get('sessions', False) and options.get('contributions', False)) or not vs.hasSessionOrContributionLink():
                    newBooking = vs.clone(conf)
                    Catalog.getIdx("cs_bookingmanager_conference").get(conf.getId()).addBooking(newBooking)
                    VidyoTools.getIndexByVidyoRoom().indexBooking(newBooking)
                    VidyoTools.getEventEndDateIndex().indexBooking(newBooking)

class CatalogIndexProvider(Component):
    implements(ICatalogIndexProvider)

    def catalogIndexProvider(self, obj):
        return [(BOOKINGS_BY_VIDYO_ROOMS_INDEX, BookingsByVidyoRoomIndex)]


