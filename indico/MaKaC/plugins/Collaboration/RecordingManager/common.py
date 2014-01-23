# -*- coding: utf-8 -*-
##
##
## This file is par{t of Indico.
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

from MaKaC.plugins.Collaboration.base import CSErrorBase
from MaKaC.plugins.Collaboration.RecordingManager.exceptions import RecordingManagerException
from MaKaC.webinterface.common.contribFilters import PosterFilterField
from MaKaC.conference import ConferenceHolder
from MaKaC.common.logger import Logger
from MaKaC.errors import MaKaCError, NoReportError
try:
    import MySQLdb
except ImportError:
    Logger.get("RecMan").debug("Cannot import MySQLdb")
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

import time
from MaKaC.common.xmlGen import XMLGen
from MaKaC.common.output import outputGenerator, XSLTransformer
from MaKaC.conference import Link
from MaKaC import conference

from urllib import urlencode, quote_plus
from urllib2 import Request, urlopen, HTTPError
import re
import os
import sys
from MaKaC.plugins.Collaboration.RecordingManager.micala import MicalaCommunication
from MaKaC.i18n import _

from indico.util.string import truncate

def getTalks(conference, sort = False):
    """
    sort: if True, contributions are sorted by start date (non scheduled contributions
    at the end)
    """

    # Logger.get('RecMan').debug("in getTalks()")

    # max length for title string
    title_length = 39

    # recordable_events is my own list of tags for each recordable event
    # which will be used by the tpl file.
    recordable_events = []
    talks = []

    speaker_str = ""
    speaker_list = conference.getChairList()
    if speaker_list is not None:
        speaker_str = ", ".join(["%s %s"%(speaker.getFirstName(), speaker.getFamilyName()) for speaker in speaker_list])

    event_info = {}
    event_info["contId"] = ""
    event_info["speakers"]   = speaker_str
    event_info["type"]       = "conference"
    event_info["IndicoID"]   = generateIndicoID(conference = conference.getId(),
                                              session         = None,
                                              contribution    = None,
                                              subcontribution = None)
    event_info["title"]      = conference.getTitle()
    event_info["titleshort"] = truncate(event_info["title"], 40)
    # this always comes first, so just pretend it's 0 seconds past the epoch
    event_info["date"]       = int(time.mktime(conference.getAdjustedStartDate().timetuple()))

    event_info["LOID"]       = ""
    event_info["IndicoLink"] = doesExistIndicoLink(conference)

    recordable_events.append(event_info)

    # Posters are contributions that are not recordable,
    # so filter them out here
    filter = PosterFilterField(conference, False, False)
    for contribution in conference.getContributionList():
        if filter.satisfies(contribution):
            talks.append(contribution)
            speaker_str = ""
            speaker_list = contribution.getSpeakerList()
            if speaker_list is not None:
                speaker_str = ", ".join(["%s %s"%(speaker.getFirstName(), speaker.getFamilyName()) for speaker in speaker_list])

            event_info = {}
            event_info["contId"] = contribution.getId()
            event_info["speakers"]   = speaker_str
            event_info["type"]       = "contribution"
            event_info["IndicoID"]   = generateIndicoID(conference = conference.getId(),
                                              session         = None,
                                              contribution    = contribution.getId(),
                                              subcontribution = None)
            event_info["title"]      = contribution.getTitle()
            event_info["titleshort"] = truncate(event_info["title"], title_length)
            # Sometimes contributions are not scheduled, so they have no start date.
            # In this case assign it the value None, and it will be displayed
            # at the end of the list with the time value "not scheduled"
            if contribution.getAdjustedStartDate() is not None:
                event_info["date"]   = int(time.mktime(contribution.getAdjustedStartDate().timetuple()))
            else:
                event_info["date"]   = None

            event_info["LOID"]       = ""
            event_info["IndicoLink"] = doesExistIndicoLink(contribution)

            recordable_events.append(event_info)
            ctr_sc = 0
            for subcontribution in contribution.getSubContributionList():
                ctr_sc += 1
                event_info = {}
                event_info["contId"] = contribution.getId()
                speaker_str = ""
                speaker_list = subcontribution.getSpeakerList()

                if speaker_list is not None:
                    speaker_str = ", ".join(["%s %s"%(speaker.getFirstName(), speaker.getFamilyName()) for speaker in speaker_list])

                event_info["speakers"]   = speaker_str
                event_info["type"]       = "subcontribution"
                event_info["IndicoID"]   = generateIndicoID(conference = conference.getId(),
                                              session         = None,
                                              contribution    = contribution.getId(),
                                              subcontribution = subcontribution.getId())
                event_info["title"]      = subcontribution.getTitle()
                event_info["titleshort"] = truncate(event_info["title"], title_length)
                # Subcontribution objects don't have start dates,
                # so get the owner contribution's start date
                # and add the counter ctr_sc so they appear in order
                if subcontribution.getOwner().getAdjustedStartDate() is not None:
                    event_info["date"]     = int(time.mktime(subcontribution.getOwner().getAdjustedStartDate().timetuple()) + ctr_sc)
                else:
                    event_info["date"]       = int(time.mktime(conference.getAdjustedStartDate().timetuple())) + ctr_sc
                event_info["LOID"]       = ""
                event_info["IndicoLink"] = doesExistIndicoLink(subcontribution)

                recordable_events.append(event_info)


    for session in conference.getSessionList():
        event_info = {}
        event_info["contId"] = ""
        event_info["speakers"] = ""
        event_info["type"]     = "session"
        event_info["IndicoID"] = generateIndicoID(conference = conference.getId(),
                                                  session         = session.getId(),
                                                  contribution    = None,
                                                  subcontribution = None)
        event_info["title"]      = session.getTitle()
        event_info["titleshort"] = truncate(event_info["title"], title_length)
        # Get start time as seconds since the epoch so we can sort
        if session.getAdjustedStartDate() is not None:
            event_info["date"]   = int(time.mktime(session.getAdjustedStartDate().timetuple()))
        else:
            event_info["date"]   = None
        event_info["LOID"]       = ""
        event_info["IndicoLink"] = doesExistIndicoLink(session)

        recordable_events.append(event_info)

    # Get list of matching IndicoIDs and CDS records from CDS
    cds_indico_matches = getCDSRecords(conference.getId())
