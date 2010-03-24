# -*- coding: utf-8 -*-
##
## $Id: common.py,v 1.4 2009/04/25 13:56:17 dmartinc Exp $
##
## This file is par{t of CDS Indico.
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

from MaKaC.plugins.Collaboration.base import CollaborationServiceException,\
    CSErrorBase
from MaKaC.common.PickleJar import Retrieves
from MaKaC.webinterface.common.contribFilters import PosterFilterField
from MaKaC.conference import Contribution, ConferenceHolder
import MySQLdb
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.conference import Contribution
from MaKaC.conference import Session

from MaKaC.common.logger import Logger

from time import mktime
from MaKaC.common.xmlGen import XMLGen
from MaKaC.export.oai2 import DataInt
from MaKaC.common.output import outputGenerator, XSLTransformer
from MaKaC.conference import Link

from urllib2 import Request, urlopen
import re
import os
import sys

def getTalks(conference, oneIsEnough = False, sort = False):
    """ oneIsEnough: the algorithm will stop at the first contribution found
                     it will then return a list with a single element
        sort: if True, contributions are sorted by start date (non scheduled contributions at the end)
    """

    # max length for title string
    title_length = 39

    # recordable_events is my own list of tags for each recordable event
    # which will be used by the tpl file.
    recordable_events = []
    talks = []

    event_info = {}
    event_info["speakers"]   = ""
    event_info["type"]       = "conference"
    event_info["IndicoID"]   = generateIndicoID(conference = conference.getId(),
                                              session         = None,
                                              contribution    = None,
                                              subcontribution = None)
    event_info["title"]      = conference.getTitle()
    event_info["titleshort"] = truncate_str(event_info["title"], 40)
    # this always comes first, so just pretend it's 0 seconds past the epoch
    event_info["date"]       = 0
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
                tag_first_iter = True
                for speaker in speaker_list:
                    if tag_first_iter:
                        speaker_str = "%s %s" % (speaker_list[0].getFirstName(),
                                                 speaker_list[0].getFamilyName())
                    else:
                        speaker_str = "%s, %s %s" % \
                            (speaker_str, speaker.getFirstName(), speaker.getFamilyName())

            event_info = {}
            event_info["speakers"]   = speaker_str
            event_info["type"]       = "contribution"
            event_info["IndicoID"]   = generateIndicoID(conference = conference.getId(),
                                              session         = None,
                                              contribution    = contribution.getId(),
                                              subcontribution = None)
            event_info["title"]      = contribution.getTitle()
            event_info["titleshort"] = truncate_str(event_info["title"], title_length)
            # NOTE: Sometimes there is no start date?! e.g. 21917. I guess I should deal with this
            try:
                event_info["date"]       = int(mktime(contribution.getStartDate().timetuple()))
            except AttributeError:
                event_info["date"]       = 1

            event_info["LOID"]       = ""
            event_info["IndicoLink"] = doesExistIndicoLink(contribution)

            recordable_events.append(event_info)
            ctr_sc = 0
            for subcontribution in contribution.getSubContributionList():
                ctr_sc += 1
                event_info = {}
                speaker_str = ""
                speaker_list = subcontribution.getSpeakerList()

                if speaker_list is not None:
                    tag_first_iter = True
                    for speaker in speaker_list:
                        if tag_first_iter:
                            speaker_str = "%s %s" % (speaker_list[0].getFirstName(),
                                                     speaker_list[0].getFamilyName())
                        else:
                            speaker_str = "%s, %s %s" % \
                            (speaker_str, speaker.getFirstName(), speaker.getFamilyName())

                event_info["speakers"]   = speaker_str
                event_info["type"]       = "subcontribution"
                event_info["IndicoID"]   = generateIndicoID(conference = conference.getId(),
                                              session         = None,
                                              contribution    = contribution.getId(),
                                              subcontribution = subcontribution.getId())
                event_info["title"]      = subcontribution.getTitle()
                event_info["titleshort"] = truncate_str(event_info["title"], title_length)
                # Subcontribution objects don't have start dates,
                # so get the owner contribution's start date
                # and add the counter ctr_sc to that
                event_info["date"]     = int(mktime(subcontribution.getOwner().getStartDate().timetuple()) + ctr_sc)
                event_info["LOID"]       = ""
                event_info["IndicoLink"] = doesExistIndicoLink(subcontribution)

                recordable_events.append(event_info)

            if oneIsEnough:
                break
    if sort and not oneIsEnough:
        talks.sort(key = Contribution.contributionStartDateForSort)

    for session in conference.getSessionList():
        event_info = {}
        event_info["speakers"] = ""
        event_info["type"]     = "session"
        event_info["IndicoID"] = generateIndicoID(conference = conference.getId(),
                                                  session         = session.getId(),
                                                  contribution    = None,
                                                  subcontribution = None)
        event_info["title"]    = session.getTitle()
        event_info["titleshort"] = truncate_str(event_info["title"], title_length)
        # Get start time as seconds since the epoch so we can sort
        event_info["date"]     = int(mktime(session.getStartDate().timetuple()))
        event_info["LOID"]       = ""
        event_info["IndicoLink"] = doesExistIndicoLink(session)

        recordable_events.append(event_info)

    # Get list of matching IndicoIDs and CDS records from CDS
    cds_indico_matches = getCDSRecords(conference.getId())

    for event_info in recordable_events:
        try:
            event_info["CDS"] = cds_indico_matches[event_info["IndicoID"]]
        except KeyError:
            event_info["CDS"] = ""
            pass


    # Get list of matching IndicoID's and LOIDs from the Micala database
    existing_matches = getMatches(conference.getId())

    # insert any existing matches into the recordable_events array
    for talk in recordable_events:
        try:
            matching_LOID = existing_matches[talk["IndicoID"]]
        except KeyError:
            matching_LOID = ""

        if matching_LOID != "":
            talk["LOID"] = matching_LOID

    # Now that we have all the micala, CDS and IndicoLink info, set up the bg images
    for talk in recordable_events:
        talk["bg"]         = chooseBGImage(talk)

    # Next, sort the list of events by startDate for display purposes
    recordable_events.sort(startTimeCompare)

    return recordable_events

