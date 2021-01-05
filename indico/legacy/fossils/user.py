# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.util.fossilize import IFossil


class IGroupFossil(IFossil):

    def getId(self):
        """ Group id """

    def getName(self):
        """ Group name """

    def getEmail(self):
        """ Group email """

    def getProvider(self):
        pass
    getProvider.produce = lambda x: getattr(x, 'provider', None)

    def getIdentifier(self):
        pass
    getIdentifier.produce = lambda x: 'Group:{}:{}'.format(getattr(x, 'provider', ''), x.id)


class IAvatarMinimalFossil(IFossil):

    def getId(self):
        """ Avatar id"""

    def getIdentifier(self):
        pass
    getIdentifier.produce = lambda x: 'User:{}'.format(x.id)

    def getStraightFullName(self):
        """ Avatar full name, the one usually displayed """
    getStraightFullName.name = "name"
    getStraightFullName.produce = lambda x: x.getStraightFullName(upper=False)


class IAvatarFossil(IAvatarMinimalFossil):

    def getEmail(self):
        """ Avatar email """

    def getFirstName(self):
        """ Avatar first name """

    def getFamilyName(self):
        """ Avatar family name """

    def getTitle(self):
        """ Avatar name title (Mr, Mrs..) """

    def getTelephone(self):
        """ Avatar telephone """
    getTelephone.name = "phone"

    def getOrganisation(self):
        """ Avatar organisation / affiliation """
    getOrganisation.name = "affiliation"

    def getFax(self):
        """ Avatar fax """

    def getAddress(self):
        """ Avatar address """