#    Logger.get('RecMan').debug('cds_indico_pending...')
    cds_indico_pending = MicalaCommunication.getCDSPending(conference.getId())

    # In case there are any records that were pending and are now appearing in CDS,
    # then update the micala database accordingly.
    MicalaCommunication.updateMicalaCDSExport(cds_indico_matches, cds_indico_pending)

#    Logger.get('RecMan').debug("cds_indico_matches: %s, cds_indico_pending: %s" % (cds_indico_matches, cds_indico_pending))
    for event_info in recordable_events:
        try:
            event_info["CDSID"]     = cds_indico_matches[event_info["IndicoID"]]
            event_info["CDSURL"]    = CollaborationTools.getOptionValue("RecordingManager", "CDSBaseURL") % event_info["CDSID"]
        except KeyError:
#            Logger.get('RecMan').debug("Following talk not in CDS: %s" % event_info["title"])
            if cds_indico_pending is not None and event_info["IndicoID"] in set(cds_indico_pending):
                event_info["CDSID"]  = 'pending'
                event_info["CDSURL"] = ""
            else:
                event_info["CDSID"]  = "none"
                event_info["CDSURL"] = ""

    # Get list of matching IndicoID's and LOIDs from the Micala database
    existing_matches = MicalaCommunication.getMatches(conference.getId())

    # insert any existing matches into the recordable_events array
    for talk in recordable_events:
        # Look up IndicoID in existing_matches dictionary
        try:
            matching_LOID = existing_matches[talk["IndicoID"]]
        # If not found, do nothing (talk["LOID"] should already be assigned to "" by default)
        except KeyError:
            pass
        # If there is a matching_LOID, assign it to talk["LOID"]
        else:
            talk["LOID"] = matching_LOID

    # Now that we have all the micala, CDS and IndicoLink info, set up the bg images
    for talk in recordable_events:
        talk["bg"]         = chooseBGColor(talk)

    # Format dates for each talk for pleasing display
    for talk in recordable_events:
        talk["date_nice"] = formatDate(talk["date"])

    # Next, sort the list of events by startDate for display purposes
    recordable_events.sort(startTimeCompare)

#    Logger.get('RecMan').debug('leaving getTalks()')

    return recordable_events

def startTimeCompare(a, b):
    '''This subroutine is for sorting the events, sessions,
    contributions and subcontributions correctly.
    Note: if a session and contribution have the exact same start time,
    then it must be the first contribution in the session, and we
    want to display the session first, so return the appropriate value to do that.
    If the date is None, put it at the end.'''

    if a["date"] is not None and b["date"] is None:
        return -1
    elif a["date"] is None and b["date"] is not None:
        return 1
    elif a["date"] is None and b["date"] is None:
        return 0
    elif a["date"] > b["date"]:
        return 1
    elif a["date"] == b["date"]:
        if a["type"] == "contribution" and b["type"] == "session":
            return 1
        elif a["type"] == "session" and b["type"] == "contribution":
            return -1
        else:
            return 0
    else:  #a < b
        return -1

