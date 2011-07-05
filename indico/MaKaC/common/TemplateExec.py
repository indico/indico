# -*- coding: utf-8 -*-
##
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

"""Template engine."""

import os.path
from MaKaC.common.Configuration import Config
from MaKaC.common.utils import formatDateTime, formatDate, formatTime
from MaKaC.user import Avatar
from mako.lookup import TemplateLookup
import MaKaC
import MaKaC.common.info as info
import xml.sax.saxutils


# The main template directory
TEMPLATE_DIR = Config.getInstance().getTPLDir()

# Directory for storing compiled Mako templates
COMPILED_MODULES = os.path.join(Config.getInstance().getTempDir(), "mako_modules")

mako = TemplateLookup(directories=["/"],
                      module_directory=COMPILED_MODULES,
                      disable_unicode=True,
                      filesystem_checks=True)


def render(tplPath, params):
    """Render the template."""
    template = mako.get_template(tplPath)
    registerHelpers(params)

    # This parameter is needed when a template which is stored
    # outside of the main tpls directory (e.g. plugins) wants
    # to include another template from the main directory.
    # Usage example: <%include file="${TPLS}/SomeTemplate.tpl"/>
    params["TPLS"] = TEMPLATE_DIR

    return template.render(**params)


def inlineContextHelp(helpContent):
    """
    Allows you to put [?], the context help marker.
    Help content passed as argument helpContent.
    """
    from MaKaC.webinterface.wcomponents import WTemplated
    params = {"helpContent" : helpContent,
              "imgSrc" : Config.getInstance().getSystemIconURL("help")}
    return WTemplated('InlineContextHelp').getHTML(params)


def contextHelp(helpId):
    """
    Allows you to put [?], the context help marker.
    Help content is defined in <div id="helpId"></div>.
    """
    from MaKaC.webinterface.wcomponents import WTemplated
    params = {"helpId" : helpId,
              "imgSrc" : Config.getInstance().getSystemIconURL("help")}
    return WTemplated('ContextHelp').getHTML(params)


def escapeAttrVal(s):
    """Just escapes the apostrophes, new lines, etc."""
#    if s == None:
#        return None
#    s = s.replace("'", r"\'")
#    s = s.strip()
    s = xml.sax.saxutils.quoteattr(s)[1:-1]
    s = s.replace("'", "`")
    s = s.replace("\"", "`")
    s = s.replace("\n", "")
    s = s.replace("\r", "")
    s = s.replace("&#13;", " ")
    s = s.replace("&#10;", " ")
    return s


def verbose(s, default=""):
    """
    Purpose: avoid showing "None" to user; show default value instead.
    """
    if isinstance(s, bool) and s != None:
        if s:
            return "yes"
        else:
            return "no"
    return s or default


def verbose_dt(dt, default=""):
    """Return verbose date representation."""
    if dt == None:
        return default
    return ("%s_%2s:%2s" % (formatDate(dt.date()).replace(' ', '_'),
                            dt.hour,
                            dt.minute)).replace(' ', '0').replace('_', ' ')


def verbose_t(t, default=""):
    """Return verbose time representation."""
    if t == None:
        return default
    return ("%2d:%2d" % (t.hour, t.minute)).replace(' ', '0')


def escape(s):
    """HTML escape"""
    return xml.sax.saxutils.escape(s)


def jsBoolean(b):
    """Return Javascript version of a boolean value."""
    if b:
        return 'true'
    else:
        return 'false'


def quoteattr(s):
    """quotes escape"""
    return xml.sax.saxutils.quoteattr(s)


def roomClass(room):
    if room.isReservable:
        roomCls = "basicRoom"
    if not room.isReservable:
        roomCls = "privateRoom"
    if room.isReservable and room.resvsNeedConfirmation:
        roomCls = "moderatedRoom"
    return roomCls


