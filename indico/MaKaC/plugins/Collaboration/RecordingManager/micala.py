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

from MaKaC.plugins.Collaboration.RecordingManager.exceptions import RecordingManagerException
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.logger import Logger
import re

try:
    import MySQLdb
except ImportError:
    Logger.get("RecMan").debug("Cannot import MySQLdb")

class MicalaCommunication(object):

    @classmethod
    def getIp(cls):
        '''This should return the IP of the current machine.'''
        return("")

    @classmethod
    def getIdMachine(cls, machine_name):
        '''Look up ID of this machine in database'''

#        Logger.get('RecMan').debug('in getIdMachine(), machine_name = %s' % machine_name)

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException(_("MySQL database error %d: %s") % (e.args[0], e.args[1]))

        cursor = connection.cursor()
        # believe it or not, the comma following machine_name is supposed to be there for MySQLdb's sake
        cursor.execute("""SELECT idMachine, hostname FROM machines WHERE hostname = %s""",
            (machine_name,))
        connection.commit()

        result_set = cursor.fetchone()


        if result_set is not None and len(result_set) > 0:
            idMachine = result_set[0]
        else:
            idMachine = ''

        cursor.close()
        connection.close()

        return(idMachine)

    @classmethod
    def getIdTask(cls, task_name):
        '''Look up ID of this task in database'''

#        Logger.get('RecMan').debug('task_name = [%s]' % task_name)

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException(_("MySQL database error %d: %s") % (e.args[0], e.args[1]))

        cursor = connection.cursor()
        cursor.execute("""SELECT idTask, name FROM tasks WHERE name = %s""",
            (task_name,))
        connection.commit()

        result_set = cursor.fetchone()

        if result_set is not None and len(result_set) > 0:
            idTask = result_set[0]
        else:
            idTask = result_set[0]

        cursor.close()
        connection.close()

        return(idTask)

    @classmethod
    def getIdLecture(cls, lecture_name):
        '''Look up internal database ID of the given lecture'''

#        Logger.get('RecMan').debug('lecture_name = [%s]' % lecture_name)

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException(_("MySQL database error %d: %s") % (e.args[0], e.args[1]))


        # Depending on style of lecture ID, search under Michigan style column or CERN style column
        cursor = connection.cursor()
        cursor.execute("""SELECT idLecture, LOID, IndicoID FROM lectures WHERE LOID = %s OR IndicoID = %s""",
            (lecture_name, lecture_name))
        connection.commit()

        result_set = cursor.fetchone()

        if result_set is not None and len(result_set) > 0:
#            Logger.get('RecMan').debug("result_set: %s" % str(result_set))
            idLecture = result_set[0]
        else:
            idLecture = ''

        cursor.close()
        connection.close()

        return(idLecture)

    @classmethod
    def isTaskComplete(cls, idLecture, idTask):
        '''Check to see if given task has been completed for the given lecture.'''

        flagComplete = False

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException(_("MySQL database error %d: %s") % (e.args[0], e.args[1]))


        # Check to see if the given task for the given lecture has status 'COMPLETE'.
        # If not then an empty set will be returned.
        cursor = connection.cursor()
        cursor.execute("""SELECT L.LOID
        FROM lectures L, lectureLatestStatus LS, status S
           WHERE L.idLecture = %s
           AND L.idLecture = LS.idLecture
           AND LS.idTask = %s
           AND LS.idStatus = S.idStatus
           AND S.status = 'COMPLETE'""",
            (idLecture, idTask))
        connection.commit()

        result_set = cursor.fetchone()

        if result_set is not None and len(result_set) > 0:
            flagComplete = True
        else:
            flagComplete = False

        cursor.close()
        connection.close()

        return(flagComplete)

    @classmethod
    def createNewMicalaLecture(cls, lecture_name, contentType):
        '''insert a record into the micala database for a new lecture'''

#        Logger.get('RecMan').debug('createNewMicalaLecture for [%s]' % lecture_name)

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException(_("MySQL database error %d: %s") % (e.args[0], e.args[1]))

        cursor = connection.cursor()

        if contentType == "plain_video":
            micalaContentType = "PLAINVIDEO"
#            Logger.get('RecMan').debug("""INSERT INTO Lectures (IndicoID, contentType, dateCreated) VALUES(%s, %s, NOW());""" % (lecture_name, micalaContentType))
            cursor.execute("""INSERT INTO lectures (IndicoID, contentType, dateCreated) VALUES(%s, %s, NOW());""", (lecture_name, micalaContentType))
        elif contentType == "web_lecture":
            micalaContentType = "WEBLECTURE"