def formatDate(date_str):
    '''Given number of seconds since the epoch, convert for display in the main Recording Manager interface.'''

    if date_str is not None:
        time_struct = time.localtime(date_str)

        day_of_week   = [_('Mon'),
                         _('Tue'),
                         _('Wed'),
                         _('Thu'),
                         _('Fri'),
                         _('Sat'),
                         _('Sun')]
    #    month_of_year = [_('January'),
    #                     _('February'),
    #                     _('March'),
    #                     _('April'),
    #                     _('May'),
    #                     _('June'),
    #                     _('July'),
    #                     _('August'),
    #                     _('September'),
    #                     _('October'),
    #                     _('November'),
    #                     _('December')]
        month_of_year = [_('Jan'),
                         _('Feb'),
                         _('Mar'),
                         _('Apr'),
                         _('May'),
                         _('Jun'),
                         _('Jul'),
                         _('Aug'),
                         _('Sep'),
                         _('Oct'),
                         _('Nov'),
                         _('Dec')]

        return "%02d:%02d, %s %d %s" % (time_struct.tm_hour,
                                        time_struct.tm_min,
                                        day_of_week[time_struct.tm_wday],
                                        time_struct.tm_mday,
                                        month_of_year[int(time_struct.tm_mon - 1)])
    else:
        return "NOT SCHEDULED"

def generateIndicoID(conference     = None,
                    session         = None,
                    contribution    = None,
                    subcontribution = None):
    """Given the conference, session, contribution and subcontribution IDs,
    return an "Indico ID" of the form:
    12345
    12345s1
    12345c0
    12345c0sc3
    """
    IndicoID = ""

    # Some old conference IDs are non-numerical, e.g. a034286, but session, contribution
    # and subcontribution IDs should all be numerical.
    if session is not None:
        IndicoID = "%ss%s" % (conference, session)
    elif contribution is None:
        IndicoID = "%s" % (conference,)
    elif subcontribution is not None:
        IndicoID = "%sc%ssc%s" % (conference, contribution, subcontribution)
    else:
        IndicoID = "%sc%s" % (conference, contribution)

    return IndicoID

def getOrphans():
    """Get list of Lecture Objects in the database that have no IndicoID assigned"""

    # Initialize success flag and result string
    flagSuccess = True
    result      = ""

    try:
        connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                     port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                     user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                     passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                     db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
    except NameError:
        raise MaKaCError("You need to install MySQLdb (python-mysql) in order to use the Recording Manager")
    except MySQLdb.Error, e:
        flagSuccess = False
        result += "MySQL error %d: %s" % (e.args[0], e.args[1])

    idTaskRecording = MicalaCommunication.getIdTask("recording")

    if flagSuccess == True:
        try:
            cursor = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            # Query Lectures table for all records in which IndicoID is blank or NULL
            cursor.execute("""SELECT L.idLecture AS idLecture, L.LOID AS LOID, L.IndicoID AS IndicoID, M.hostname AS Hostname, V.roomName AS RoomName, L.duration AS Duration
                FROM lectures L, lectureLatestStatus LS, status S, machines M, venues V
                WHERE LS.idLecture = L.idLecture
                AND LS.idTask = %s
                AND LS.idStatus = S.idStatus
                AND S.idMachine = M.idMachine
                AND M.idVenue = V.idVenue
                AND L.IndicoID IS NULL
                ORDER BY L.LOID""",
                (idTaskRecording,))
            connection.commit()
            rows = cursor.fetchall()
            cursor.close()
            connection.close()
        except MySQLdb.Error, e:
            flagSuccess = False
            result += _("MySQL error %d: %s") % (e.args[0], e.args[1])
        # nothing went wrong, so populate the list "rows" with the appropriate LOID metadata and assign to result to be returned
        else:
            for lecture in rows:
                lecture["time"] = formatLOID(lecture["LOID"])[0]
                lecture["date"] = formatLOID(lecture["LOID"])[1]
                lecture["box"]  = formatLOID(lecture["LOID"])[2]
                lecture["niceDuration"] = formatDuration(lecture["Duration"])
                idLecture = MicalaCommunication.getIdLecture(lecture["LOID"])
                idTaskPreview = MicalaCommunication.getIdTask("building preview")
                lecture["preview"] = MicalaCommunication.isTaskComplete(idLecture, idTaskPreview)
            result = rows

    return {"success": flagSuccess, "result": result}

