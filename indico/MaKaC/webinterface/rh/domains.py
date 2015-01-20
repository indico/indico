# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.domain as domain
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.errors as errors
import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.rh.admins as admins
from MaKaC.webinterface.rh.base import RHProtected


class RHDomainProtected( admins.RHAdminBase):
    pass

class RHDomains( RHDomainProtected ):
    _uh = urlHandlers.UHDomains

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPDomainList( self, self._params )
        return p.display()


class RHDomainBase( RHDomainProtected ):

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._domain = locators.DomainWebLocator( params ).getObject()


class RHDomainDetails( RHDomainBase ):
    _uh = urlHandlers.UHDomainDetails

    def _process( self ):
        p = adminPages.WPDomainDetails( self, self._domain )
        return p.display()


class RHDomainModification( RHDomainBase ):
    _uh = urlHandlers.UHDomainModification

    def _process( self ):
        p = adminPages.WPDomainModification( self, self._domain )
        return p.display()


class _DomainUtils:

    def setDomainValues( domain, domainData ):
        domain.setName(domainData["name"])
        domain.setDescription(domainData["description"])
        domain.setFiltersFromStr(domainData["filters"])
    setDomainValues = staticmethod( setDomainValues )


class RHDomainPerformModification( RHDomainBase ):
    _uh = urlHandlers.UHDomainPerformModification

    def _process( self ):
        _DomainUtils.setDomainValues( self._domain, self._getRequestParams() )
        self._redirect( urlHandlers.UHDomainDetails.getURL( self._domain ) )


class RHDomainCreation( RHDomainProtected ):
    _uh = urlHandlers.UHNewDomain

    def _process( self ):
        p = adminPages.WPDomainCreation( self )
        return p.display()


class RHDomainPerformCreation( RHDomainProtected ):
    _uh = urlHandlers.UHDomainPerformCreation

    def _process( self ):
        d = domain.Domain()
        _DomainUtils.setDomainValues( d, self._getRequestParams() )
        if d.getName() != "":
            dh = domain.DomainHolder()
            dh.add( d )
            self._redirect( urlHandlers.UHDomainDetails.getURL( d ) )
        else:
            self._redirect( urlHandlers.UHDomains.getURL() )






