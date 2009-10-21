# -*- coding: utf-8 -*-
##
## $Id: utils.py,v 1.45 2009/06/29 12:29:58 jose Exp $
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from random import randint
from datetime import datetime, date, timedelta
import time
from MaKaC import user
import re
from MaKaC.i18n import _
import sys
import os



###########
#CONSTANTS#
###########
_KEY_DEFAULT_LENGTH = 20
_FAKENAME_SIZEMIN = 5
_FAKENAME_SIZEMAX = 10



###########
#functions#
###########

from MaKaC.common.db import DBMgr
from BTrees.OOBTree import OOBTree


def isWeekend( d ):
    """
    Accepts date or datetime object.
    """
    return d.weekday() in [5, 6]


HOLIDAYS_KEY = 'Holidays'
class HolidaysHolder:

    @classmethod
    def isWorkingDay( cls, d ):
        if isinstance( d, datetime ):
            d = d.date()
        if isWeekend( d ):
            return False
        return not cls.__getBranch().has_key( d )

    @classmethod
    def getHolidays( cls ):
        """
        Returns list of holidays
        """
        return cls.__getBranch().keys()

    @classmethod
    def insertHoliday( cls, d ):
        cls.__getBranch()[d] = None

    @classmethod
    def clearHolidays( cls ):
        root = DBMgr.getInstance().getDBConnection().root()
        root[HOLIDAYS_KEY] = OOBTree()

    @staticmethod
    def __getBranch():
        root = DBMgr.getInstance().getDBConnection().root()
        if not root.has_key( HOLIDAYS_KEY ):
            root[HOLIDAYS_KEY] = OOBTree()
        return root[HOLIDAYS_KEY]


def stringToDate( str ):
    months = { "January":1, "February":2, "March":3, "April":4, "May":5, "June":6, "July":7, "August":8, "September":9, "October":10, "November":11, "December":12 }
    [ day, month, year ] = str.split("-")

    return datetime(int(year),months[month],int(day))

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

charRplace = [
[u'\u2019', u"'"],
[u'\u0153', u"oe"],
[u'\u2026', u"..."],
[u'\u2013', u"-"],
[u'\u2018', u"'"]
]

def utf8Tolatin1(text):
    t = text.decode("utf8")
    for i in charRplace:
        t = t.replace(i[0], i[1])
    return t.encode("latin1",'replace')

def utf8rep(text):
    # \x -> _x keeps windows systems satisfied
    return text.decode('utf-8').encode('unicode_escape').replace('\\x','_x')

def sortUsersByName(x,y):
    return cmp(x.getFamilyName().lower(),y.getFamilyName().lower())

def sortUsersByFirstName(x,y):
    return cmp(x.getFirstName().lower(),y.getFirstName().lower())

def sortUsersByAffiliation(x,y):
    return cmp(x.getAffiliation().lower(),y.getAffiliation().lower())

def sortUsersByEmail(x,y):
    return cmp(x.getEmail().lower(),y.getEmail().lower())

def sortGroupsByName(x,y):
    return cmp(x.getName().lower(),y.getName().lower())

def sortDomainsByName(x,y):
    return cmp(x.getName().lower(),y.getName().lower())

def sortFilesByName(x,y):
    return cmp(x.getName().lower(),y.getName().lower())

def sortContributionByDate(x,y):
    return cmp(x.getStartDate(),y.getStartDate())

def sortSlotByDate(x,y):
    return cmp(x.getStartDate(),y.getStartDate())

def sortCategoryByTitle(x,y):
    return cmp(x.getTitle(),y.getTitle())

def sortPrincipalsByName(x,y):
    firstNamex, firstNamey = "", ""
    if x is None:
        namex = ""
    elif isinstance(x, user.CERNGroup) or isinstance(x, user.Group):
        namex = x.getName()
    else:
        namex = x.getFamilyName()
        firstNamex = x.getFirstName()

    if y is None:
        namey = ""
    elif isinstance(y, user.CERNGroup) or isinstance(y, user.Group):
        namey = y.getName()
    else:
        namey = y.getFamilyName()
        firstNamey = y.getFirstName()

    cmpRes = cmp(namex.lower(),namey.lower())
    if cmpRes == 0:
        cmpRes = cmp(firstNamex.lower(),firstNamey.lower())
    return cmpRes

def validMail(email):
    if re.search("^[a-zA-Z][\w\.-]*[a-zA-Z0-9]@[a-zA-Z0-9][\w\.-]*[a-zA-Z0-9]\.[a-zA-Z][a-zA-Z\.]*[a-zA-Z]$",email):
        return True
    return False

def validIP(ip):
    """
    Quick and dirty IP address validation
    (not exact, but enough)
    """
    expr = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    return re.match(expr, ip) != None


def isStringHTML(s):
    if type(s) == str:
        tags = [ "<p>", "<p ", "<br>" ]
        for tag in tags:
            if s.lower().find(tag) != -1:
                return True
    return False

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

def dictionaryToTupleList(dic):
    return [(k,v) for (k,v) in dic.iteritems()]

def removeQuotes(myString):
    """encode/replace problematics quotes."""
    #Note: Use &rsquo; because &apos; can be problematic with context help!!!
    #Note: \xe2\x80\x99 = ďż˝
    return str(myString).strip().replace('"', "&quot;").replace("'", "&rsquo;").replace("$-1������", "&rsquo;").replace("\xe2\x80\x99", "&rsquo;")

def putbackQuotes(myString):
    """cancel (almost all) effects of function removeQuotes()."""
    return str(myString).strip().replace("&quot;", '"').replace("&rsquo;", "'")

