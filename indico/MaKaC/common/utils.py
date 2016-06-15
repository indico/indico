# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
import time
from datetime import datetime

from indico.core.db import db
from indico.util.date_time import format_datetime, format_date, format_time

from MaKaC import errors


# fcntl is only available for POSIX systems
if os.name == 'posix':
    import fcntl

_KEY_DEFAULT_LENGTH = 20
_FAKENAME_SIZEMIN = 5
_FAKENAME_SIZEMAX = 10


def stringToDate( str ):
    months = { "January":1, "February":2, "March":3, "April":4, "May":5, "June":6, "July":7, "August":8, "September":9, "October":10, "November":11, "December":12 }
    [ day, month, year ] = str.split("-")

    if months.has_key(month):
        month = months[month]
    else:
        month = int(month)
    return datetime(int(year),month,int(day))

def getTextColorFromBackgroundColor(bgcolor):
    #Returns black if the average of the RGV values
    #is less than 128, and white if bigger.
    if len(bgcolor.strip())==7:# remove "#" before the color code
        bgcolor=bgcolor[1:]
    if len(bgcolor)==6:
        try:
            avg=int((int(bgcolor[0:2], 16)+int(bgcolor[2:4], 16)+int(bgcolor[4:6], 16))/3)
            if avg>128:
                return "#000000"
            else:
                return "#FFFFFF"
        except ValueError:
            pass
    return "#202020"


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

def validIP(ip):
    """
    Quick and dirty IP address validation
    (not exact, but enough)
    """
    expr = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    return re.match(expr, ip) != None


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


def dictionaryToString(dico):
    """ Convert the given dictionary to a string, which is returned.
        Useful for HTML attributes (e.g. name="a" value="x" ...).
    """
    #check params
    if not isinstance(dico, dict): return ""
    #converting
    attrString = " "
    for item in dico.items():
        if len(item)==2: #it should always be 2 (Better to prevent than to heal!)
            attrName= str(item[0])
            attrVal = str(item[1])
            attrVal = attrVal.replace('"', "'") #remove double quotes : " -> '
            attrString += """%s="%s" """%(attrName,attrVal)
    return attrString

def removeQuotes(myString):
    """encode/replace problematics quotes."""
    # XXX: why are we handling this one in a special way? there are more non-ascii quotes!
    # http://en.wikipedia.org/wiki/Quotation_mark#Unicode_code_point_table
    unicode_quote = u'\N{RIGHT SINGLE QUOTATION MARK}'.encode('utf-8')
    return str(myString).strip().replace('"', '&quot;').replace("'", '&rsquo;').replace(unicode_quote, '&rsquo;')


def putbackQuotes(myString):
    """cancel (almost all) effects of function removeQuotes()."""
    return str(myString).strip().replace("&quot;", '"').replace("&rsquo;", "'")


def nodeValue(node):
    """given a leaf node, returns its value."""
    from xml.dom.minidom import Element,Text
    if isinstance(node,Text):
        return node.data
    elif isinstance(node,Element) and node.firstChild!=None and isinstance(node.firstChild,Text):
        return node.firstChild.data.encode('utf-8')
    return ""

def _bool(val):
    """same as bool(), but returns False when you give "False"."""
    if str(val).strip() == "False" :
        return False
    else: return bool(val)

def _int(val):
    """same as int(), but returns 0 when you give "" or None."""
    if str(val).strip()=="" or val==None :
        val=0
    else:
        return int(val)

def _positiveInt(val):
    """same as _int(), but returns 0 when you give a negative int."""
    val = _int(val)
    if val<0:
        return 0
    else:
        return val

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


def parseDate(dateStr, format='%d/%m/%Y'):
    t=time.strptime(dateStr, format)
    return datetime(t.tm_year,t.tm_mon, t.tm_mday).date()

def prettyDuration(duration):
    """Return duration 01:05 in a pretty format 1h05'"""
    hours = duration.seconds/60/60
    minutes = duration.seconds/60%60
    if hours:
        return "%sh%s'" % (hours, minutes)
    else:
        return "%s'" % minutes

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


def parseDateTime(dateTimeStr):
    t=time.strptime(dateTimeStr, '%d/%m/%Y %H:%M')
    return datetime(t.tm_year,t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min)

def normalizeToList(l):
    if type(l) != list:
        l=[l]
    return l

def getHierarchicalId(obj):

    """
    Gets the ID of a Conference, Contribution or Subcontribution,
    in an hierarchical manner
    """

    if isinstance(obj, db.m.Contribution):
        return '{}.{}'.format(obj.event_new.id, obj.id)
    elif isinstance(obj, db.m.SubContribution):
        return '{}.{}.{}'.format(obj.event_new.id, obj.contribution.id, obj.id)
    elif isinstance(obj, db.m.Session):
        return '{}.s{}'.format(obj.event_new.id, obj.id)
    elif isinstance(obj, db.m.SessionBlock):
        return '{}.s{}.{}'.format(obj.event_new.id, obj.session.id, obj.id)
    return obj.id

def resolveHierarchicalId(objId):
    """
    Gets an object from its Id (unless it doesn't exist,
    in which case it returns None
    """

    from MaKaC.conference import ConferenceHolder

    m = re.match(r'(\w+)(?:\.(s?)(\w+))?(?:\.(\w+))?', objId)

    # If the expression doesn't match at all, return
    if not m or not m.groups()[0]:
        return None

    try:
        m = m.groups()
        conference = ConferenceHolder().getById(m[0])

        if m[1]:
            # session id specified - session or slot
            session = conference.getSessionById(m[2])

            if m[3]:
                # session slot: 1234.s12.1
                return session.getSlotById(m[3])
            else:
                # session: 1234.s12
                return session
        else:
            if m[2]:
                # second token is not a session id
                # (either contribution or subcontribution)

                contribution = conference.getContributionById(m[2])

                if m[3]:
                    # subcontribution: 1234.12.1
                    return contribution.getSubContributionById(m[3])
                else:
                    # contribution: 1234.12
                    return contribution
            else:
                # there's not second token
                # it's definitely a conference
                return conference

    except errors.MaKaCError:
        return None


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


def getProtectionText(target):
    # XXX: the only relevant return values are domain / not falsy
    from MaKaC.conference import Conference
    if isinstance(target, Conference):
        event = target.as_event
        if not event.is_protected:
            return '', None
        networks = [x.name for x in event.get_access_list() if x.is_network]
        if networks:
            return 'domain', networks
        else:
            return 'protected', None
    else:
        if target.hasAnyProtection():
            if target.isItselfProtected():
                return "protected_own", None
            elif target.hasProtectedOwner():
                return "protected_parent", None
            elif target.getDomainList() != []:
                return "domain", list(x.getName() for x in target.getDomainList())
            else:
                return getProtectionText(target.getOwner())
        return "", None
