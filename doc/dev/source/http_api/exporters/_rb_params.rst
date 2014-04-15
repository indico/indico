
==============  =====  ================  =======================================================================
Param           Short  Values            Description
==============  =====  ================  =======================================================================
occurrences     occ    yes, no           Include all occurrences of room reservations.
cancelled       cxl    yes, no           If specified only include cancelled (*yes*) or
                                         non-cancelled (*no*) reservations.
rejected        rej    yes, no           If specified only include rejected/non-rejected resvs.
confirmed       `-`    yes, no, pending  If specified only include bookings/pre-bookings with the
                                         given state.
archival        arch   yes, no           If specified only include bookings (not) from the past.
recurring       rec    yes, no           If specified only include bookings which are (not) recurring.
repeating       rep    yes, no           Alias for *recurring*
avc             `-`    yes, no           If specified only include bookings which (do not) use AVC.
avcsupport      avcs   yes, no           If specified only include bookings which (do not) need AVC Support.
startupsupport  sts    yes, no           If specified only include bookings which (do not) need Startup Support.
bookedfor       bf     text (wildcards)  Only include bookings where the *booked for* field matches the
                                         given wildcard string.
==============  =====  ================  =======================================================================
