Files
=====

General Information
-------------------

The file export is only available for authenticated users, i.e. when
using an API key and a signature (if enabled).


URL Format
----------
*/export/event/EVENT_ID/session/SESSION_ID/contrib/CONTRIBUTION_ID/subcontrib/SUBCONTRIBUTION_ID/material/MATERIAL_ID/RESOURCE_ID.TYPE*

All ID's should be single ID, not separated list.

| The *EVENT_ID* should be the event ID, e.g. *123*.
| The *SESSION_ID*  *(optional)* should be the session ID, e.g. *4*.
| The *CONTRIBUTION_ID* *(optional)* should be the contribution ID, e.g. *3*.
| The *SUBCONTRIBUTION_ID* *(optional)* should be the sub-contribution ID, e.g. *1*.
| The *MATERIAL_ID* should by the material name if it came default group e.g. *Slides* or material ID if not, e.g. *2*.
| The *RESOURCE_ID* should by the resource ID.
| Only supported *TYPE* for files is *bin* (binary data).


Parameters
----------

None


Detail Levels
-------------

file
~~~~~

Returns file (or an error in *JSON* format).

For example: https://indico.server/export/event/23/session/0/contrib/3/material/slides/3.bin?ak=00000000-0000-0000-0000-000000000000