def newFakeName(minSize=_FAKENAME_SIZEMIN, maxSize=_FAKENAME_SIZEMAX):
    """Give randomly a fake name. Useful when we want to make people anonymous..."""
    #check
    try:
        minSize = int(minSize)
    except:
        minSize = _FAKENAME_SIZEMIN
    try:
        maxSize = int(maxSize)
    except:
        maxSize = _FAKENAME_SIZEMAX
    #next
    length = randint(minSize,maxSize)
    uppers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    vowels = "aeiouy"
    consonants = "bcdfghjklmnpqrstvwxz"
    upperIndexMax = len(uppers)-1
    vowelIndexMax = len(vowels)-1
    consonantIndexMax = len(consonants)-1
    #first capital letter
    fakename = uppers[ randint(0,upperIndexMax) ]
    #following lowercase letters
    isVowel = fakename.lower() in vowels
    for i in range(1, length):
        if isVowel:
            fakename += consonants[ randint(0,consonantIndexMax) ]
            isVowel = False
        else:
            fakename += vowels[ randint(0,vowelIndexMax) ]
            isVowel = True
    return fakename


def newKey(length=_KEY_DEFAULT_LENGTH):
    """returns a new crypted key of given length."""
    #check
    try:
        length = int(length)
    except:
        length = _KEY_DEFAULT_LENGTH
    #next
    table = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    key = ""
    indexMax = len(table)-1
    for i in range(length):
        key += table[ randint(0,indexMax) ]
    return key

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

def _negativeInt(val):
    """same as _int(), but returns 0 when you give a positive int."""
    val = _int(val)
    if val>0:
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


def daysBetween(dtStart, dtEnd):
    d = dtEnd - dtStart
    days = [ dtStart + timedelta(n) for n in range(0, d.days + 1)]
    if days[-1] != dtEnd:
        # handles special case, when d.days is the
        # actual span minus 2
        # |----|----|----|----|
        # (4 days)
        #    |----|----|---
        # (2 days and some hours)
        days.append(dtEnd)

    return days

def formatDateTime(dateTime, showWeek=False, format=None):
    week = ""
    if showWeek:
        week = "%a "
    if not format:
        return datetime.strftime(dateTime, week+'%d/%m/%Y %H:%M')
    else:
        return datetime.strftime(dateTime, format)

def formatDate(date, showWeek=False, format=None):
    week = ""
    if showWeek:
        week = "%a "
    if not format:
        return datetime.strftime(date, week+'%d/%m/%Y')
    else:
        return datetime.strftime(date, format)

def formatTime(time):
    return time.strftime('%H:%M')

def parseDate(dateStr):
    t=time.strptime(dateStr, '%d/%m/%Y')
    return datetime(t.tm_year,t.tm_mon, t.tm_mday).date()

def parseTime(timeStr):
    t=time.strptime(timeStr, '%H:%M')
    return datetime(t.tm_year,t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min).time()

def parseDateTime(dateTimeStr):
    t=time.strptime(dateTimeStr, '%d/%m/%Y %H:%M')
    return datetime(t.tm_year,t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min)

def cleanUnicodeObjects(obj):
    """ obj must be a list or a dictionary
        This method will loop through the object and change unicode objects into str objects encoded in utf-8.
        If a list or a dictionary is found during the loop, a recursive call is made.
        However this method does not support objects that are not lists or dictionaries.
        This method is useful to turn unicode objects from the output object given by simplejson.loads(),
        into str objects encoded in utf-8.
        In case of a persistent object or an object inside a persistent object,
        you will need to notify the database of changes in the object after calling this method.
    """

    # replace unicode objects inside a list
    if isinstance(obj,list):
        for i in range(0, len(obj)):
            if type(obj[i]) == unicode:
                obj[i] = obj[i].encode('utf-8','replace')
            else:
                cleanUnicodeObjects(obj[i])

    #replace unicode objects inside a dictionary
    if isinstance(obj,dict):
        #replace values
        for k,v in obj.items():
            if type(v) == unicode:
                obj[k] = v.encode('utf-8','replace')
            else:
                cleanUnicodeObjects(obj[k])

        #replace keys
        dict2 = obj.copy()
        for k in dict2.keys():
            if type(k) == unicode:
                del obj[k]
                obj[k.encode('utf-8','replace')] = dict2[k]
            else:
                cleanUnicodeObjects(k)

def normalizeToList(l):
    if type(l) != list:
        l=[l]
    return l

def getHierarchicalId(obj):

    """ Gets the ID of a Conference, Contribution or Subcontribution, in an hierarchical manner"""

    from MaKaC import conference

    ret = obj.getId()
    if isinstance(obj,conference.Contribution):
        ret="%s.%s"%(obj.getConference().getId(),ret)
    elif isinstance(obj, conference.SubContribution):
        ret="%s.%s.%s"%(obj.getConference().getId(), obj.getContribution().getId(), ret)
    elif isinstance(obj, conference.DeletedObject):
        ret=obj.getId().replace(':','.')
    elif isinstance(obj, conference.Session):
        ret="%s.s%s"%(obj.getConference().getId(), ret)
    elif isinstance(obj, conference.SessionSlot):
        ret="%s.s%s.%s"%(obj.getConference().getId(), obj.getSession().getId(), ret)
    return ret

def main():
    DBMgr.getInstance().startRequest()
    print _("Is working day: ")
    print str( HolidaysHolder.isWorkingDay( date( 2007, 5, 1 ) ) )
    print str( HolidaysHolder.isWorkingDay( date( 2007, 5, 2 ) ) )
    print str( HolidaysHolder.isWorkingDay( date( 2007, 9, 5 ) ) )

    h = HolidaysHolder.getHolidays()
    for day in h:
        if day.year == 2007:
            print day

    DBMgr.getInstance().endRequest()

if __name__ == '__main__':
    main()
