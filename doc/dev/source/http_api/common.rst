Common Parameters
==================

The following parameters are valid for all requests no matter which element
is requested. If a parameter has a shorter form, it's given in parentheses.

==========  =====  =======================================================
Param       Short  Description
==========  =====  =======================================================
from/to     f/t    Accepted formats:
                      * ISO 8601 subset - YYYY-MM-DD[THH:MM]
                      * 'today', 'yesterday', 'tomorrow' and 'now'
                      * days in the future/past: '[+/-]DdHHhMMm'
pretty      p      Pretty-print the output. When exporting as JSON it will
                   include whitespace to make the json more human-readable.
onlypublic  op     Only return results visible to unauthenticated users
                   when set to *yes*.
onlyauthed  oa     Fail if the request is unauthenticated for any reason
                   when this is set to *yes*.
cookieauth  ca     Use the Indico session cookie to authenticate instead of
                   an API key.
limit       n      Return no more than the X results.
offset      O      Skip the first X results.
detail      d      Specify the detail level (values depend on the exported
                   element)
order       o      Sort the results. Must be one of *id*, *start*, *end*,
                   *title*.
descending  c      Sort the results in descending order when set to *yes*.
tz          `-`    Assume given timezone (default UTC) for specified dates.
                   Example: ``Europe/Lisbon``.
==========  =====  =======================================================
