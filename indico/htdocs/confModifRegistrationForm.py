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

import MaKaC.webinterface.rh.registrationFormModif as registrationFormModif


def index(req, **params):
    return registrationFormModif.RHRegistrationFormModif( req ).process( params )

def changeStatus(req, **params):
    return registrationFormModif.RHRegistrationFormModifChangeStatus( req ).process( params )

def dataModif(req, **params):
    return registrationFormModif.RHRegistrationFormModifDataModification( req ).process( params )

def performDataModif(req, **params):
    return registrationFormModif.RHRegistrationFormModifPerformDataModification( req ).process( params )

def modifSessions(req, **params):
    return registrationFormModif.RHRegistrationFormModifSessions( req ).process( params )

def modifSessionsData(req, **params):
    return registrationFormModif.RHRegistrationFormModifSessionsDataModif( req ).process( params )

def performModifSessionsData(req, **params):
    return registrationFormModif.RHRegistrationFormModifSessionsPerformDataModif( req ).process( params )

def addSession(req, **params):
    return registrationFormModif.RHRegistrationFormModifSessionsAdd( req ).process( params )

def performAddSession(req, **params):
    return registrationFormModif.RHRegistrationFormModifSessionsPerformAdd( req ).process( params )

def removeSession(req, **params):
    return registrationFormModif.RHRegistrationFormModifSessionsRemove( req ).process( params )

def modifAccommodation(req, **params):
    return registrationFormModif.RHRegistrationFormModifAccommodation( req ).process( params )

def modifAccommodationData(req, **params):
    return registrationFormModif.RHRegistrationFormModifAccommodationDataModif( req ).process( params )

def performModifAccommodationData(req, **params):
    return registrationFormModif.RHRegistrationFormModifAccommodationPerformDataModif( req ).process( params )

def removeAccommodationType(req, **params):
    return registrationFormModif.RHRegistrationFormModifAccommodationTypeRemove( req ).process( params )

def addAccommodationType(req, **params):
    return registrationFormModif.RHRegistrationFormModifAccommodationTypeAdd( req ).process( params )

def performAddAccommodationType(req, **params):
    return registrationFormModif.RHRegistrationFormModifAccommodationTypePerformAdd( req ).process( params )

def modifyAccommodationType(req, **params):
    return registrationFormModif.RHRegistrationFormAccommodationTypeModify( req ).process( params )

def performModifyAccommodationType(req, **params):
    return registrationFormModif.RHRegistrationFormAccommodationTypePerformModify( req ).process( params )

def modifFurtherInformation(req, **params):
    return registrationFormModif.RHRegistrationFormModifFurtherInformation( req ).process( params )

def modifFurtherInformationData(req, **params):
    return registrationFormModif.RHRegistrationFormModifFurtherInformationDataModif( req ).process( params )

def performModifFurtherInformationData(req, **params):
    return registrationFormModif.RHRegistrationFormModifFurtherInformationPerformDataModif( req ).process( params )

def modifReasonParticipation(req, **params):
    return registrationFormModif.RHRegistrationFormModifReasonParticipation( req ).process( params )

def modifReasonParticipationData(req, **params):
    return registrationFormModif.RHRegistrationFormModifReasonParticipationDataModif( req ).process( params )

def performModifReasonParticipationData(req, **params):
    return registrationFormModif.RHRegistrationFormModifReasonParticipationPerformDataModif( req ).process( params )

def modifSocialEvent(req, **params):
    return registrationFormModif.RHRegistrationFormModifSocialEvent( req ).process( params )

def modifSocialEventData(req, **params):
    return registrationFormModif.RHRegistrationFormModifSocialEventDataModif( req ).process( params )

def performModifSocialEventData(req, **params):
    return registrationFormModif.RHRegistrationFormModifSocialEventPerformDataModif( req ).process( params )

def removeSocialEvent(req, **params):
    return registrationFormModif.RHRegistrationFormModifSocialEventRemove( req ).process( params )

def addSocialEvent(req, **params):
    return registrationFormModif.RHRegistrationFormModifSocialEventAdd( req ).process( params )

def performAddSocialEvent(req, **params):
    return registrationFormModif.RHRegistrationFormModifSocialEventPerformAdd( req ).process( params )

def enableSection(req, **params):
    return registrationFormModif.RHRegistrationFormModifEnableSection( req ).process( params )

def enablePersonalField(req, **params):
    return registrationFormModif.RHRegistrationFormModifEnablePersonalField( req ).process( params )

def switchPersonalField(req, **params):
    return registrationFormModif.RHRegistrationFormModifSwitchPersonalField( req ).process( params )

def modifySocialEventItem(req, **params):
    return registrationFormModif.RHRegistrationFormSocialEventItemModify( req ).process( params )

def performModifySocialEventItem(req, **params):
    return registrationFormModif.RHRegistrationFormSocialEventItemPerformModify( req ).process( params )

def actionSection(req, **params):
    return registrationFormModif.RHRegistrationFormActionSection( req ).process( params )

def modifGeneralSection(req, **params):
    return registrationFormModif.RHRegistrationFormModifGeneralSection( req ).process( params )

def modifGeneralSectionData(req, **params):
    return registrationFormModif.RHRegistrationFormModifGeneralSectionDataModif( req ).process( params )

def performModifGeneralSectionData(req, **params):
    return registrationFormModif.RHRegistrationFormModifGeneralSectionPerformDataModif( req ).process( params )

def addGeneralField(req, **params):
    return registrationFormModif.RHRegistrationFormModifGeneralSectionFieldAdd( req ).process( params )

def performAddGeneralField(req, **params):
    return registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformAdd( req ).process( params )

def modifGeneralField(req, **params):
    return registrationFormModif.RHRegistrationFormModifGeneralSectionFieldModif( req ).process( params )

def performModifGeneralField(req, **params):
    return registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformModif( req ).process( params )

def removeGeneralField(req, **params):
    return registrationFormModif.RHRegistrationFormModifGeneralSectionFieldProcess( req ).process( params )

def actionStatuses(req, **params):
    return registrationFormModif.RHRegistrationFormActionStatuses( req ).process( params )

def modifStatus(req, **params):
    return registrationFormModif.RHRegistrationFormStatusModif( req ).process( params )

def performModifStatus(req, **params):
    return registrationFormModif.RHRegistrationFormModifStatusPerformModif( req ).process( params )
