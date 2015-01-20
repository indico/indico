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

from MaKaC.registration import Registrant
from conference import Conference
from poster import PosterTemplateItem
from MaKaC.webinterface.common.countries import CountryHolder


class ConferenceDates:

    def getArgumentType(cls):
        return Conference
    getArgumentType = classmethod (getArgumentType)

    def getValue(cls, conf):
        if conf.getStartDate().date() == conf.getEndDate().date():
            return conf.getAdjustedStartDate().strftime("%a %d/%m/%Y %H:%M")
        else:
            return str(conf.getAdjustedStartDate().date()) + ' - ' + str(conf.getAdjustedEndDate().date())
    getValue = classmethod (getValue)

class ConferenceLocation:

    def getArgumentType(cls):
        return Conference
    getArgumentType = classmethod (getArgumentType)

    def getValue(cls, conf):
        return conf.getLocation().getName() if conf.getLocation() else ""
    getValue = classmethod (getValue)


class ConferenceAddress:

    def getArgumentType(cls):
        return Conference
    getArgumentType = classmethod (getArgumentType)

    def getValue(cls, conf):
        return conf.getLocation().getAddress() if conf.getLocation() else ""
    getValue = classmethod (getValue)

class LectureCategory:
    def getArgumentType(cls):
        return Conference
    getArgumentType = classmethod (getArgumentType)

    def getValue(cls, conf):
        return conf.getOwner().getTitle()
    getValue = classmethod (getValue)

class Organisers:
    def getArgumentType(cls):
        return Conference
    getArgumentType = classmethod (getArgumentType)

    def getValue(cls, conf):
        return conf.getOrgText()
    getValue = classmethod (getValue)

class ConferenceRoom:
    def getArgumentType(cls):
        return Conference
    getArgumentType = classmethod (getArgumentType)

    def getValue(cls, conf):
        if conf.getRoom():
            return conf.getRoom().getName()
        else:
            return ""
    getValue = classmethod (getValue)

class ConferenceChairperson:
    def getArgumentType(cls):
        return Conference
    getArgumentType = classmethod (getArgumentType)

    def getValue(cls, conf):
        list = conf.getChairList()
        return list

    getValue = classmethod (getValue)


class PosterDesignConfiguration:
    """ This class has 2 objects:
    -items_actions maps the name of an item to the action that should be taken
    at the time it is drawed.
    -groups organizes the item names into groups. These groups are used for the
    <select> box in the WConfModifPosterDesign.tpl file.
    """

    """ Dictionary that maps the name of an item to the action that should be taken
    at the time it is drawed.
    An action can be:
      -A method: depending on the class owning the method, a Conference object,
      a Registrant object, or a PosterTemplateItem object should be passed to the method.
      The method must return a string.
      For example: 'Full Name' : Registrant.getFullName  means that, if a posterTemplate
      has a 'Full Name' item, each time a poster will be drawed, the Full Name of the
      registrant will be drawed as returned by the method getFullName of the class Registrant.
      -A class: when there is no method already available for what we need, we have
      to write a custom class (see classes above).
      These classes must have 2 methods:
       *it must have a getArgumentType() method, which returns either Conference, Registrant or PosterTemplateItem.
       Depending on what is returned, we will pass a different object to the getValue() method.
       *it must have a getValue(object) method, to which a Conference instance, a Registrant instance or a
       PosterTemplateItem instance must be passed, depending on the result of the getArgumentType() method.

      """
    def __init__(self):

        self.items_actions = {
                         "Lecture Category": (_("Lecture Category"), LectureCategory),
                         "Lecture Name": (_("Lecture Name"), Conference.getTitle),
                         "Lecture Date(s)": (_("Lecture Date(s)"), ConferenceDates),
                         "Speaker(s)": (_("Speaker(s)"), ConferenceChairperson),
                         "Description": (_("Description"), Conference.getDescription),
                         "Location (name)": (_("Location (name)"), ConferenceLocation),
                         "Location (address)": (_("Location (address)"), ConferenceAddress),
                         "Location (room)": (_("Location (room)"), ConferenceRoom),
                         "Organisers": (_("Organisers"), Organisers),
                         "Fixed Text": (_("Fixed Text"), PosterTemplateItem.getFixedText)
                        }

        """ Dictionary that maps group names to the item names that fall into that group.
        The groups are only used for the <select> box in the WConfModifPosterDesign.tpl file.
        """
        self.groups = [( _("Lecture Data"), ["Lecture Category", "Lecture Name", "Lecture Date(s)","Speaker(s)",
                                             "Description", "Location (name)", "Location (address)", "Location (room)","Organisers"]),
                        ( _("Fixed Elements"), ["Fixed Text"])]
