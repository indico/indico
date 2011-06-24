Common Parameters
==================

The following parameters are valid for all requests no matter which element
is requested. If a parameter has a shorter form, it's given in parentheses.

==========  =====  =======================================================
Param       Short  Description
==========  =====  =======================================================
nocache     nc     Do not return cached results (the results are written
                   to the cache though).
pretty      p      Pretty-print the output. When exporting as JSON it will
                   include whitespace to make the json more human-readable.
onlypublic  op     Only return results visible to unauthenticated users
                   when set to *yes*.
limit       n      Return no more than the X results.
offset      O      Skip the first X results.
detail      d      Specify the detail level (values depend on the exported
                   element)
order       o      Sort the results. Must be one of *id*, *end*, *title*.
descending  c      Sort the results in descending order when set to *yes*.
tz          `-`    Use the given timezone when returning time information.
==========  =====  =======================================================
