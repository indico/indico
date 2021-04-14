# Security Policy

## Supported Versions

Indico uses the second part of the version number for major feature releases, ie.
2.2, 2.3, ...

**Bugfixes are generally only released for the latest major version (e.g. 2.3.1 to
fix bugs discovered in 2.3).**

**For security releases we usually follow the same schema.** In exceptional cases
where the previous version (e.g. 2.2) is still somewhat recent and thus widely
used AND no suitable workarounds exist, we may also create a patch release for
that version.

Once version 3.0 (currently under development) is out, the same versioning
schema will apply there. However, due to the move from Python 2 or Python 3 and
the former having reached its end-of-live, no more 2.3.x releases will be made
after that point, and anyone running an Indico instance will be expected to move
to 3.0 as security cannot be guaranteed in an environment that has reached its
end-of-life.

## Reporting a Vulnerability

Please email indico-team@cern.ch to report security vulnerabilities privately.
