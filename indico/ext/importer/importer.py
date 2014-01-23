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

class DataImporter(object):
    """
    Base class for custom data importers. Fetches and converts data from external source.
    """

    def importData(self, query, size):
        """
        Method that should be overloaded by inheriting classes. Imports data from the source.
        @param query A search phrase send to the importer.
        @param size Number of records to fetch from external source.
        @return list of dictionaries. The list of dictionaries should have the following format. Please note
        that all elements of the dictionary are optional.
        [
            {
            "recordId" : idOfTheRecordInExternalSource,
            "title" : eventTitle,
            "primaryAuthor" : {
                                "firstName": primaryAuthorFirstName,
                                "familyName": primaryAuthorFamilyName,
                                "affiliation": primaryAuthorAffiliation
                                },
            "speaker" : {
                                "firstName": speakerFirstName,
                                "familyName": speakerFamilyName,
                                "affiliation": speakerAffiliation
                                },
            "secondaryAuthor" : {
                                "firstName": secondaryAuthorFirstName,
                                "familyName": secondaryAuthorFamilyName,
                                "affiliation": secondaryAuthorAffiliation
                                },
            "summary" : eventSummary,
            "meetingName" : nameOfTheEventMeeting,
            "materials" : [{
                        "name": nameOfTheLink,
                        "url": linkDestination
                      } ... ],
            "reportNumbers" : [reportNumber, ...]
            "startDateTime" : {
                                "time" : eventStartTime,
                                "date" : eventStartDate
                               },
            "endDateTime" : {
                                "time" : eventEndTime,
                                "date" : eventEndDate
                               }
            "place" : eventPlace
            },
            ...
        ]
        """
        raise "Base class method. Need to be implemented."
