# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import re
import urlparse

from flask import g, has_request_context, request

from MaKaC.common.url import URL, EndpointURL

from indico.core.config import Config


class BooleanMixin:
    """Mixin to convert True to 'y' and remove False altogether."""
    _true = 'y'

    @classmethod
    def _translateParams(cls, params):
        return dict((key, cls._true if value is True else value)
                    for key, value in params.iteritems()
                    if value is not False)


class BooleanTrueMixin(BooleanMixin):
    _true = 'True'


class URLHandler(object):
    """This is the generic URLHandler class. It contains information about the
        concrete URL pointing to the request handler and gives basic methods to
        generate the URL from some target objects complying to the Locable
        interface.
       Actually, URLHandlers must never be intanciated as all their methods are
        classmethods.

       Attributes:
        _relativeURL - (string) Contains the relative (the part which is
            variable from the root) URL pointing to the corresponding request
            handler.
        _endpoint - (string) Contains the name of a Flask endpoint.
        _defaultParams - (dict) Default params (overwritten by kwargs)
        _fragment - (string) URL fragment to set
    """
    _relativeURL = None
    _endpoint = None
    _defaultParams = {}
    _fragment = False

    @classmethod
    def getRelativeURL(cls):
        """Gives the relative URL (URL part which is carachteristic) for the
            corresponding request handler.
        """
        return cls._relativeURL

    @classmethod
    def getStaticURL(cls, target=None, **params):
        if cls._relativeURL:
            return cls._relativeURL.replace('.py', '.html')
        else:
            # yay, super ugly, but it works...
            return re.sub(r'^event\.', '', cls._endpoint) + '.html'

    @classmethod
    def _want_secure_url(cls, force_secure=None):
        if not Config.getInstance().getBaseSecureURL():
            return False
        elif force_secure is not None:
            return force_secure
        elif not has_request_context():
            return False
        else:
            return request.is_secure

    @classmethod
    def _getURL(cls, _force_secure=None, **params):
        """ Gives the full URL for the corresponding request handler.

            Parameters:
                _force_secure - (bool) create a secure url if possible
                params - (dict) parameters to be added to the URL.
        """

        secure = cls._want_secure_url(_force_secure)
        if not cls._endpoint:
            # Legacy UH containing a relativeURL
            cfg = Config.getInstance()
            baseURL = cfg.getBaseSecureURL() if secure else cfg.getBaseURL()
            url = URL('%s/%s' % (baseURL, cls.getRelativeURL()), **params)
        else:
            assert not cls.getRelativeURL()
            url = EndpointURL(cls._endpoint, secure, params)

        if cls._fragment:
            url.fragment = cls._fragment

        return url

    @classmethod
    def _translateParams(cls, params):
        # When overriding this you may return a new dict or modify the existing one in-place.
        # But in any case, you must return the final dict.
        return params

    @classmethod
    def _getParams(cls, target, params):
        params = dict(cls._defaultParams, **params)
        if target is not None:
            params.update(target.getLocator())
        params = cls._translateParams(params)
        return params

    @classmethod
    def getURL(cls, target=None, _ignore_static=False, **params):
        """Gives the full URL for the corresponding request handler. In case
            the target parameter is specified it will append to the URL the
            the necessary parameters to make the target be specified in the url.

            Parameters:
                target - (Locable) Target object which must be uniquely
                    specified in the URL so the destination request handler
                    is able to retrieve it.
                params - (Dict) parameters to be added to the URL.
        """
        if not _ignore_static and g.get('static_site'):
            return URL(cls.getStaticURL(target, **params))
        return cls._getURL(**cls._getParams(target, params))


# Hack to allow secure Indico on non-80 ports
def setSSLPort(url):
    """
    Returns url with port changed to SSL one.
    If url has no port specified, it returns the same url.
    SSL port is extracted from loginURL (MaKaCConfig)
    """
    # Set proper PORT for images requested via SSL
    sslURL = Config.getInstance().getBaseSecureURL()
    sslPort = ':%d' % (urlparse.urlsplit(sslURL).port or 443)

    # If there is NO port, nothing will happen (production indico)
    # If there IS a port, it will be replaced with proper SSL one, taken from loginURL
    regexp = ':\d{2,5}'   # Examples:   :8080   :80   :65535
    return re.sub(regexp, sslPort, url)


class UHConferenceHelp(URLHandler):
    _endpoint = 'misc.help'


class UHConferenceDisplay(URLHandler):
    _endpoint = 'event.conferenceDisplay'


class UHConferenceOtherViews(URLHandler):
    _endpoint = 'event.conferenceOtherViews'


# ============================================================================
# ROOM BOOKING ===============================================================
# ============================================================================

# Free standing ==============================================================


class UHRoomBookingMapOfRooms(URLHandler):
    _endpoint = 'rooms.roomBooking-mapOfRooms'


class UHRoomBookingMapOfRoomsWidget(URLHandler):
    _endpoint = 'rooms.roomBooking-mapOfRoomsWidget'


class UHRoomBookingWelcome(URLHandler):
    _endpoint = 'rooms.roomBooking'


class UHRoomBookingSearch4Bookings(URLHandler):
    _endpoint = 'rooms.roomBooking-search4Bookings'


class UHRoomBookingRoomDetails(BooleanTrueMixin, URLHandler):
    _endpoint = 'rooms.roomBooking-roomDetails'


class UHRoomBookingRoomStats(URLHandler):
    _endpoint = 'rooms.roomBooking-roomStats'


class UHRoomBookingDeleteBooking(URLHandler):
    _endpoint = 'rooms.roomBooking-deleteBooking'


# RB Administration
class UHRoomBookingAdmin(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-admin'


class UHRoomBookingAdminLocation(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-adminLocation'


class UHRoomBookingSetDefaultLocation(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-setDefaultLocation'


class UHRoomBookingSaveLocation(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-saveLocation'


class UHRoomBookingDeleteLocation(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-deleteLocation'


class UHRoomBookingSaveEquipment(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-saveEquipment'


class UHRoomBookingDeleteEquipment(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-deleteEquipment'


class UHRoomBookingSaveCustomAttributes(URLHandler):
    _endpoint = 'rooms_admin.roomBooking-saveCustomAttributes'


class UHConfClone(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-clone'


class UHConfPerformCloning(URLHandler):
    _endpoint = 'event_mgmt.confModifTools-performCloning'


class UHConfUser(URLHandler):
    @classmethod
    def getURL(cls, conference, av=None):
        url = cls._getURL()
        if conference is not None:
            loc = conference.getLocator().copy()
            if av:
                loc.update(av.getLocator())
            url.setParams(loc)
        return url


class UHConfEnterAccessKey(UHConfUser):
    _endpoint = 'event.conferenceDisplay-accessKey'


class UHErrorReporting(URLHandler):
    _endpoint = 'misc.errors'


class UHConfMyStuff(URLHandler):
    _endpoint = 'event.myconference'


class UHResetSession(URLHandler):
    _endpoint = 'misc.resetSessionTZ'


class UHContact(URLHandler):
    _endpoint = 'misc.contact'