def dequote(s):
    """Remove surrounding quotes from a string (if there are any)."""
    if ((s.startswith('"') or s.startswith("'"))
            and (s.endswith('"') or s.endswith("'"))):
        return s[1:-1]
    return s


def linkify(s):
    urlIxStart = s.find('http://')
    if urlIxStart == -1:
        return s
    urlIxEnd = s.find(' ', urlIxStart + 1)
    s = (s[0:urlIxStart] + '<a href="' + s[urlIxStart:urlIxEnd] + '">'
            + s[urlIxStart:urlIxEnd] + "</a> " + s[urlIxEnd:])
    return s


def deepstr(obj):
    """ obj is any kind of object
        This method will loop through the object and turn objects into
        strings through their __str__ method. If a list or a dictionary
        is found during the loop, a recursive call is made. However this
        method does not support objects that are not lists or dictionaries.
        Author: David Martin Clavo
    """

    # stringfy objects inside a list
    if isinstance(obj, list):
        for i in range(0, len(obj)):
            obj[i] = deepstr(obj[i])

    #stringfy objects inside a dictionary
    if isinstance(obj, dict):
        for k, v in obj.items():
            del obj[k] #wAvatare delete the old key
            obj[deepstr(k)] = deepstr(v)

    return str(obj)

def beautify(obj, classNames={"UlClassName": "optionList",
                              "KeyClassName": "optionKey"}, level=0):
    """ Turns list or dicts into beautiful <ul> HTML lists, recursively.
        -obj: an object that can be a list, a dict, with lists or dicts inside
        -classNames: a dictionary specifying class names. Example:
            {"UlClassName": "optionList", "KeyClassName": "optionKey"}
        supported types are: UlClassName, LiClassName, DivClassName, KeyClassName
        See BeautifulHTMLList.tpl and BeautifulHTMLDict.tpl to see how they are used.
        In the CSS file, you should define classes like: ul.optionList1, ul.optionList2, ul.optionKey1 (the number is the level of recursivity)
        -level: the level of recursivity.
    """
    from MaKaC.webinterface import wcomponents
    if isinstance(obj, list):
        return wcomponents.WBeautifulHTMLList(obj, classNames, level + 1).getHTML()
    elif isinstance(obj, dict):
        return wcomponents.WBeautifulHTMLDict(obj, classNames, level + 1).getHTML()
    elif isinstance(obj, Avatar):
        return obj.getStraightFullName()
    else:
        return str(obj)

def systemIcon(s):
    return Config.getInstance().getSystemIconURL(s)

def iconFileName(s):
    return Config.getInstance().getSystemIconFileName(s)

def truncateTitle(title, maxSize=30):
    if len(title) > maxSize:
        return title[:maxSize] + '...'
    else:
        return title

def escapeHTMLForJS(s):
    """ Replaces some restricted characters in JS strings.
        \ -> \\
        ' -> \'
        " -> \"
        & -> \&
        / -> \/
        (line jump) -> \n
        (tab) -> \t
        (carriage return) -> \r
        (backspace) -> \b
        (form feed) -> \f

        TODO: try to optimize this (or check if it's optimum already).
        translate() doesn't work, because we are replacing characters by couples of characters.
        explore use of regular expressions, or maybe split the string and then join it manually, or just replace them by
        looping through the string and using an if...elif... etc.
    """
    res = s.replace("\\", "\\\\").replace("\'", "\\\'").replace("\"", "\\\"").replace("&", "\\&").replace("/", "\\/").replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r").replace("\b", "\\b").replace("\f", "\\f")
    return res

