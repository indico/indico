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

from MaKaC.common import Config
from MaKaC.common.utils import encodeUnicode

from MaKaC.errors import MaKaCError, htmlScriptError, htmlForbiddenTag
from MaKaC.webinterface.common.tools import scriptDetection, escape_html, restrictedHTML

"""
base module for HTML security
"""

def sanitizationCheck(target, params, accessWrapper):
    # first make sure all params are utf-8
    for param in params.keys():
        if isinstance(params[param], str) and params[param] != "":
            params[param] = encodeUnicode(params[param])
            if params[param] == "":
                raise MaKaCError("Your browser is using an encoding which is not recognized by Indico... Please make sure you set your browser encoding to utf-8")
        elif isinstance(params[param], list):
            #the params is a list, check inside
            for i in range(len(params[param])):
                item = params[param][i]
                if isinstance(item, str) and item != "":
                    params[param][i] = encodeUnicode(item)
                    if params[param][i] == "":
                        raise MaKaCError("Your browser is using an encoding which is not recognized by Indico... Please make sure you set your browser encoding to utf-8")


    # then check the security level of data sent to the server
    # if no user logged in, then no html allowed
    if accessWrapper.getUser():
        level = Config.getInstance().getSanitizationLevel()
    elif target and hasattr(target, "canModify") and target.canModify(accessWrapper):
        # not logged user, but use a modification key
        level = Config.getInstance().getSanitizationLevel()
    else:
        level = 0

    if level not in range(4):
        level = 1

    if level == 0:
        #Escape all HTML tags
        for param in params.keys():
            if isinstance(params[param], str):
                #the params is a string
                params[param] = escape_html(params[param])
            elif isinstance(params[param], list):
                #the params is a list, check inside
                for i in range(len(params[param])):
                    item = params[param][i]
                    if isinstance(item, str):
                        params[param][i] = escape_html(item)

    # raise error if form or iframe tags are used
    elif level == 1:
        #level 1 or default
        #raise error if script or style detected
        ret = None
        for param in params.keys():
            if isinstance(params[param], str):
                ret = scriptDetection(params[param])
                if not restrictedHTML(params[param]):
                    raise htmlForbiddenTag(params[param])
            elif isinstance(params[param], list):
                for item in params[param]:
                    if isinstance(item, str):
                        ret = scriptDetection(item)
                        if ret:
                            raise htmlScriptError(item)
                        if not restrictedHTML(item):
                            raise htmlForbiddenTag(item)
            if ret:
                raise htmlScriptError(params[param])

    elif level == 2:
        #raise error if script but style accepted
        ret = None
        for param in params.keys():
            if isinstance(params[param], str):
                ret = scriptDetection(params[param], allowStyle=True)
                if ret:
                    raise htmlScriptError(params[param])
                ret = restrictedHTML(params[param])
                if not ret:
                    raise htmlForbiddenTag(params[param])
            elif isinstance(params[param], list):
                for item in params[param]:
                    if isinstance(item, str):
                        ret = scriptDetection(item, allowStyle=True)
                        if ret:
                            raise htmlScriptError(item)
                        ret = restrictedHTML(item)
                        if not ret:
                            raise htmlForbiddenTag(item)


    elif level == 3:
        # Absolutely no checks
        return