#            Logger.get('RecMan').debug("""INSERT INTO Lectures (LOID, contentType, dateCreated) VALUES(%s, %s, NOW());""" % (lecture_name, micalaContentType))
            cursor.execute("""INSERT INTO lectures (LOID, contentType, dateCreated) VALUES(%s, %s, NOW());""", (lecture_name, micalaContentType))

        connection.commit()

        connection.close()

        return cls.getIdLecture(lecture_name)

    @classmethod
    def updateLectureInfo(cls, idLecture, lectureTitle, lectureSpeakers):
        '''Update basic info in micala DB for convenience in identifying records.'''

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException(_("MySQL database error %d: %s") % (e.args[0], e.args[1]))

        cursor = connection.cursor()

        cleanedLectureTitle    = cls.cleanSQLData(lectureTitle)
        cleanedLectureSpeakers = cls.cleanSQLData(lectureSpeakers)

        Logger.get('RecMan').info("""UPDATE lectures SET title = %s, creator = %s WHERE idLecture = %s""" % (cleanedLectureTitle, cleanedLectureSpeakers, idLecture))

        cursor.execute("""UPDATE lectures SET title = %s, creator = %s WHERE idLecture = %s""", \
                       (cleanedLectureTitle, cleanedLectureSpeakers, idLecture))

        connection.commit()

        connection.close()

        return ()

    @classmethod
    def getMatches(cls, confID):
        '''For the current conference, get list from the database of IndicoID's already matched to Lecture Objects.'''

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException(_("MySQL database error %d: %s") % (e.args[0], e.args[1]))

        cursor = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute('''SELECT IndicoID, LOID, contentType FROM lectures WHERE IndicoID LIKE "%s%%"''' % confID)
        connection.commit()
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        # Build dictionary of matches
        match_array = {}
        for row in rows:
            # We are only interested in reporting on lecture object matches here,
            # not whether plain video talks are in the micala database.
            # Also, it shouldn't ever happen, but ignore records in the micala DB with ContentType WEBLECTURE
            # that don't have a LOID.
            # LOID = NULL in the MySQL database translates in Python to being None.
            if row["contentType"] == 'WEBLECTURE' and row["LOID"] is not None:
                match_array[row["IndicoID"]] = row["LOID"]

        return (match_array)

    @classmethod
    def reportStatus(cls, status, message, idMachine, idTask, idLecture):
        '''Make status report to the database'''

#        Logger.get('RecMan').debug('in reportStatus()')

        if idLecture == '':
            idLecture = None

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException(_("MySQL database error %d: %s") % (e.args[0], e.args[1]))

        cursor = connection.cursor()
        cursor.execute("""INSERT INTO status
            (idMachine, idTask, idLecture, status, message, dateReported)
            VALUES(%s, %s, %s, %s, %s, NOW());""", \
                       (idMachine, idTask, idLecture, status, message))
        cursor.close()

        connection.commit()
        connection.close()

    @classmethod
    def associateIndicoIDToLOID(cls, IndicoID, LODBID):
        """Update the micala DB to associate the given talk with the given LOID"""

        # Initialize success flag and result string
        flagSuccess = True
        result      = ""

#        Logger.get('RecMan').debug("in associateIndicoIDToLOID()")

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            flagSuccess = False
            result += _("MySQL error %d: %s") % (e.args[0], e.args[1])
        except Exception, e:
            flagSuccess = False
            result += _("Unknown error %d: %s") % (e.args[0], e.args[1])

        cursor = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        Logger.get('RecMan').info("UPDATE lectures SET IndicoID=%s, contentType=%s WHERE idLecture=%s" % (IndicoID, "WEBLECTURE", LODBID))

        try:
            cursor.execute("UPDATE lectures SET IndicoID=%s, contentType=%s WHERE idLecture=%s",
                           (IndicoID, "WEBLECTURE", LODBID))
            connection.commit()
        except MySQLdb.Error, e:
            flagSuccess = False
            result += _("MySQL error %d: %s") % (e.args[0], e.args[1])
        except Exception, e:
            flagSuccess = False
            result += _("Unknown error %d: %s") % (e.args[0], e.args[1])

        cursor.close()
        connection.close()

        return {"success": flagSuccess, "result": result}

    @classmethod
    def associateCDSRecordToLOID(cls, CDSID, LODBID):
        """Update the micala DB to associate the CDS record number with the given lecture.
        Note: if you are using cdsdev, the CDSID stored in the micala database will be the cdsdev record, not the cds record.
        The micala database doesn't know the difference between cds and cdsdev. So if you create a bunch of test records and
        then want to go back and create them again in CDS, you'll have to tinker around with the micala database,
        deleting some status records and probably re-publish those lectures from the beginning."""

        # Initialize success flag and result string
        flagSuccess = True
        result      = ""