def startTimeCompare(a, b):
    '''This subroutine is for sorting the events, sessions,
    contributions and subcontributions correctly.
    Note: if a session and contribution have the exact same start time,
    then it must be the first contribution in the session, and we
    want to display the session first, so return the appropriate value to do that.'''

    if a["date"] > b["date"]:
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

def truncate_str(str, length):
    '''Truncates given string to the desired length and if it
    was longer than that, sticks ellipses on the end'''

    if len(str) < length:
        return str
    else:
        return str[:length] + "..."

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

    if session is not None:
        IndicoID = "%ds%d" % (int(conference), int(session))
    elif contribution is None:
        IndicoID = "%d" % (int(conference),)
    elif subcontribution is not None:
        IndicoID = "%dc%dsc%d" % (int(conference), int(contribution), int(subcontribution))
    else:
        IndicoID = "%dc%d" % (int(conference), int(contribution))

    return IndicoID

def parseIndicoID(IndicoID):
    """Given an "Indico ID" of the form shown above, determine whether it is
    a conference, subcontribution etc, and return that info with the individual IDs."""

    pConference      = re.compile('(\d+)$')
    pSession         = re.compile('(\d+)s(\d+)$')
    pContribution    = re.compile('(\d+)c(\d+)$')
    pSubcontribution = re.compile('(\d+)c(\d+)sc(\d+)$')

    mE  = pConference.match(IndicoID)
    mS  = pSession.match(IndicoID)
    mC  = pContribution.match(IndicoID)
    mSC = pSubcontribution.match(IndicoID)

    if mE:
        Logger.get('RecMan').info("searched %s, matched %s" % (IndicoID, 'conference'))
        return {'type':           'conference',
                'conference':     mE.group(1),
                'session':        '',
                'contribution':   '',
                'subcontribution':''}
    elif mS:
        Logger.get('RecMan').info("searched %s, matched %s" % (IndicoID, 'session'))
        return {'type':           'session',
                'conference':     mS.group(1),
                'session':        mS.group(2),
                'contribution':   '',
                'subcontribution':''}
    elif mC:
        Logger.get('RecMan').info("searched %s, matched %s" % (IndicoID, 'contribution'))
        return {'type':           'contribution',
                'conference':     mC.group(1),
                'session':        '',
                'contribution':   mC.group(2),
                'subcontribution':''}
    elif mSC:
        Logger.get('RecMan').info("searched %s, matched %s" % (IndicoID, 'subcontribution'))
        return {'type':           'subcontribution',
                'conference':     mSC.group(1),
                'session':        '',
                'contribution':   mSC.group(2),
                'subcontribution':mSC.group(3)}
    else:
        return None

