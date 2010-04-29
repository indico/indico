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

from MaKaC.registration import Registrant
from conference import Conference
from badge import BadgeTemplateItem
from MaKaC.webinterface.common.countries import CountryHolder
from MaKaC.i18n import _


class RegistrantBadge:

    @classmethod
    def getArgumentType(cls):
        return Registrant

class RegistrantCountry(RegistrantBadge):

    @classmethod
    def getValue(cls, reg):
        return CountryHolder().getCountryById(reg.getCountry())


class RegistrantFullName2(RegistrantBadge):
    """
    FullName without Title.
    """
    @classmethod
    def getValue(cls, reg):
        return reg.getFullName(title=False)

class RegistrantFullName3(RegistrantBadge):
    """
    FullName with Title and with the FirstName first.
    """
    @classmethod
    def getValue(cls, reg):
        return reg.getFullName(firstNameFirst=True)

class RegistrantFullName4(RegistrantBadge):
    """
    FullName without Title and with the FirstName first.
    """
    @classmethod
    def getValue(cls, reg):
        return reg.getFullName(title=False, firstNameFirst=True)

class RegistrantFullName5(RegistrantBadge):
    """
    FullName with Title, the FirstName first and uppercase in surname.
    """
    @classmethod
    def getValue(cls, reg):
        res = "%s %s"%( reg.getFirstName(), reg.getFamilyName().upper())
        res = res.strip()
        if reg.getTitle() != "":
            res = "%s %s"%( reg.getTitle(), res )
        return res

class RegistrantFullName6(RegistrantBadge):
    """
    FullName without Title, the FirstName first and uppercase inthe surname.
    """
    @classmethod
    def getValue(cls, reg):
        res = "%s %s"%( reg.getFirstName(), reg.getFamilyName().upper())
        res = res.strip()
        return res

class ConferenceDates:

    @classmethod
    def getArgumentType(cls):
        return Conference

    @classmethod
    def getValue(cls, conf):
        adjusted_sDate = conf.getAdjustedStartDate()
        adjusted_eDate = conf.getAdjustedEndDate()
        confDateInterval = "%s to %s"%(adjusted_sDate.strftime("%d %B %Y"), adjusted_eDate.strftime("%d %B %Y"))
        if adjusted_sDate.strftime("%d%B%Y") == \
                adjusted_eDate.strftime("%d%B%Y"):
            confDateInterval = adjusted_sDate.strftime("%d %B %Y")
        elif adjusted_sDate.strftime("%B%Y") == adjusted_eDate.strftime("%B%Y"):
            confDateInterval = "%s-%s %s"%(adjusted_sDate.day, adjusted_eDate.day, adjusted_sDate.strftime("%B %Y"))
        return confDateInterval


class BadgeDesignConfiguration:
    """ This class has 2 objects:
    -items_actions maps the name of an item to the action that should be taken
    at the time it is drawed.
    -groups organizes the item names into groups. These groups are used for the
    <select> box in the WConfModifBadgeDesign.tpl file.
    """

    """ Dictionary that maps the name of an item to the action that should be taken
    at the time it is drawed.
    An action can be:
      -A method: depending on the class owning the method, a Conference object,
      a Registrant object, or a BadgeTemplateItem object should be passed to the method.
      The method must return a string.
      For example: 'Full Name' : Registrant.getFullName  means that, if a badgeTemplate
      has a 'Full Name' item, each time a badge will be drawed, the Full Name of the
      registrant will be drawed as returned by the method getFullName of the class Registrant.
      -A class: when there is no method already available for what we need, we have
      to write a custom class (see classes above).
      These classes must have 2 methods:
       *it must have a getArgumentType() method, which returns either Conference, Registrant or BadgeTemplateItem.
       Depending on what is returned, we will pass a different object to the getValue() method.
       *it must have a getValue(object) method, to which a Conference instance, a Registrant instance or a
       BadgeTemplateItem instance must be passed, depending on the result of the getArgumentType() method.

      """
    def __init__(self):

            self.items_actions = { "Title":               (_("Title"), Registrant.getTitle),
                               "Full Name":               (_("Full Name"), Registrant.getFullName),
                               "Full Name (w/o title)":   (_("Full Name (w/o title)"), RegistrantFullName2),
                               "Full Name B":             (_("Full Name B"), RegistrantFullName3),
                               "Full Name B (w/o title)": (_("Full Name B (w/o title)"), RegistrantFullName4),
                               "Full Name C":             (_("Full Name C"), RegistrantFullName5),
                               "Full Name C (w/o title)": (_("Full Name C (w/o title)"), RegistrantFullName6),
                               "First Name":              (_("First Name"), Registrant.getFirstName),
                               "Surname":                 (_("Surname"), Registrant.getSurName),
                               "Position":                (_("Position"), Registrant.getPosition),
                               "Institution":             (_("Institution"), Registrant.getInstitution),
                               "Country":                 (_("Country"), RegistrantCountry),
                               "City":                    (_("City"), Registrant.getCity),
                               "Address":                 (_("Address"), Registrant.getAddress),
                               "Phone":                   (_("Phone"), Registrant.getPhone),
                               "Fax":                     (_("Fax"), Registrant.getFax),
                               "Email":                   (_("Email"), Registrant.getEmail),
                               "Personal homepage":       (_("Personal homepage"), Registrant.getPersonalHomepage),
                               "Amount":                  (_("Amount"), Registrant.getTotal),
                               "Conference Name":         (_("Conference Name"), Conference.getTitle),
                               "Conference Dates":        (_("Conference Dates"), ConferenceDates),
                               "Fixed Text":              (_("Fixed Text"), BadgeTemplateItem.getFixedText)
                            }

            """ Dictionary that maps group names to the item names that fall into that group.
            The groups are only used for the <select> box in the WConfModifBadgeDesign.tpl file.
            """
            self.groups = [( _("Registrant Data"), [ "Title", "Full Name", "Full Name (w/o title)", "Full Name B", "Full Name B (w/o title)", "Full Name C", "Full Name C (w/o title)", "First Name",  "Surname",  "Position",
                                                     "Institution",  "Country",  "City", "Address", "Phone", "Fax", "Email", "Personal homepage", "Amount"]),
                      ( _("Conference Data"), [ "Conference Name",  "Conference Dates"]),
                      ( _("Fixed Elements"), [ "Fixed Text"])]