def parseIndicoID(IndicoID):
    """Given an "Indico ID" of the form shown above, determine whether it is
    a conference, subcontribution etc, and return that info with the individual IDs."""

    # regular expressions to match IndicoIDs for conference, session, contribution,
    # subcontribution
    # Note: older conferences may be a string like this: a034286 instead of just a
    # number
    pConference      = re.compile('(\w*\d+)$')
    pSession         = re.compile('(\w*\d+)s(\d+|s\d+)$')
    pContribution    = re.compile('(\w*\d+)c(\d+|s\d+t\d+)$')
    pSubcontribution = re.compile('(\w*\d+)c(\d+|s\d+t\d+)sc(\d+)$')

    # perform the matches (match searches from the beginning of the string,
    # unlike search, which matches anywhere in the string)
    mE  = pConference.match(IndicoID)
    mS  = pSession.match(IndicoID)
    mC  = pContribution.match(IndicoID)
    mSC = pSubcontribution.match(IndicoID)

    # Depending on which talk type it is, populate a dictionary containing the name of
    # the type of talk, the actual object, and the individual conference, session,
    # contribution, subcontribution IDs.
    if mSC:
        # Logger.get('RecMan').debug("searched %s, matched %s" % (IndicoID, 'subcontribution'))
        conference = ConferenceHolder().getById(mSC.group(1))
        contribution = conference.getContributionById(mSC.group(2))
        return {'type':           'subcontribution',
                'object':         contribution.getSubContributionById(mSC.group(3)),
                'conference':     mSC.group(1),
                'session':        '',
                'contribution':   mSC.group(2),
                'subcontribution':mSC.group(3)}
    elif mS:
        # Logger.get('RecMan').debug("searched %s, matched %s" % (IndicoID, 'session'))
        conference = ConferenceHolder().getById(mS.group(1))
        return {'type':           'session',
                'object':         conference.getSessionById(mS.group(2)),
                'conference':     mS.group(1),
                'session':        mS.group(2),
                'contribution':   '',
                'subcontribution':''}
    elif mC:
        # Logger.get('RecMan').debug("searched %s, matched %s" % (IndicoID, 'contribution'))
        conference = ConferenceHolder().getById(mC.group(1))
        return {'type':           'contribution',
                'object':         conference.getContributionById(mC.group(2)),
                'conference':     mC.group(1),
                'session':        '',
                'contribution':   mC.group(2),
                'subcontribution':''}
    elif mE:
        # Logger.get('RecMan').debug("searched %s, matched %s" % (IndicoID, 'conference'))
        conference = ConferenceHolder().getById(mE.group(1))
        return {'type':           'conference',
                'object':         conference,
                'conference':     mE.group(1),
                'session':        '',
                'contribution':   '',
                'subcontribution':''}
    else:
        return None


def getBasicXMLRepresentation(aw, IndicoID, contentType, videoFormat, languages):
    '''Generate the basic XML that is to be transformed using one of the XSL files.'''

    # Incantation to initialize XML that I don't fully understand
    xmlGen = XMLGen()
    xmlGen.initXml()

    # aw stands for AccessWrapper. I don't really understand exactly what
    # this command does, but it is apparently necessary
    og = outputGenerator(aw, xmlGen)

    # Generate XML event tag to enclose the entire conference
    xmlGen.openTag("event")

    # Given the IndicoID, retrieve the type of talk and IDs
    parsed = parseIndicoID(IndicoID)

    # populate dictionary with RecordingManager parameters to be used by methods in outputGenerator
    # such as confToXML, _confToXML, _sessionToXML, _contribToXML, _subContributionToXML
    tags = {'talkType':    parsed['type'],
            'talkId':      parsed[parsed['type']],
            'contentType': contentType,
            'videoFormat': videoFormat,
            'languages':   languages}

#    Logger.get('RecMan').info("tags: [%s] [%s] [%s] [%s]" %\
#                              (tags['talkType'],
#                              tags['talkId'],
#                              tags['contentType'],
#                              tags['videoFormat']))
#    for l in tags["languages"]:
#        Logger.get('RecMan').info("language: %s" % l)

    # Given the conference ID, retrieve the corresponding Conference object
    conference = ConferenceHolder().getById(parsed["conference"])

    # Defining the dictionary 'tags' is how we identify ourselves to the outputGenerator
    # methods.
    # Call ConfToXML with different args depending on talk type.
    # includeSession - descend into each session.
    #                  This is necessary for sessions, contributions, and subcontributions,
    #                  since contributions and subcontributions are children of sessions.
    # includeContribution - necessary for contributions and subcontributions
    # includeMaterial - this is always set to "1".
    # showSession - create XML for a particular session, identified by ID
    # showContribution - create XML for a particular contribution, identified by ID
    # showSubContribution - create XML for a particular subcontribution, identified by ID
    # overrideCache - True means force it NOT to use the cache.
    # recordingManagerTags - this is how we pass along all the necessary RecordingManager args to the outputGenerator methods.
    #
    # Nobody outside CERN should have access to CERN access lists.
    # OAI harvesters outside CERN call the same methods we'll be calling,
    # and we don't want to make the access lists available to them.
    if parsed["type"] == 'conference':
