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
from MaKaC.i18n import _

globalOptions = [
    #Collaboration options necessary in all plugins
    ("tab", {"description" : "Name of tab where the Recording Manager plugin will be placed",
               "type": str,
               "defaultValue": "Recording Manager",
               "editable": True,
               "visible": True,
               "mustReload": False}),
    ("allowedOn", {"description" : "Kind of event types (conference, meeting, simple_event) supported",
               "type": list,
               "defaultValue": ["conference","simple_event","meeting"],
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("admins", {"description": "Recording Manager admins / responsibles",
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #RecordingManager options
    ("sendMailNotifications", {"description" : "Should mail notifications be sent to responsibles?",
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True} ),

    ("micalaDBServer", {"description" : "Server hosting lecture archiving database",
               "type": str,
               "defaultValue": "lectureprocessing01.cern.ch",
               "editable": True,
               "visible": True} ),

    ("micalaDBPort", {"description" : "database port number",
               "type": str,
               "defaultValue": "3306",
               "editable": True,
               "visible": True} ),

    ("micalaDBName", {"description" : "Database name",
               "type": str,
               "defaultValue": "micala",
               "editable": True,
               "visible": True} ),

    ("micalaDBReaderUser", {"description" : "DB reader account",
               "type": str,
               "defaultValue": "reader",
               "editable": True,
               "visible": True} ),

    ("micalaDBReaderPW", {"description" : "DB reader account password",
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True} ),

    ("micalaDBUser", {"description" : "DB account for changes",
               "type": str,
               "defaultValue": "metadata01",
               "editable": True,
               "visible": True} ),

    ("micalaDBPW", {"description" : "DB account password",
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True} ),

    ("micalaDBMachineName", {"description" : "The host name of this machine",
               "type": str,
               "defaultValue": "indico.cern.ch",
               "editable": True,
               "visible": True} ),

    ("micalaDBStatusExportCDS", {"description" : "micala DB task name for CDS export",
               "type": str,
               "defaultValue": "metadata export to CDS",
               "editable": True,
               "visible": True} ),

    ("micalaDBStatusExportMicala", {"description" : "micala DB task name for micala export",
               "type": str,
               "defaultValue": "metadata export to micala",
               "editable": True,
               "visible": True} ),

    ("micalaPreviewURL", {"description" : "URL for web directory containing lecture object previews",
               "type": str,
               "defaultValue": "http://lectureprocessing01.cern.ch/previews",
               "editable": True,
               "visible": True} ),

    ("micalaUploadURL", {"description" : "URL for micala web upload",
               "type": str,
               "defaultValue": "http://lectureprocessing01.cern.ch/micala_monitor/submit_metadata.py",
               "editable": True,
               "visible": True} ),

    ("CDSQueryURL", {"description" : "CDS query URL (put the string REPLACE_WITH_INDICO_ID where you want the Indico ID to be)",
               "type": str,
               "defaultValue": '''http://cdsdev.cern.ch/search?p=sysno%3A%22INDICO.REPLACE_WITH_INDICO_ID%22&f=&action_search=Search&sf=&so=d&rm=&rg=1000&sc=1&ot=970&of=t&ap=0''',
               "editable": True,
               "visible": True} ),

    ("CDSBaseURL", {"description" : "Base URL for CDS record",
               "type": str,
               "defaultValue": "http://cdsweb.cern.ch/record/%s",
               "editable": True,
               "visible": True} ),

    ("CDSUploadURL", {"description" : "URL for CDS web upload (%s is the callback url)",
               "type": str,
               "defaultValue": "http://cdstest.cern.ch/webupload.py?callback_url=%s",
               "editable": True,
               "visible": True} ),

    ("CDSUploadCallbackURL", {"description" : "URL for CDS web upload callback (%s is the IndicoID)",
               "type": str,
               "defaultValue": "https://micala.cern.ch/webservices/api_json.py?action=cds_callback&IndicoId=%s",
               "editable": True,
               "visible": True} ),

    ("CDSCategoryAssignments", {"description" : "A dictionary whose keys are Indico category IDs and whose corresponding values are the CDS categories to which any records with these Indico IDs as owners should be assigned.",
                      "type": dict,
                      "defaultValue": {"3l13": "Restricted_ATLAS_Talks",
                                       "2l76": "Restricted_CMS_Talks"    },
                      "editable": True} ),

    ("CDSExperimentAssignments", {"description" : "A dictionary whose keys are Indico category IDs and whose values are the corresponding experiment names.",
                      "type": dict,
                      "defaultValue": {"1l2":  "ATLAS",
                                       "2l76": "CMS",
                                       "1l22": "LHCb",
                                       "1l8": "ALICE"    },
                      "editable": True} ),

    ("videoLinkName", {"description" : "Name of Indico link to CDS",
               "type": str,
               "defaultValue": "Video in CDS",
               "editable": True,
               "visible": True} ),

# need to look over this again:
    ("mediaArchiveFormatPlainVideo", {"description" : "Format of plain video filename",
               "type": str,
               "defaultValue": "http://mediaarchive.cern.ch/MediaArchive/Video/Public/Conferences/%s/%s",
               "editable": True,
               "visible": True} ),

# need to look over this again:
    ("mediaArchiveFormatWebLecture", {"description" : "Format of web lecture filename",
               "type": str,
               "defaultValue": "http://mediaarchive.cern.ch/MediaArchive/Video/Public2/WebLectures/%s/%s",
               "editable": True,
               "visible": True} ),

    ("videoFormatStandard", {"description" : "Standard video format",
               "type": str,
               "defaultValue": "720x576 4/3, 25",
               "editable": True,
               "visible": True} ),

    ("videoFormatWide", {"description" : "Wide-screen video format",
               "type": str,
               "defaultValue": "720x576 16/9, 25",
               "editable": True,
               "visible": True} ),

    ("contentTypeWebLecture", {"description" : "Web lecture identifier",
               "type": str,
               "defaultValue": "WLAPLectureObject-v0.2",
               "editable": True,
               "visible": True} ),

    ("languageDictionary", {"description" : "Dictionary of language codes and names; please use MARC codes: http://www.loc.gov/marc/languages",
                      "type": dict,
                      "defaultValue": {"eng": "English",
                                       "fre": "French",
                                       "bul": "Bulgarian",
                                       "chi": "Chinese",
                                       "cze": "Czech",
                                       "dan": "Danish",
                                       "dut": "Dutch/Flemish",
                                       "fin": "Finnish",
                                       "ger": "German",
                                       "gre": "Greek",
                                       "hun": "Hungarian",
                                       "ita": "Italian",
                                       "jpn": "Japanese",
                                       "nor": "Norweigan",
                                       "pol": "Polish",
                                       "por": "Portuguese",
                                       "slo": "Slovak",
                                       "spa": "Spanish",
                                       "swe": "Swedish" },
                      "editable": True} ),

    ("languageCodePrimary", {"description" : "First choice of language; please use MARC codes: http://www.loc.gov/marc/languages",
               "type": str,
               "defaultValue": "eng",
               "editable": True,
               "visible": True} ),

    ("languageCodeSecondary", {"description" : "Second choice of language; please use MARC codes: http://www.loc.gov/marc/languages",
               "type": str,
               "defaultValue": "fre",
               "editable": True,
               "visible": True} )
]
