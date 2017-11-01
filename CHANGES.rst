Changelog
=========


Version 2.1
-----------

*Unreleased*

Major Features
^^^^^^^^^^^^^^

- Add event roles, which are similar to local groups but within the
  scope of an event. They can be used both for assigning permissions
  within the event and also for quickly seeing which user has which
  role (such as "Program Committee" in the event
- Add new *List of Participants* (previously called *Roles*) which
  now shows each person's custom event roles and whether they have
  registered for the event in addition to the the default roles
  (speaker, chairperson, etc.)

Improvements
^^^^^^^^^^^^

- Allow specifying a default session for a track which will then be
  used by default when accepting an abstract in that track (:issue:`3069`)
- Allow marking contribution types as private so they cannot be selected
  by users submitting an abstract (:issue:`3138`)

Internal Changes
^^^^^^^^^^^^^^^^

- Rename *Roles* in ACL entries to *Permissions*.  This especially affects
  the ``can_manage`` method whose ``role`` argument has been renamed to
  ``permission`` (:issue:`3057`)


----


Version 2.0rc2
--------------

*Unreleased*

Improvements
^^^^^^^^^^^^

- Allow changing the reloader used by the dev server (:issue:`3150`)

Bugfixes
^^^^^^^^

- Do not show borders above/below the message in registration emails
  unless both the header and body blocks are used (:issue:`3151`)


Version 2.0rc1
--------------

*Released on November 10, 2017*

Improvements
^^^^^^^^^^^^

- Hide category field in event creation dialog if there are no
  subcategories (:issue:`3112`)
- Remove length limit from registration form field captions (:issue:`3119`)
- Use semicolons instead of commas as separator when exporting list
  values (such as multi-select registration form fields) to CSV or
  Excel (:issue:`3060`)
- Use custom site title in page title (:issue:`3018`)
- Allow manually entering dates in datetime fields (:issue:`3136`)
- Send emails through a celery task. This ensures users do not get
  an error if the mail server is temporarily unavailable. Sending an
  email is also retried for a while in case of failure. In case of a
  persistent failure the email is dumped to the temp directory and
  can be re-sent manually using the new ``indico resend_email``
  command (:issue:`3121`)
- Reject requests containing NUL bytes in the query string (:issue:`3142`)

Bugfixes
^^^^^^^^

- Do not intercept HTTP exceptions containing a custom response.
  When raising such exceptions we do not want the default handling
  but rather send the custom response to the client.
- Do not apply margin for empty root category sidebar (:issue:`3116`,
  thanks :user:`nop33`)
- Fix alignment of info-grid items on main conference page (:issue:`3126`)
- Properly align the label of the attachment folder title field
- Fix some rare unicode errors during exception handling/logging
- Clarify messages in session block rescheduling dialogs (:issue:`3080`)
- Fix event header bar in IE11 (:issue:`3135`)
- Fix footer on login page (:issue:`3132`)
- Use correct module name for abstract notification emails in the event log
- Remove linebreaks from email subject in paper review notifications
- Fix extra padding in the CFA roles dialog (:issue:`3129`)
- Do not show an extra day in timetable management if an event begins
  before a DST change
- Disable caching when retrieving the list of unscheduled contributions
- Process placeholders in the subject when emailing registrants
- Fix Shibboleth login with non-ascii names (:issue:`3143`)

Internal Changes
^^^^^^^^^^^^^^^^

- Add new ``is_ticket_blocked`` signal that can be used by plugins to
  disable ticket downloads for a registration.


Version 2.0a1
-------------

*Released on October 20, 2017*

This is the first release of the 2.0 series, which is an almost complete
rewrite of Indico based on a modern software stack and PostgreSQL.