#        Logger.get('RecMan').info("generating MARC XML for a conference")
        og.confToXML(conference,
                     0, # includeSession
                     0, # includeContribution
                     1, # includeMaterial
                     showSession         = None,
                     showContribution    = None,
                     showSubContribution = None,
                     overrideCache       = True,
                     recordingManagerTags = tags)
    elif parsed["type"] == 'session':
#        Logger.get('RecMan').info("generating MARC XML for a session")
        og.confToXML(conference,
                     1, # includeSession
                     0, # includeContribution
                     1, # includeMaterial
                     showSession         = parsed["session"],
                     showContribution    = None,
                     showSubContribution = None,
                     overrideCache       = True,
                     recordingManagerTags = tags)
    elif parsed["type"] == 'contribution':
#        Logger.get('RecMan').info("generating MARC XML for a contribution")
        og.confToXML(conference,
                     1, # includeSession
                     1, # includeContribution
                     1, # includeMaterial
                     showSession         = parsed["session"],
                     showContribution    = parsed["contribution"],
                     showSubContribution = None,
                     overrideCache       = True,
                     recordingManagerTags = tags)
    elif parsed["type"] == 'subcontribution':
#        Logger.get('RecMan').info("generating MARC XML for a subcontribution")
        og.confToXML(conference,
                     1, # includeSession
                     1, # includeContribution
                     1, # includeMaterial
                     showSession         = None,
                     showContribution    = parsed["contribution"], # maybe I should turn this on?
                     showSubContribution = parsed["subcontribution"],
                     overrideCache       = True,
                     recordingManagerTags = tags)
    else:
        raise RecordingManagerException(_("IndicoID %s is not a known conference, session, contribution or subcontribution.") % IndicoID)

    xmlGen.closeTag("event")

    # Retrieve the entire basic XML string
    return xmlGen.getXml()

def createCDSRecord(aw, IndicoID, LODBID, lectureTitle, lectureSpeakers, contentType, videoFormat, languages):
    '''Retrieve a MARC XML string for the given conference, then web upload it to CDS.'''

    # Initialize success flag, and result string to which we will append any errors.
    flagSuccess = True
    result = ""

    # generate the basic XML from which we will produce MARC XML for CDS and lecture.xml for micala
    basexml = getBasicXMLRepresentation(aw, IndicoID, contentType, videoFormat, languages)

    from indico.core.config import Config

    marcxml = ""

    # Given the IndicoID, retrieve the type of talk and IDs, so we know which XSL file to use.
    parsed = parseIndicoID(IndicoID)

    # Choose the appropriate stylesheet:
    # - cds_marcxml_video_conference.xsl
    # - cds_marcxml_video_session.xsl
    # - cds_marcxml_video_contribution.xsl
    # - cds_marcxml_video_subcontribution.xsl
    styleSheet = "%s_%s.xsl" % ('cds_marcxml_video', parsed["type"])
    stylePath = os.path.join(Config.getInstance().getStylesheetsDir(), styleSheet)

    if os.path.exists(stylePath):
        try:
#            Logger.get('RecMan').info("Trying to do XSLT using path %s" % stylePath)
            parser = XSLTransformer(stylePath)
            marcxml = parser.process(basexml)
        except Exception:
            flagSuccess = False
            result += _("Cannot parse stylesheet: %s") % sys.exc_info()[0]
    else:
        flagSuccess = False
        result += _("Stylesheet does not exist: %s") % stylePath

    # Uncomment these lines when debugging to see the basic XML representation that is being created.
#    f = open('/tmp/base.xml', 'w')
#    f.write(basexml)
#    f.close()

    # Uncomment these lines when debugging to see the MARC XML being submitted to CDS
#    f = open('/tmp/marc.xml', 'w')
#    f.write(marcxml)
#    f.close()

    # Submit MARC XML record to CDS
    data = urlencode({
        "file": marcxml,
        "mode": "-ir"
    })
    headers = {"User-Agent": "invenio_webupload"}
    url = CollaborationTools.getOptionValue("RecordingManager", "CDSUploadURL")
    if '%s' in url:
        callback_url = CollaborationTools.getOptionValue("RecordingManager", "CDSUploadCallbackURL")
        url = url % quote_plus(callback_url % IndicoID)
    req = Request(url, data, headers)