def registerHelpers(objDict):
    """
    Adds helper methods to the dictionary.
    Does it only if symbol does not exist - backward compatibility.
    """
    if not 'contextHelp' in objDict:
        objDict['contextHelp'] = contextHelp
    if not 'inlineContextHelp' in objDict:
        objDict['inlineContextHelp'] = inlineContextHelp
    if not 'escapeAttrVal' in objDict:
        objDict['escapeAttrVal'] = escapeAttrVal
    if not 'escape' in objDict:
        objDict['escape'] = escape
    if not 'quoteattr' in objDict:
        objDict['quoteattr'] = quoteattr
    if not 'verbose' in objDict:
        objDict['verbose'] = verbose
    if not 'verbose_dt' in objDict:
        objDict['verbose_dt'] = verbose_dt
    if not 'verbose_t' in objDict:
        objDict['verbose_t'] = verbose_t
    if not 'dequote' in objDict:
        objDict['dequote'] = dequote
    if not 'formatTime' in objDict:
        objDict['formatTime'] = formatTime
    if not 'formatDate' in objDict:
        objDict['formatDate'] = formatDate
    if not 'systemIcon' in objDict:
        objDict['systemIcon'] = systemIcon
    if not 'formatDateTime' in objDict:
        objDict['formatDateTime'] = formatDateTime
    if not 'linkify' in objDict:
        objDict['linkify'] = linkify
    if not 'truncateTitle' in objDict:
        objDict['truncateTitle'] = truncateTitle
    if not 'urlHandlers' in objDict:
        objDict['urlHandlers'] = MaKaC.webinterface.urlHandlers
    if not 'Config' in objDict:
        objDict['Config'] = MaKaC.common.Configuration.Config
    if not 'jsBoolean' in objDict:
        objDict['jsBoolean'] = jsBoolean
    if not 'offlineRequest' in objDict:
        from MaKaC.services.interface.rpc.offline import offlineRequest
        objDict['offlineRequest'] = offlineRequest
    if not 'jsonDescriptor' in objDict:
        from MaKaC.services.interface.rpc.offline import jsonDescriptor
        objDict['jsonDescriptor'] = jsonDescriptor
    if not 'jsonDescriptorType' in objDict:
        from MaKaC.services.interface.rpc.offline import jsonDescriptorType
        objDict['jsonDescriptorType'] = jsonDescriptorType
    if not 'jsonEncode' in objDict:
        from MaKaC.services.interface.rpc.json import encode as jsonEncode
        objDict['jsonEncode'] = jsonEncode
    if not 'roomInfo' in objDict:
        from MaKaC.services.interface.rpc.offline import roomInfo
        objDict['roomInfo'] = roomInfo
    if not 'macros' in objDict:
        from MaKaC.webinterface.asyndico import macros
        objDict['macros'] = macros
    if not 'roomBookingActive' in objDict:
        try:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            objDict['roomBookingActive'] = minfo.getRoomBookingModuleActive()
        except:
            # if the connection to the database is not started, there is no need to set the variable and
            # we avoid an error report.
            # THIS IS NEEDED, when using JSContent. JSContent does not need connection to the database
            # and this is causing an unexpected exception.
            pass
    if not 'user' in objDict:
        if not '__rh__' in objDict or not objDict['__rh__']:
            objDict['user'] = "ERROR: Assign self._rh = rh in your WTemplated.__init__( self, rh ) method."
        else:
            objDict['user'] = objDict['__rh__']._getUser()  # The '__rh__' is set by framework
    if not 'rh' in objDict:
        objDict['rh'] = objDict['__rh__']
    if not roomClass in objDict:
        objDict['roomClass'] = roomClass
    if not 'systemIcon' in objDict:
        objDict['systemIcon'] = systemIcon
    if not 'iconFileName' in objDict:
        objDict['iconFileName'] = iconFileName
    if not 'escapeHTMLForJS' in objDict:
        objDict['escapeHTMLForJS'] = escapeHTMLForJS
    if not 'deepstr' in objDict:
        objDict['deepstr'] = deepstr
    if not 'beautify' in objDict:
        objDict['beautify'] = beautify
    # allow fossilization
    if not 'fossilize' in objDict:
        from MaKaC.common.fossilize import fossilize
        objDict['fossilize'] = fossilize
