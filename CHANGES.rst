Changelog
=========


Version 2.0a2
-------------

*Unreleased*

Improvements
^^^^^^^^^^^^

- Hide category field in event creation dialog if there are no
  subcategories (:issue:`3112`)

Bugfixes
^^^^^^^^

- Do not intercept HTTP exceptions containing a custom response.
  When raising such exceptions we do not want the default handling
  but rather send the custom response to the client.


Version 2.0a1
-------------

*Released on October 20, 2017*

This is the first release of the 2.0 series, which is an almost complete
rewrite of Indico based on a modern software stack and PostgreSQL.