def getMatches(confID):
    """For the current conference, get list from the database of IndicoID's already matched to Lecture Object."""

    try:
        connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                     port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                     user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                     passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                     db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
    except MySQLdb.Error, e:
        raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

    cursor = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute('''SELECT IndicoID, LOID FROM Lectures WHERE IndicoID LIKE "%s%%"''' % confID)
    connection.commit()
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    match_array = {}
    for row in rows:
        match_array[row["IndicoID"]] = row["LOID"]

    return (match_array)

def getOrphans():
    """Get list of Lecture Objects in the database that have no IndicoID assigned"""

    try:
        connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                     port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                     user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                     passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                     db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
    except MySQLdb.Error, e:
        raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

    cursor = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, LOID, IndicoID, Title, Creator FROM Lectures WHERE NOT IndicoID")
    connection.commit()
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    for lecture in rows:
        lecture["time"] = formatLOID(lecture["LOID"])[0]
        lecture["date"] = formatLOID(lecture["LOID"])[1]
        lecture["box"]  = formatLOID(lecture["LOID"])[2]

    return (rows)

def updateMicala(IndicoID, LOID):
    """Submit Indico ID to the micala DB"""

#    Logger.get('RecMan').exception("inside updateMicala.")

    try:
        connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                     port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                     user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBUser"),
                                     passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBPW"),
                                     db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
    except MySQLdb.Error, e:
        raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

    cursor = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("UPDATE Lectures SET IndicoID=%s WHERE id=%s",
                       (IndicoID, LOID))
        connection.commit()
    except MySQLdb.Error, e:
        raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

    cursor.close()
    connection.close()

def createCDSRecord(IndicoID, aw):
    '''Retrieve a MARC XML string for the given conference, then package it up and send it to CDS.'''

    # I don't understand what some of the following lines do. Pedro did some of it for me.
    xmlGen = XMLGen()
    xmlGen.initXml()
    di = DataInt(xmlGen)
#    og = outputGenerator(aw, dataInt=di)
    og = outputGenerator(aw, xmlGen)

    xmlGen.openTag("event")

    parsed = parseIndicoID(IndicoID)
    Logger.get('RecMan').info("IndicoID = %s", IndicoID)
    Logger.get('RecMan').info("parsed[conference] = %s", str(parsed["conference"]))

    conf = ConferenceHolder().getById(parsed["conference"])
    # setting source='RecordingManager' is how we identify ourselves to the outputGenerator
    # Nobody else should need to know this access information, and it shouldn't be accessible
    # to e.g. OAI harvesters outside CERN.
    if parsed["type"] == 'conference':
        Logger.get('RecMan').info("generating MARC XML for a conference")
#        og.confToXMLMarc21(conf, 1, 1, 1, forceCache=True, out=xmlGen, source='RecordingManager')
        og.confToXML(conf, 0, 0, 1, source='RecordingManager')
#        conf,includeSession,includeContribution,includeMaterial,showSession="all", showContribution="all", out=None, forceCache=False
    elif parsed["type"] == 'session':
        Logger.get('RecMan').info("generating MARC XML for a session (no such thing yet)")
        # there is no such method for sessions yet for some reason...
        # og.confToXMLMarc21(conf, 1, 1, 1, forceCache=True, out=xmlGen, source='RecordingManager')
        pass
    elif parsed["type"] == 'contribution':
        Logger.get('RecMan').info("generating MARC XML for a contribution")
        cont = conf.getContributionById(parsed["contribution"])
        og.contribToXMLMarc21(cont, includeMaterial=1, forceCache=True, out=xmlGen, source='RecordingManager')
#                              cont,includeMaterial=1, out=None, forceCache=False, source=None
    elif parsed["type"] == 'subcontribution':
        Logger.get('RecMan').info("generating MARC XML for a subcontribution")
        cont = conf.getContributionById(parsed["contribution"])
        subCont = cont.getSubContributionById(parsed["subcontribution"])
        og.subContribToXMLMarc21(subCont, includeMaterial=1, forceCache=True, out=xmlGen, source='RecordingManager')
