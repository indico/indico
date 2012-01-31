# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import MaKaC.webinterface.rh.taskList as taskList


def index(req, **params):
    return taskList.RHTaskList( req ).process( params )

def taskListAction(req, **params):
    return taskList.RHTaskListAction( req ).process( params )

def newTask(req, **params):
    return taskList.RHTaskNew( req ).process( params )

def addNewTask(req, **params):
    return taskList.RHTaskNewAdd( req ).process( params )

def taskDetails(req, **params):
    return taskList.RHTaskDetails( req ).process( params )
    
def taskDetailsAction(req, **params):
    return taskList.RHTaskDetailsAction( req ).process( params )

def commentNew(req, **params):
    return taskList.RHTaskCommentNew( req ).process( params )

def commentNewAction(req, **params):
    return taskList.RHTaskCommentNewAction( req ).process( params )

def searchResponsible(req, **params):
    return taskList.RHTaskNewResponsibleSearch( req ).process( params )

def newResponsible(req, **params):
    return taskList.RHTaskNewResponsibleNew( req ).process( params )

def personAdd(req, **params):
    return taskList.RHTaskNewPersonAdd( req ).process( params )

def detailSearchResponsible(req, **params):
    return taskList.RHTaskDetailsResponsibleSearch( req ).process( params )

def detailNewResponsible(req, **params):
    return taskList.RHTaskDetailsResponsibleNew( req ).process( params )

def detailPersonAdd(req, **params):
    return taskList.RHTaskDetailsPersonAdd( req ).process( params )
    