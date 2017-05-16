Video Services & Collaboration
==============================

URL Format
----------
*/export/video/SERVICE_ID.TYPE*

The SERVICE_ID may be a single collaboration type or many separated by `-`. 
At present, the only TYPE compatible with the Video Services export is `ics` / iCalendar.

As the query is signed with a signature generated using secret API key, the query need not be timestamped.
Instead, each booking is given its own unique identifier and, therefore, the
generated query URL may be fed as a persistent calendar for importing in your application 
of choice. The link will only expire once your account has been closed, if TTL is required by
your server administrator or your API key is deleted.

If TTL is required by your server administrator, requests should be both timestamped and signed.

Parameters
----------

===========  =====  ================  =============================================================
Param        Short  Values            Description
===========  =====  ================  =============================================================
alarms       `-`    int               If defined with a value of x int, all bookings to be exported 
                                      will be accompanied by a matching alarm set to occur x minutes 
                                      prior to the start of the booking itself. The alarm is set to 
                                      provide a popup reminder. The default value is 0 minutes.
===========  =====  ================  =============================================================

Please be aware that specifying the alarm parameter in your query will assign alarms to `every` 
booking which is to be exported.

Service Identifiers Used in CERN
--------------------------------

The following parameters are both for example to other installations, and for use within CERN installations of
Indico, they represent the options available for configuration through the SERVICE_ID parameter.

==========  ==============================
SERVICE_ID  Linked Service
==========  ==============================
all         Traverse all plugin indices.
vidyo       Return Vidyo bookings only.
evo         Return EVO bookings only.
mcu         Return CERNMCU bookings only.
webcast     Return Webcast Requests only.
recording   Return Recording Requests only.
==========  ==============================

SERVICE_ID may be one of more of these identifiers, if more than one is required simply join the service names with `-`, please
refer to common examples for usage scenarios.

Common Examples
---------------

All Bookings
~~~~~~~~~~~~

To obtain all bookings in the past 7 days for all collaboration plugins registered:

https://indico.server/export/video/all.ics?ak=API_KEY&from=-70000&to=now&signature=SIGNATURE

To obtain the same output, but with alarms set to display 20 minutes prior to each event:

https://indico.server/export/video/all.ics?ak=API_KEY&alarms=20&from=-70000&to=now&signature=SIGNATURE

Individual Plugin Bookings
~~~~~~~~~~~~~~~~~~~~~~~~~~

To obtain bookings from a specific plugin, in this example Vidyo, from a set date range and with alarms 30
minutes prior to the booking:

https://indico.server/export/video/vidyo.ics?ak=API_KEY&alarms=30&from=2011-08-01&to=2011-12-01&signature=SIGNATURE

Multiple Plugin Bookings
~~~~~~~~~~~~~~~~~~~~~~~~

We may also reference more than one plugin's bookings, to request all EVO and CERNMCU bookings over a 
specified date range with no alarms:

https://indico.server/export/video/evo-mcu.ics?ak=API_KEY&from=2011-09-01&to=2011-09-08&signature=SIGNATURE

