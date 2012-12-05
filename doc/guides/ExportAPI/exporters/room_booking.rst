Room Booking
============

General Information
-------------------

The room booking api is only available for authenticated users,
i.e. when using an API key and a signature (if enabled).
If the room booking system is restricted to certain users/groups this
restriction applies for the reservation export API, too.
The booking will fail if there is a collision with another one, blocking or unavailable period.

The room booking api handle only POST requests.

Note that it is not possible to pre-book a room through this api.

URL Format
----------
*/api/roomBooking/bookRoom.TYPE*

The *TYPE* should be *json* or *xml*.


Parameters
----------

Following parameters are obligatory:

==============  ================  =======================================================================
Param           Values            Description
==============  ================  =======================================================================
location        text              Room location, e.g. *CERN*
roomid          text              Room id
from/to         f/t               Start/End time for a booking. Accepted formats:
                                        * ISO 8601 subset - YYYY-MM-DD[THH:MM]
                                        * 'today', 'yesterday', 'tomorrow' and 'now'
                                        * days in the future/past: '[+/-]DdHHhMMm'
reason          text              Reason for booking a room
username        text              User login name for whom the booking will be created
==============  ================  =======================================================================


Detail Levels
-------------

book a room
~~~~~~~~~~~~

Returns *reservation id* if the booking was successful or error information it there were any problems.

For example, http://indico.server/api/roomBooking/bookRoom.json?username=jatrzask&from=2012-12-29T18:11&ak=00000000-0000-0000-0000-000000000000&to=2012-12-29T20:15&reason=meeting&location=CERN&roomid=189::

    {
        {
            "url": "\/api\/roomBooking\/bookRoom.json?username=jatrzask&from=2012-12-29T18%3A11&ak=00000000-0000-0000-0000-000000000000&to=2012-12-29T20%3A15&reason=meeting&location=CERN&roomid=189", 
            "_type": "HTTPAPIResult",
            "results": {
                "reservationID": 45937
            },
            "ts": 1354695663
        }
    }