#    Logger.get('RecMan').debug("req = %s" % str(req))

    try:
        f = urlopen(req)
        cds_response = f.read()
        # cds_response = "testing" # uncomment for debugging
        # Successful operations should result in a one-line message that looks like this:
        # [INFO] Some message here
        # anything else means there was an error
        if cds_response.lstrip()[0:6] != "[INFO]":
            flagSuccess = False
            result += _("CDS webupload response: %s\n") % cds_response
    except HTTPError, e:
        flagSuccess = False
        result += _("CDS returned an error when submitting to %s: %s\n") % (url, e)
    except Exception, e:
        flagSuccess = False
        result += _("Unknown error occured when submitting CDS record: %s.\n") % e

    # Uncomment these lines when debugging to see the result returned by CDS
#    f = open('/tmp/cds_result.txt', 'w')
#    f.write(cds_response)
#    f.close()

    # Update the micala database showing the task has started, but only if
    # the submission actually succeeded.
    if flagSuccess == True:
        # Update the micala database with our current task status
        try:
            # first need to get DB ids for stuff
            idMachine = MicalaCommunication.getIdMachine(CollaborationTools.getOptionValue("RecordingManager", "micalaDBMachineName"))
            idTask    = MicalaCommunication.getIdTask(CollaborationTools.getOptionValue("RecordingManager", "micalaDBStatusExportCDS"))
            # Look for the current talk in the Lectures table of the micala database
            # If it is a plain_video talk, look for its IndicoID;
            # if it is a web_lecture talk, use its LODBID
            if contentType == 'plain_video':
                idLecture = MicalaCommunication.getIdLecture(IndicoID)
                # If the current talk was not found in the micala DB, add a new record.
                if idLecture == '':
                    # It's not necessary to pass contentType since this only gets called once,
                    # for plain_videos, but maybe later we'll want to use it to create records for LOIDs
                    idLecture = MicalaCommunication.createNewMicalaLecture(IndicoID, contentType)
            elif contentType == 'web_lecture':
                # there's no question that there is a record for this lecture object,
                # because we just read the database to get the LODBID.
                idLecture = LODBID

            # update the current lecture record with the title and speaker name
            MicalaCommunication.updateLectureInfo(idLecture, lectureTitle, lectureSpeakers)

            # Inform the micala DB that the CDS record creation task has started.
            MicalaCommunication.reportStatus('START', '', idMachine, idTask, idLecture)
        except Exception, e:
            flagSuccess = False
            result += _("Unknown error occured when updating task information in micala database: %s\n") % e

    return {"success": flagSuccess, "result": result}

def submitMicalaMetadata(aw, IndicoID, contentType, LODBID, LOID, videoFormat, languages):
    '''Generate a lecture.xml file for the given event, then web upload it to the micala server.'''

#    Logger.get('RecMan').debug('in submitMicalaMetadata()')

    # Initialize success flag, and result string to which we will append any errors.
    flagSuccess = True
    result = ""

    # First update the micala database that we've started this task
    try:
        idMachine = MicalaCommunication.getIdMachine(CollaborationTools.getOptionValue("RecordingManager", "micalaDBMachineName"))
        idTask    = MicalaCommunication.getIdTask(CollaborationTools.getOptionValue("RecordingManager", "micalaDBStatusExportMicala"))
        idLecture = LODBID
#        Logger.get('RecMan').debug('submitMicalaMetadata calling reportStatus...')
        MicalaCommunication.reportStatus('START', '', idMachine, idTask, idLecture)
    except Exception, e:
        flagSuccess = False
        result += _("Unknown error occured when updating MICALA START task information in micala database: %s\n.") % e

    basexml = getBasicXMLRepresentation(aw, IndicoID, contentType, videoFormat, languages)

    from indico.core.config import Config

    micalaxml = ""

    # Given the IndicoID, retrieve the type of talk and IDs, so we know which XSL file to use.
    parsed = parseIndicoID(IndicoID)

    # Choose the appropriate stylesheet for the type of talk:
    # - micala_lecture_conference.xsl
    # - micala_lecture_session.xsl
    # - micala_lecture_contribution.xsl
    # - micala_lecture_subcontribution.xsl
    styleSheet = "%s_%s.xsl" % ('micala_lecture', parsed["type"])
    stylePath = os.path.join(Config.getInstance().getStylesheetsDir(), styleSheet)

    if os.path.exists(stylePath):
        try:
