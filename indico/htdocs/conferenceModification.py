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

# The following is a (failed) trial to reload modules
# for each request, so you do not have to restart apache.
# Pitty.

#import sys
#oryginalModules = sys.modules.copy()

#import __builtin__
#class RollbackImporter:
#
#    def __init__(self):
#        "Creates an instance and installs as the global importer"
#
#        self.previousModules = sys.modules.copy()
#        self.realImport = __builtin__.__import__
#        __builtin__.__import__ = self._import
#        self.newModules = {}
#
#    def _import(self, name, globals=None, locals=None, fromlist=[]):
#        result = apply(self.realImport, (name, globals, locals, fromlist))
#        self.newModules[name] = 1
#        return result
#
#    def uninstall(self):
#        for modname in self.newModules.keys():
#            if not self.previousModules.has_key(modname):
#                # Force reload when modname next imported
#                del(sys.modules[modname])
#
#        __builtin__.__import__ = self.realImport

#rollbackImporter = RollbackImporter()

from MaKaC.webinterface.rh import conferenceModif

def index(req, **params):
    return conferenceModif.RHConferenceModification( req ).process( params )

def data( req, **params ):
    return conferenceModif.RHConfDataModif( req ).process( params )

def screenDates( req, **params ):
    return conferenceModif.RHConfScreenDatesEdit( req ).process( params )

def dataPerform( req, **params ):
    return conferenceModif.RHConfPerformDataModif( req ).process( params )

def sessionSlots( req, **params ):
    return conferenceModif.RHConfSessionSlots( req ).process( params )

def addContribType( req, **params ):
    return conferenceModif.RHConfAddContribType( req ).process( params )

def removeContribType( req, **params ):
    return conferenceModif.RHConfRemoveContribType( req ).process( params )

def editContribType( req, **params ):
    return conferenceModif.RHConfEditContribType( req ).process( params )

def managementAccess( req, **params ):
    return conferenceModif.RHConferenceModifManagementAccess( req ). process( params)

def modifKey(req, **params):
    return conferenceModif.RHConferenceModifKey(req).process(params)

def closeModifKey(req, **params):
    return conferenceModif.RHConferenceCloseModifKey(req).process(params)

def close(req, **params):
    return conferenceModif.RHConferenceClose(req).process(params)

def open(req, **params):
    return conferenceModif.RHConferenceOpen(req).process(params)

def modificationClosed(req, **params):
    return conferenceModif.RHConferenceModificationClosed(req).process(params)

def sectionsSettings(req, **params):
    return conferenceModif.RHConfSectionsSettings(req).process(params)

def materialsAdd(req, **params):
    return conferenceModif.RHMaterialsAdd(req).process(params)

def materialsShow(req, **params):
    return conferenceModif.RHMaterialsShow(req).process(params)


# ============================================================================
# === Room booking related ===================================================
# ============================================================================

# 0. Searching
def roomBookingChooseEvent( req, **params ):
    return conferenceModif.RHConfModifRoomBookingChooseEvent( req ).process(params)

# 1. Searching
def roomBookingSearch4Rooms( req, **params ):
    return conferenceModif.RHConfModifRoomBookingSearch4Rooms( req ).process(params)

# 2. List of...
def roomBookingRoomList( req, **params ):
    return conferenceModif.RHConfModifRoomBookingRoomList( req ).process( params )

def roomBookingList( req, **params ):
    r = conferenceModif.RHConfModifRoomBookingList(req).process(params)
    return r

# 3. Details of...
def roomBookingRoomDetails( req, **params ):
    return conferenceModif.RHConfModifRoomBookingRoomDetails( req ).process( params )

def roomBookingDetails( req, **params ):
    return conferenceModif.RHConfModifRoomBookingDetails(req).process(params)

# 4. New booking: form
def roomBookingBookingForm( req, **params ):
    return conferenceModif.RHConfModifRoomBookingBookingForm(req).process(params)
def roomBookingCloneBooking( req, **params ):
    return conferenceModif.RHConfModifRoomBookingCloneBooking(req).process(params)

# 4. New booking: physical insert
def roomBookingSaveBooking( req, **params ):
#    import wingdbstub
#    if wingdbstub.debugger != None:
#        wingdbstub.debugger.StartDebug()
    return conferenceModif.RHConfModifRoomBookingSaveBooking(req).process(params)

roomBookingChooseEvent
