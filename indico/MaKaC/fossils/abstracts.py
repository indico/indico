# -*- coding: utf-8 -*-
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

from MaKaC.common.fossilize import IFossil


class IAuthorFossil(IFossil):

    def getTitle(self):
        """ Author title (Mr, Mrs..) """

    def getId(self):
        """ Author id """

    def getFirstName(self):
        """ Author first name """

    def getFamilyName(self):
        """ Author family name """

    def getAffiliation(self):
        """ Author affiliation """

    def getEmail(self):
        """ Author email """

    def getPhone(self):
        """ Author phone """

    def isSpeaker(self):
        """ Author is speaker """


class IAbstractFieldFossil(IFossil):

    def getCaption(self):
        """ Caption of the field """

    def getId(self):
        """ ID of the field """

    def isMandatory(self):
        """ True if mandatory """


class IAbstractTextFieldFossil(IAbstractFieldFossil):

    def getMaxLength(self):
        """ Maximum length of the field """

    def getLimitation(self):
        """ Type of limitation """


class ISelectionFieldOptionFossil(IFossil):

    def getId(self):
        """ ID of the option """

    def getValue(self):
        """ Value of the option """

    def isDeleted(self):
        """ True if option has been deleted """


class IAbstractSelectionFieldFossil(IAbstractFieldFossil):

    def getOptions(self):
        """ Options for selection """
    getOptions.result = ISelectionFieldOptionFossil