#            Logger.get('RecMan').info("Trying to do XSLT using path %s" % stylePath)
            parser = XSLTransformer(stylePath)
            micalaxml = parser.process(basexml)
        except Exception, e:
            flagSuccess = False
            result += _("Cannot parse stylesheet: %s") % sys.exc_info()[0]
    else:
        flagSuccess = False
        result += _("Stylesheet does not exist: %s") % stylePath

    # temporary, for my own debugging
#    f = open('/tmp/micala.xml', 'w')
#    f.write(micalaxml)
#    f.close()

    # Web upload metadata to micala server
    if flagSuccess == True:
        # encode the LOID and the XML file as POST variables
        data = urlencode({ "LOID": LOID, "micalaxml": micalaxml })
        # use the header to identify ourselves
        headers = {"User-Agent": "micala_webupload"}
        # build the request
        request = Request(CollaborationTools.getOptionValue("RecordingManager", "micalaUploadURL"), data, headers)

#        Logger.get('RecMan').debug("micala request = %s" % str(request))

        # submit the request, and append caught exceptions to the result string,
        # to be displayed by services.py
        try:
            f = urlopen(request)
            request_result = f.read()
            if request_result == 'no data':
                result += _("micala web upload returned an unknown error when submitting to ") + "%s\n" % \
                    (CollaborationTools.getOptionValue("RecordingManager", "micalaUploadURL"))
            # Logger.get('RecMan').debug("micala result = %s" % str(request_result))
        except HTTPError, e:
            flagSuccess = False
            result += _("micala web upload returned an error when submitting to ") + "%s: %s\n" % \
                (CollaborationTools.getOptionValue("RecordingManager", "micalaUploadURL"), e)
        except Exception, e:
            flagSuccess = False
            Logger.get('RecMan').exception('Error submitting metadata')
            result += _("Unknown error occured when submitting micala metadata: %s\n") % str(e)

    # Update the micala database showing the task has started, but only if
    # the submission actually succeeded.
    if flagSuccess == True:
        try:
            MicalaCommunication.reportStatus('COMPLETE', '', idMachine, idTask, idLecture)
        except Exception, e:
            flagSuccess = False
            result += _("Unknown error occured when updating COMPLETE MICALA task information in micala database: %s\n." % e)
    # if errors were encountered, report ERROR status and details to micala DB
    else:
        try:
            MicalaCommunication.reportStatus('ERROR', result, idMachine, idTask, idLecture)
        except Exception, e:
            flagSuccess = False
            result += _("Unknown error occured when updating COMPLETE MICALA task information in micala database: %s\n." % e)

    return {"success": flagSuccess, "result": result}

def getCDSRecords(confId):
    '''Query CDS to see if it has an entry for the given event as well as all its sessions, contributions and subcontributions.
    If yes return a dictionary pairing CDS IDs with Indico IDs.'''

    # Also, this method should then make sure that the database Status table has been updated to show that the export to CDS task is complete

#    Logger.get('RecMan').debug('in getCDSRecords()')

    # Slap a wildcard on the end of the ID to find the conference itself as well as all children.
    id_plus_wildcard = confId + "*"

    # Here is a help page describing the GET args,
    # if this CDS query needs to be changed (thanks jerome.caffaro@cern.ch):
    # http://invenio-demo.cern.ch/help/hacking/search-engine-api
    # NB: We replace the string REPLACE_WITH_INDICO_ID manually instead of using %s because
    # there are also url-encoded chars containing the % char.
    optionsCDSQueryURL = CollaborationTools.getOptionValue("RecordingManager", "CDSQueryURL")
    escapedOptionsCDSQueryURL = optionsCDSQueryURL.replace("REPLACE_WITH_INDICO_ID", id_plus_wildcard)
#    Logger.get('RecMan').debug("escapedOptionsCDSQueryURL = " + escapedOptionsCDSQueryURL)
    url = escapedOptionsCDSQueryURL

    # This dictionary will contain CDS ID's, referenced by Indico ID's
    results = {}

    # perform the URL query to CDS. It contains one line for each CDS record,
    # of the form:
    # 001121974 970__ $$aINDICO.21917c22
    # The first number is the CDS record ID, with leading zeros
    # The second number is the MARC XML tag
    # The third string contains the Indico ID
    # (see http://www.loc.gov/marc/bibliographic for detailed information on MARC)
    request = Request(url)
    f = urlopen(request)
    lines = f.readlines()
    f.close()

    # Read each line, extracting the IndicoIDs and their corresponding CDS IDs
    for line in lines:
        result = line.strip()
        if result != "":
