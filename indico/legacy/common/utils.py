# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os


# fcntl is only available for POSIX systems
if os.name == 'posix':
    import fcntl


def isStringHTML(s):
    if not isinstance(s, str):
        return False
    s = s.lower()
    return any(tag in s for tag in ('<p>', '<p ', '<br', '<li>'))


class OSSpecific:
    """
    Namespace for OS Specific operations:
     - file locking
    """

    @classmethod
    def _lockFilePosix(cls, f, lockType):
        """Lock file f with lock type lockType."""
        fcntl.flock(f, lockType)

    @classmethod
    def _lockFileOthers(cls, f, lockType):
        """Win32/others file locking could be implemented here."""

    @classmethod
    def lockFile(cls, f, lockType):
        """
        API method - locks a file
        f - file handler
        lockType - string: LOCK_EX | LOCK_UN | LOCK_SH
        """
        cls._lockFile(f, cls._lockTranslationTable[lockType])

    # Check OS and choose correct locking method
    if os.name == 'posix':
        _lockFile = _lockFilePosix
        _lockTranslationTable = {
            'LOCK_EX': fcntl.LOCK_EX,
            'LOCK_UN': fcntl.LOCK_UN,
            'LOCK_SH': fcntl.LOCK_SH
        }
    else:
        _lockFile = _lockFileOthers
        _lockTranslationTable = {
            'LOCK_EX': None,
            'LOCK_UN': None,
            'LOCK_SH': None
        }
