from MaKaC.plugins.Collaboration.RecordingManager.exceptions import RecordingManagerException
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.logger import Logger

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
        cursor.execute("""SELECT id,Hostname FROM Machines WHERE Hostname = %s""",
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
        cursor.execute("""SELECT id,Name FROM Tasks WHERE Name = %s""",
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
        cursor.execute("""SELECT id,LOID,IndicoID FROM Lectures WHERE LOID = %s OR IndicoID = %s""",
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
#            Logger.get('RecMan').debug("""INSERT INTO Lectures (IndicoID, contentType, DateCreated) VALUES(%s, %s, NOW());""" % (lecture_name, micalaContentType))
            cursor.execute("""INSERT INTO Lectures (IndicoID, contentType, DateCreated) VALUES(%s, %s, NOW());""", (lecture_name, micalaContentType))
        elif contentType == "web_lecture":
            micalaContentType = "WEBLECTURE"
#            Logger.get('RecMan').debug("""INSERT INTO Lectures (LOID, contentType, DateCreated) VALUES(%s, %s, NOW());""" % (lecture_name, micalaContentType))
            cursor.execute("""INSERT INTO Lectures (LOID, contentType, DateCreated) VALUES(%s, %s, NOW());""", (lecture_name, micalaContentType))

        connection.commit()

        connection.close()

        return cls.getIdLecture(lecture_name)

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
        cursor.execute('''SELECT IndicoID, LOID, ContentType FROM Lectures WHERE IndicoID LIKE "%s%%"''' % confID)
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
            if row["ContentType"] == 'WEBLECTURE' and row["LOID"] is not None:
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
        cursor.execute("""INSERT INTO Status
            (idMachine, idTask, idLecture, Status, Message, DateReported)
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

        try:
            cursor.execute("UPDATE Lectures SET IndicoID=%s, contentType=%s WHERE id=%s",
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
    def getCDSPending(cls, confId, cds_indico_matches):
        """Query the Micala database to find Indico IDs whose MARC has been exported to CDS, but no CDS record exists yet.
        Return a list of these Indico IDs."""

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

        cursor = connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # The following query returns the IndicoID's for which the metadata export task was started.
        # Whether it was finished we will find out separately by querying CDS to see what records have been created.
        cursor.execute('''SELECT L.id, L.LOID, L.IndicoID,
            T.id, T.Name,
            S.idLecture, S.idTask, S.Status, S.Message
            FROM Lectures L, Tasks T, Status S
            WHERE ( L.id = S.idLecture)
            AND S.Status = 'START'
            AND T.Name = '%s'
            AND T.id = S.idTask
            AND L.IndicoID LIKE "%s%%"''' % \
                       (CollaborationTools.getOptionValue("RecordingManager", "micalaDBStatusExportCDS"),
                       confId))

        connection.commit()
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        talk_array = []
        # Now we need to eliminate from our list those talks listed in cds_indico_matches.
        # Those are not pending.
        for row in rows:
            try:
                # check to see if the IndicoID in question is to be found in the dictionary of matches
                # if it is found, that means the CDS record exists and there's nothing to do.
                existing_cds_record = cds_indico_matches[row["IndicoID"]]
#                Logger.get('RecMan').debug(" CDS export complete for: %s" % existing_cds_record)
                # Otherwise, if it is not found, that means the CDS record hasn't been created yet,
                # so add the IndicoID to the list of pending records.
            except KeyError:
#                Logger.get('RecMan').debug(" CDS export pending for: %s" % row["IndicoID"])
                talk_array.append(row["IndicoID"])

        return talk_array

    @classmethod
    def updateMicalaCDSExport(cls, cds_indico_matches, cds_indico_pending):
        '''If there are records found in CDS but not yet listed in the micala database as COMPLETE, then update it.
        cds_indico_matches is a dictionary of key-value pairs { IndicoID1: CDSID1, IndicoID2: CDSID2, ... }
        cds_indico_pending is a list of IndicoIDs.'''

#        Logger.get('RecMan').debug('in updateMicalaCDSExport()')

        # debugging:
#        for matched in cds_indico_matches.keys():
#            Logger.get('RecMan').debug('Looping through cds_indico_matches: %s -> %s' % (matched, cds_indico_matches[matched]))
#        for pending in cds_indico_pending:
#            Logger.get('RecMan').debug('Looping through cds_indico_pending: %s' % pending)


        for pending in cds_indico_pending:
#            Logger.get('RecMan').debug('Looping through cds_indico_pending: %s (and looking up in cds_indico_matches)' % pending)
            try:
                new_record = cds_indico_matches[pending]
                idMachine = cls.getIdMachine(CollaborationTools.getOptionValue("RecordingManager", "micalaDBMachineName"))
                idTask    = cls.getIdTask(CollaborationTools.getOptionValue("RecordingManager", "micalaDBStatusExportCDS"))
                idLecture = cls.getIdLecture(pending)
                cls.reportStatus("COMPLETE", "CDS record: %s" % new_record, idMachine, idTask, idLecture)

                # I should still update the Lectures table to add the CDS record

            except KeyError:
                # current pending lecture still not found in CDS so do nothing.
                Logger.get('RecMan').debug('%s listed as pending and not found in cds_indico_matches, so it must still be pending.' % pending)