#                                subCont,includeMaterial=1, out=None, forceCache=False, source=None
    else:
        Logger.get('RecMan').info("IndicoID = %s", IndicoID)

    xmlGen.closeTag("event")

    # Get the MARC XML
    marcxml = xmlGen.getXml()

    from MaKaC.common import Config

    outputData = ""
    stylepath = "%s/%s.xsl" % (Config.getInstance().getStylesheetsDir(),
                               'cds_marcxml_presentation')
    if os.path.exists(stylepath):
        try:
            Logger.get('RecMan').info("Trying to do XSLT using path %s" % stylepath)
            parser = XSLTransformer(stylepath)
            outputData = parser.process(marcxml)
        except:
            outputData = "Cannot parse stylesheet: %s" % sys.exc_info()[0]
    else:
        outputData = marcxml


    # temporary, for my own debugging
    f = open('/tmp/marc.xml', 'w')
    f.write(outputData)
    f.close()

    # Next step: submit this marc xml to CDS

    return True

def getCDSRecords(confId):
    '''Query CDS to see if it has an entry for the given event as well as all its sessions, contributions and subcontributions.
    If yes return a dictionary pairing CDS IDs with Indico IDs.'''

    # Slap a wildcard on the end of the ID to find the conference itself as well as all children.
    id_plus_wildcard = confId + "*"

    # Here is a help page describing the GET args,
    # if this CDS query needs to be changed (thanks jerome.caffaro@cern.ch):
    # http://invenio-demo.cern.ch/help/hacking/search-engine-api
    url = "http://cdsweb.cern.ch/search?p=sysno%%3A%%22INDICO.%s%%22&f=&action_search=Search&sf=&so=d&rm=&rg=1000&sc=1&ot=970&of=t&ap=0" \
        % (id_plus_wildcard)

    # This dictionary will contain CDS ID's, referenced by Indico ID's
    results = {}

    # perform the URL query to CDS. It contains one line for each CDS record,
    # of the form:
    # 001121974 970__ $$aINDICO.21917c22
    # The first number is the CDS record ID, with leading zeros
    # The second number is the MARC XML tag
    # The third string contains the Indico ID
    request = Request(url)
    f = urlopen(request)
    lines = f.readlines()
    f.close()

    for line in lines:
        print line,
        result = line.strip()
        if result != "":

            bigcdsid = result.split(" ")[0]
            CDSID = bigcdsid.lstrip("0")

            p = re.compile('INDICO\.([sc\d]+)')
            m = p.search(line)

            if m:
                IndicoID = m.group(1)
                results[IndicoID] = CDSID
            else:
                # If we end up here then probably something's wrong with the URL
                pass

#            results.append({"CDSID": CDSID, "IndicoID": IndicoID})

    return results

def createIndicoLink(IndicoID):
    """Create a link in Indico to the CDS record."""

    eventInfo = parseIndicoID(IndicoID)


def doesExistIndicoLink(obj):
    """This function will be called with a conference, session, contribution or subcontribution object.
    Each of those has a getAllMaterialList() method. Call that method and search for a title "Video in CDS"
    and make sure it has a link."""

    flagLinkFound = False

    materials = obj.getAllMaterialList()
    if materials is not None and len(materials) > 0:
        for mat in materials:
            if mat.getTitle() == "Video in CDS" and isinstance(mat.getMainResource(), Link):
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

def chooseBGImage(talk):
    """Given a talk dictionary, check if it has an LOID, CDS record, and IndicoLink.
    Pick the appropriate image RecordingManagerNNN.png to match that.
    This image will be used for the div background.
    """

    if talk["LOID"] != '':
        flagLOID = '1'
    else:
        flagLOID = '0'

    if talk["CDS"] != '':
        flagCDS = '1'
    else:
        flagCDS = '0'

    if talk["IndicoLink"] == True:
        flagIndicoLink = '1'
    else:
        flagIndicoLink = '0'

    return "/indico/images/RecordingManager%s%s%s.png" % (flagLOID, flagCDS, flagIndicoLink)

class RecordingManagerError(CSErrorBase):
    def __init__(self, operation, inner):
        CSErrorBase.__init__(self)
        self._operation = operation
        self._inner = inner

    @Retrieves(['MaKaC.plugins.Collaboration.RecordingManager.common.RecordingManagerError'], 'origin')
    def getOrigin(self):
        return 'RecordingManager'

    @Retrieves(['MaKaC.plugins.Collaboration.RecordingManager.common.RecordingManagerError'],
               'operation')
    def getOperation(self):
        return self._operation

    @Retrieves(['MaKaC.plugins.Collaboration.RecordingManager.common.RecordingManagerError'],
               'inner')
    def getInner(self):
        return str(self._inner)

    def getUserMessage(self):
        return ''

    def getLogMessage(self):
        return "Recording Request error for operation: " + str(self._operation) + ", inner exception: " + str(self._inner)


class RecordingManagerException(CollaborationServiceException):
    pass
