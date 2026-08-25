.. _security:

Security
=======

Known Risks and Threats
+++++++

This section presents a number of known security risks and threats that must be considered when using Indico. While Indico is designed with security in mind, no system is completely immune to vulnerabilities. The risks described here are not exhaustive, but they highlight the areas where particular attention should be paid to ensure a secure deployment. Understanding these risks is essential for administrators and operators who are responsible for running Indico in production environments.

- Indico uses Pickle to serialize the tasks and results that travel, respectively, from the message broker to the worker and from the result backend to the web process via Redis. Access to the Redis instance must therefore be properly protected, since the ability to write to it could allow an attacker to achieve code execution both in the worker and in the web process.
- The Indico CLI exposes a pair of commands to export and import event archives. These archives are serialized and deserialized using either YAML or Pickle, and both formats can lead to code execution when a malicious file is deserialized. Untrusted archives must therefore be treated as potentially dangerous input.
- The Celery beat scheduler persists its schedule as a Python ``shelve`` at ``<TEMP_DIR>/celerybeat-schedule``, and this file is reopened and deserialized via Pickle every time the worker is started with beat enabled (``indico celery worker -B``). If ``TEMP_DIR`` points to a location that another local user can write to and traverse, that user could replace the schedule with a crafted Pickle payload and achieve code execution as the Indico worker user on the next restart. ``TEMP_DIR`` must therefore never be set to a shared or world-writable directory: keep it inside the Indico user's home directory with the restrictive permissions applied by the installation guide (e.g. a ``0710`` home directory), and never point it at a world-writable location such as ``/tmp``.

.. toctree::

