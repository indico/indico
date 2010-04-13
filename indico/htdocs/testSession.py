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

import session
session = reload(session)

import pickle

def askUserName():
    text = """
            <html>
                <head>
                    <title>Session test</title>
                </head>
                <body>
                    <form action="http://cdsdev.cern.ch/MaKaC/testSession.py">
                        I don't know you, please tell me your crazy name 
                        <input type="text" name="userName">
                        <input type="submit">
                    </form>
                </body>
            </html>
           """
    return text

def showUserName(userName, times):
    text = """
            <html>
                <head>
                    <title>Session test</title>
                </head>
                <body>
                    <form action="http://cdsdev.cern.ch/MaKaC/testSession.py">
                        Ahhh!! Welcome %s!! During this session you have visited this page %i times<br>
                        You can <input type="submit" value="logout" name="logout">
                    </form>
                </body>
            </html>
           """%(userName, times)
    return text

def index(req, userName=None, logout=None):
    try:
        pfh = open("/tmp/SM2.makac", "r")
    except IOError, e:
        SM = session.MPSessionManager()
    else:
        SM=pickle.load(pfh)
        pfh.close()
    if not SM.has_session_cookie( req, 1 ):
        if userName == None:
            return askUserName()
    s = SM.get_session( req )
    if logout!=None:
        SM.expire_session(req)
    else:
        try:
            s.times += 1
        except AttributeError, e:
            s.user = userName
            s.times = 0
        SM.maintain_session( req, s )
    pfh = open("/tmp/SM2.makac", "w")
    pickle.dump( SM, pfh )
    pfh.close()
    if logout!=None:
        return "I don't know you anymore"
    return showUserName(s.user, s.times)   