#            Logger.get('RecMan').debug(" CDS query result: %s" % line)

            bigcdsid = result.split(" ")[0]
            CDSID = bigcdsid.lstrip("0")

            p = re.compile('INDICO\.(\w*[sc\d]+)')
            m = p.search(line)

            if m:
                IndicoID = m.group(1)
                results[IndicoID] = CDSID
            else:
                # If we end up here then probably something's wrong with the URL, or perhaps we jusy got a blank line
                pass

#            results.append({"CDSID": CDSID, "IndicoID": IndicoID})

    return results


def createIndicoLink(IndicoID, CDSID):
    """Create a link in Indico to the CDS record."""

#    Logger.get('RecMan').debug("in createIndicoLink()")
    # From IndicoID, get info
    try:
        talkInfo = parseIndicoID(IndicoID)
    except NoReportError:
        return False
    obj = talkInfo["object"]

    # Only one link per talk allowed.
    if doesExistIndicoLink(obj):
        return True # consider it a success anyway
    else:
#        Logger.get('RecMan').info("creating a new link in Indico for talk %s, CDS record %s" % (IndicoID, CDSID))

        # material object holds link object.
        # First create a material object with title "Video in CDS" or whatever the current text is.
        material = conference.Material()
        material.setTitle(CollaborationTools.getOptionValue("RecordingManager", "videoLinkName"))
        videoLink = Link()
        videoLink.setOwner(material)
#    I don't think this stuff is necessary:
#        videoLink.setName("Name goes here")
#        videoLink.setDescription("Description goes here")
        videoLink.setURL(CollaborationTools.getOptionValue("RecordingManager", "CDSBaseURL") % str(CDSID))
        material.addResource(videoLink)
        material.setMainResource(videoLink)
        obj.addMaterial(material)
        return True

def doesExistIndicoLink(obj):
    """This function will be called with a conference, session, contribution or subcontribution object.
    Each of those has a getAllMaterialList() method. Call that method and search for a title "Video in CDS"
    and make sure it has a link."""

    flagLinkFound = False

    materials = obj.getAllMaterialList()
    if materials is not None and len(materials) > 0:
        for material in materials:
            # If the material in question is a link
            # whose title is either the original "Video in CDS"
            # or whatever other title might be specified in the RecordingManager
            # plugin options, then we've found a link.
            if isinstance(material.getMainResource(), Link) and \
            (material.getTitle() == "Video in CDS" or material.getTitle() == \
             CollaborationTools.getOptionValue("RecordingManager", "videoLinkName") ):
                flagLinkFound = True

    return flagLinkFound

def formatLOID(LOID):
    """Given a LOID of the form YYYYMMDD-recordingDev-HHMMSS, split it up into nicely readable parts: time, date, recording_device."""

    rawdate = LOID.split('-')[0]
    rawtime = LOID.split('-')[2]

    date = rawdate[6:8] + '.' + rawdate[4:6] + '.' + rawdate[0:4]
    time = rawtime[0:2] + ':' + rawtime[2:4] + ':' + rawtime[4:8]

    recording_device = LOID.split('-')[1]

    return(time, date, recording_device)

def formatDuration(duration):
    """Given the number of seconds, format duration nicely in a human readable string."""

    if duration is None or duration == "":
        return "unknown duration"

    seconds = duration % 60
    hours   = int(duration / 3600)
    minutes = int( (duration - 3600 * hours) / 60 )

    if duration < 60:
        niceDuration = "%d seconds" % seconds
    elif duration < 3600:
        niceDuration = "%d minutes" % minutes
    else:
        niceDuration = "%d hours %02d minutes" % (hours, minutes)

    return niceDuration

def chooseBGColor(talk):
    """Given a talk dictionary, check if it has an LOID, CDS record, and IndicoLink.
    Pick the appropriate image RecordingManagerNNN.png to match that.
    This image will be used for the div background.
    """

    # NB: not currently used
    # I might change this later to gray out talks that have already been matched etc.

    return "#FFFFFF"

class RecordingManagerError(CSErrorBase):
    def __init__(self, operation, inner):
        CSErrorBase.__init__(self)
        self._operation = operation
        self._inner = inner

    def getOrigin(self):
        return 'RecordingManager'

    def getOperation(self):
        return self._operation

    def getInner(self):
        return str(self._inner)

    def getUserMessage(self):
        return ''

    def getLogMessage(self):
        return "Recording Request error for operation: " + str(self._operation) + ", inner exception: " + str(self._inner)