#        Logger.get('RecMan').debug("in associateIndicoIDToLOID()")

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            flagSuccess = False
            result += _("MySQL error %d: %s") % (e.args[0], e.args[1])
        except Exception, e:
            flagSuccess = False
            result += _("Unknown error %d: %s") % (e.args[0], e.args[1])

        cursor = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        try:
            cursor.execute("UPDATE lectures SET CDSRecord=%s WHERE idLecture=%s",
                           (CDSID, LODBID))
            connection.commit()
        except MySQLdb.Error, e:
            flagSuccess = False
            result += _("MySQL error %d: %s") % (e.args[0], e.args[1])
        except Exception, e:
            flagSuccess = False
            result += _("Unknown error %d: %s") % (e.args[0], e.args[1])

        cursor.close()
        connection.close()

        return {"success": flagSuccess, "result": result}

    @classmethod
    def getCDSPending(cls, confId):
        """Query the Micala database to find Indico IDs whose MARC has been exported to CDS, but not marked as completed in the micala DB.
        (Note: they may have just been completed, but we'll deal with newly completed tasks separately)
         Return a list of these Indico IDs."""

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

        cursorTaskStarted = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # The following query returns the IndicoID's for which the metadata export task was started.
        # Whether it was finished we will find out separately by querying CDS to see what records have been created.
        cursorTaskStarted.execute('''SELECT IndicoID, LOID, name, status FROM viewStatusComprehensive
                        WHERE status = 'START'
                        AND name = "%s"
                        AND IndicoID LIKE "%s%%"'''  % \
                       (CollaborationTools.getOptionValue("RecordingManager", "micalaDBStatusExportCDS"),
                       confId))

        connection.commit()
        rowsStarted = cursorTaskStarted.fetchall()
        cursorTaskStarted.close()

        # Do another query to get list of IndicoIDs marked as completed
        cursorTaskComplete = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # The following query returns the IndicoID's for which the metadata export task is COMPLETE.
        cursorTaskComplete.execute('''SELECT IndicoID, LOID, name, status FROM viewStatusComprehensive
                        WHERE status = 'COMPLETE'
                        AND name = "%s"
                        AND IndicoID LIKE "%s%%"'''  % \
                       (CollaborationTools.getOptionValue("RecordingManager", "micalaDBStatusExportCDS"),
                       confId))

        connection.commit()
        rowsComplete = cursorTaskComplete.fetchall()
        cursorTaskComplete.close()

        connection.close()

        # Now from these queries, build two sets
        setStarted = set()
        setComplete = set()
        for row in rowsStarted:
            setStarted.add(row["IndicoID"])
        for row in rowsComplete:
            setComplete.add(row["IndicoID"])

        # Return a list containing the IndicoID's for whom the task was marked as started but not finished.
        return list(setStarted.difference(setComplete))

    @classmethod
    def updateMicalaCDSExport(cls, cds_indico_matches, cds_indico_pending):
        '''If there are records found in CDS but not yet listed in the micala database as COMPLETE, then update it.
        cds_indico_matches is a dictionary of key-value pairs { IndicoID1: CDSID1, IndicoID2: CDSID2, ... }
        cds_indico_pending is a list of IndicoIDs (for whom the CDS export task has been started but not completed).'''

#        Logger.get('RecMan').debug('in updateMicalaCDSExport()')

        # debugging:
#        for matched in cds_indico_matches.keys():
#            Logger.get('RecMan').debug('Looping through cds_indico_matches: %s -> %s' % (matched, cds_indico_matches[matched]))
#        for pending in cds_indico_pending:
#            Logger.get('RecMan').debug('Looping through cds_indico_pending: %s' % pending)


        for pending in cds_indico_pending:
#            Logger.get('RecMan').debug('Looping through cds_indico_pending: %s (and looking up in cds_indico_matches)' % pending)
            try:
                newRecord = cds_indico_matches[pending]

                idMachine = cls.getIdMachine(CollaborationTools.getOptionValue("RecordingManager", "micalaDBMachineName"))
                idTask    = cls.getIdTask(CollaborationTools.getOptionValue("RecordingManager", "micalaDBStatusExportCDS"))
                idLecture = cls.getIdLecture(pending)
                cls.reportStatus("COMPLETE", "CDS record: %s" % newRecord, idMachine, idTask, idLecture)

                # add the CDS record number to the Lectures table
                resultAssociateCDSRecord = cls.associateCDSRecordToLOID(newRecord, idLecture)
                if not resultAssociateCDSRecord["success"]:
                    Logger.get('RecMan').error("Unable to update Lectures table in micala database: %s" % resultAssociateCDSRecord["result"])
                    # this is not currently used:
                    return resultAssociateCDSRecord["result"]

            except KeyError:
                # current pending lecture still not found in CDS so do nothing.
                Logger.get('RecMan').debug('%s listed as pending and not found in cds_indico_matches, so it must still be pending.' % pending)

    @classmethod
    def cleanSQLData(cls, uncleanString):
        """Get rid of SQL-unfriendly chars."""

        # Truncate the string in case it is longer than 500 chars
        if len(uncleanString) > 500:
            uncleanString = uncleanString[0:500]

        # Replace all non-alphanumeric chars with spaces
        cleanString = re.sub("[^0-9a-zA-Z]", " ", uncleanString)

        return cleanString
