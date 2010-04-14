from MaKaC.plugins.Collaboration.RecordingManager.exceptions import RecordingManagerException
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.logger import Logger

import MySQLdb

class MicalaCommunication():
    def _init_(self):
        pass

    def getIp(self):
        '''This should return the IP of the current machine.'''
        return("")

    def getIdMachine(self, machine_name):
        '''Look up ID of this machine in database'''

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

        cursor = connection.cursor()
        cursor.execute("""SELECT id,Hostname FROM Machines WHERE Hostname = %s""",
            (machine_name,))
        connection.commit()

        result_set = cursor.fetchone()

        idMachine = result_set[0]

        cursor.close()
        connection.close()

        return(idMachine)

    def getIdTask(self, task_name):
        '''Look up ID of this task in database'''

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

        cursor = connection.cursor()
        cursor.execute("""SELECT id,Name FROM Tasks WHERE Name = %s""",
            (task_name,))
        connection.commit()

        result_set = cursor.fetchone()

        idTask = result_set[0]

        cursor.close()
        connection.close()

        return(idTask)

    def getIdLecture(self, lecture_name, pattern_cern, pattern_umich):
        '''Look up ID of this lecture in database'''

        match_cern  = pattern_cern.search(lecture_name)
        match_umich = pattern_umich.search(lecture_name)

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))


        # Depending on style of lecture ID, search under Michigan style column or CERN style column
        cursor = connection.cursor()
        cursor.execute("""SELECT id,LOID,IndicoID FROM Lectures WHERE LOID = %s OR IndicoID = %s""",
            (lecture_name, lecture_name))
        connection.commit()

        result_set = cursor.fetchone()

        idLecture = result_set[0]

        cursor.close()
        connection.close()

        return(idLecture)

    def getMatches(self, confID):
        '''For the current conference, get list from the database of IndicoID's already matched to Lecture Object.'''

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

    def reportStatus(self, status, message, idMachine, idTask, idLecture):
        '''Make status report to the database'''

        if idLecture == '':
            idLecture = None

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

        cursor = connection.cursor()
        cursor.execute("""INSERT INTO Status
            (idMachine, idTask, idLecture, Status, Message, Time)
            VALUES(%s, %s, %s, %s, %s, NOW());""", \
                       (idMachine, idTask, idLecture, status, message))
        cursor.close()

        connection.commit()
        connection.close()

    # WHO THE HELL CALLS THIS?!
    def updateMicala(self, IndicoID, contentType, LOID):
        """Submit Indico ID to the micala DB"""

    #    Logger.get('RecMan').exception("inside updateMicala.")

        if contentType == 'web_lecture':
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

        elif contentType == 'plain_video':
            # Should update the database here as well.
            # first need to backup the DB, create a new column called contentType
            # (I already created this column in micala.sql, just need to recreate DB from this file)
            pass

    def getCDSPending(self, confId, cds_indico_matches):
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

        # the following command is not necessarily what I want. I already have the list of existing CDS records.
        # Now I just need to know the IndicoID's for whom the export was started not finished.
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
        for row in rows:
            Logger.get('RecMan').info("Started CDS export for: %s" % row["L.IndicoID"])
            talk_array.push(row["L.IndicoID"])

        return talk_array