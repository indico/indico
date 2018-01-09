# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import os
import re

from indico.util.date_time import format_date, format_datetime, format_time


# fcntl is only available for POSIX systems
if os.name == 'posix':
    import fcntl


def utf8rep(text):
    # \x -> _x keeps windows systems satisfied
    return text.decode('utf-8').encode('unicode_escape').replace('\\x','_x')


def validMail(emailstr, allowMultiple=True):
    """
    Check the validity of an email address or serie of email addresses
    - emailstr: a string representing a single email address or several
    email addresses separated by separators
    Returns True if the email/emails is/are valid.
    """
    # Convert the separators into valid ones. For now only, mix of whitespaces,
    # semi-colons and commas are handled and replaced by commas. This way the
    # method only checks the validity of the email addresses without taking
    # care of the separators
    emails = setValidEmailSeparators(emailstr)

    # Creates a list of emails
    emaillist = emails.split(",")

    if not allowMultiple and len(emaillist) > 1:
        return False

    # Checks the validity of each email in the list
    if emaillist != None or emaillist != []:
        for em in emaillist:

            if re.search(r"^[-a-zA-Z0-9!#$%&'*+/=?\^_`{|}~]+(?:.[-a-zA-Z0-9!#$%&'*+/=?^_`{|}~]+)*@(?:[a-zA-Z0-9](?:[-a-zA-Z0-9]*[a-zA-Z0-9])?.)+[a-zA-Z0-9](?:[-a-zA-Z0-9]*[a-zA-Z0-9])?$",
                         em) == None:
    #        if re.search("^[a-zA-Z][\w\.-]*[a-zA-Z0-9]@[a-zA-Z0-9][\w\.-]*[a-zA-Z0-9]\.[a-zA-Z][a-zA-Z\.]*[a-zA-Z]$",
    #                     em) == None:
                return False
    return True


def setValidEmailSeparators(emailstr):
    """
    Replace occurrences of separators in a string of email addresses by
    occurrences of "," in order to get a string of emails valid with the
    html 'a' tag. Separators that could be replaced are semi-colons,
    whitespaces and mixes of the previous two along with commas. This allows
    the handling of multiple email addresses.
    - emailstr: the string of emails in which we want to convert the separators
    into commas
    """
    # remove occurences of separators at the beginning and at the end of
    # the string
    emails = re.subn(r"(?:^[ ;,]+)|(?:[ ;,]+$)", "", emailstr)[0]

    # return the string obtained after replacing the separators
    return re.subn(r"[ ;,]+", ",", emails)[0]


def isStringHTML(s):
    if not isinstance(s, basestring):
        return False
    s = s.lower()
    return any(tag in s for tag in ('<p>', '<p ', '<br', '<li>'))


def getEmailList(stri):
    emailList = []
    for email in stri.split(",") :
        email = email.strip()
        if email!="" and email.rfind(".", email.find("@") )>0 and email not in emailList :
            emailList.append(email)
    return emailList


def encodeUnicode(text, sourceEncoding = "utf-8"):
    try:
        tmp = str(text).decode( sourceEncoding )
    except:
        try:
            tmp = str(text).decode( 'iso-8859-1' )
        except:
            return ""
    return tmp.encode('utf-8')


def unicodeSlice(s, start, end, encoding='utf-8'):
    """Returns a slice of the string s, based on its encoding."""
    return s.decode(encoding, 'replace')[start:end]


def formatDateTime(dateTime, showWeek=False, format=None, locale=None, server_tz=False):
    week = "EEEE" if showWeek else ""

    if not format:
        return format_datetime(dateTime, week+'d/M/yyyy H:mm', locale=locale, server_tz=server_tz)
    else:
        return format_datetime(dateTime, format, locale=locale, server_tz=server_tz)


def formatDate(date, showWeek=False, format=None, locale=None, timezone=None):
    week = ""
    if showWeek:
        week = "EEE "
    if not format:
        return format_date(date, week+'d/M/yyyy', locale=locale, timezone=timezone)
    else:
        return format_date(date, format, locale=locale, timezone=timezone)


def formatTime(tm, format=None, locale=None, server_tz=False, tz=None):
    if not format:
        return format_time(tm, 'H:mm', locale=locale, timezone=tz, server_tz=server_tz)
    else:
        return format_time(tm, format, locale=locale, timezone=tz, server_tz=server_tz)


def formatDuration(duration, units = 'minutes', truncate = True):
    """ Formats a duration (a timedelta object)
    """

    seconds = duration.days * 86400 + duration.seconds

    if units == 'seconds':
        result = seconds
    elif units == 'minutes':
        result = seconds / 60
    elif units == 'hours':
        result = seconds / 3600
    elif units == 'days':
        result = seconds / 86400

    elif units == 'hours_minutes':
        #truncate has no effect here
        minutes = int(seconds / 60) % 60
        hours = int(seconds / 3600)
        return str(hours) + 'h' + str(minutes).zfill(2) + 'm'

    elif units == '(hours)_minutes':
        #truncate has no effect here
        minutes = int(seconds / 60) % 60
        hours = int(seconds / 3600)
        if hours:
            return str(hours) + 'h' + str(minutes).zfill(2) + 'm'
        else:
            return str(minutes) + 'm'

    else:
        raise Exception("Unknown duration unit: " + str(units))

    if truncate:
        return int(result)
    else:
        return result


class OSSpecific(object):
    """
    Namespace for OS Specific operations:
     - file locking
    """

    @classmethod
    def _lockFilePosix(cls, f, lockType):
        """
        Locks file f with lock type lockType
        """
        fcntl.flock(f, lockType)

    @classmethod
    def _lockFileOthers(cls, f, lockType):
        """
        Win32/others file locking could be implemented here
        """
        pass

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
