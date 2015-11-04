# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from conference import Conference
from badge import BadgeTemplateItem
from MaKaC.i18n import _
from indico.util.date_time import format_date


class ConferenceDates:

    @classmethod
    def getArgumentType(cls):
        return Conference

    @classmethod
    def getValue(cls, conf):
        adjusted_sDate = conf.getAdjustedStartDate()
        adjusted_eDate = conf.getAdjustedEndDate()
        confDateInterval = _("%s to %s") % (format_date(adjusted_sDate, format='long'), format_date(adjusted_eDate, format='long'))
        if adjusted_sDate.strftime("%d%B%Y") == \
                adjusted_eDate.strftime("%d%B%Y"):
            confDateInterval = format_date(adjusted_sDate, format='long')
        elif adjusted_sDate.strftime("%B%Y") == adjusted_eDate.strftime("%B%Y"):
            confDateInterval = "%s-%s %s" % (adjusted_sDate.day, adjusted_eDate.day, format_date(adjusted_sDate, format='MMMM yyyy'))
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

        self.items_actions = {
            "Title": (_("Title"), lambda x: x.get_personal_data().get('title', '')),
            "Full Name": (_("Full Name"), lambda x: u"{} {}".format(x.get_personal_data().get('title', ''),
                                                                    x.get_full_name())),
            "Full Name (w/o title)": (_("Full Name (w/o title)"), lambda x: "{}".format(x.get_full_name())),
            "Full Name B": (_("Full Name B"), lambda x: u"{} {}".format(x.get_personal_data().get('title', ''),
                                                                        x.get_full_name(last_name_first=False))),
            "Full Name B (w/o title)": (_("Full Name B (w/o title)"), lambda x: x.get_full_name(last_name_first=False)),
            "Full Name C": (_("Full Name C"),
                            lambda x: u"{} {}".format(x.get_personal_data().get('title', ''),
                                                      x.get_full_name(last_name_first=False, last_name_upper=True))),
            "Full Name C (w/o title)": (_("Full Name C (w/o title)"), lambda x: x.get_full_name(last_name_upper=True)),
            "Full Name D (abbrev)": (_("Full Name D (abbrev)"),
                                     lambda x: u"{} {}".format(x.get_personal_data().get('title', ''),
                                                               x.get_full_name(last_name_first=False,
                                                                               last_name_upper=True,
                                                                               abbrev_first_name=True))),
            "Full Name D (abbrev, w/o title)": (_("Full Name D (abbrev, w/o title)"),
                                                lambda x: x.get_full_name(last_name_upper=True,
                                                                          abbrev_first_name=True)),
            "First Name": (_("First Name"), lambda x: x.first_name),
            "Surname": (_("Surname"), lambda x: x.last_name),
            "Institution": (_("Institution"), lambda x: x.get_personal_data().get('affiliation', '')),
            "Address": (_("Address"), lambda x: x.get_personal_data().get('address', '')),
            "Country": (_("Country"), lambda x: x.get_personal_data().get('country', '')),
            "Phone": (_("Phone"), lambda x: x.get_personal_data().get('phone', '')),
            "Email": (_("Email"), lambda x: x.email),
            "Amount": (_("Amount"), lambda x: x.price),
            "Conference Name": (_("Conference Name"), Conference.getTitle),
            "Conference Dates": (_("Conference Dates"), ConferenceDates),
            "Fixed Text": (_("Fixed Text"), BadgeTemplateItem.getFixedText)
        }

        # Dictionary that maps group names to the item names that fall into that group.
        # The groups are only used for the <select> box in the WConfModifBadgeDesign.tpl file.
        self.groups = [
            (_("Registrant Data"), ["Title", "Full Name", "Full Name (w/o title)", "Full Name B",
                                    "Full Name B (w/o title)", "Full Name C", "Full Name C (w/o title)",
                                    "Full Name D (abbrev)", "Full Name D (abbrev, w/o title)", "First Name",
                                    "Surname", "Institution", "Address",
                                    "Country", "Phone", "Email", "Amount"]),
            (_("Conference Data"), ["Conference Name",  "Conference Dates"]),
            (_("Fixed Elements"), ["Fixed Text"])
        ]
