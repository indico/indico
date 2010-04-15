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

        Logger.get('RecMan').info('machine_name = %s' % machine_name)

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBReaderPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))

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

    def getIdTask(self, task_name):
        '''Look up ID of this task in database'''

        Logger.get('RecMan').info('task_name = [%s]' % task_name)

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

        if result_set is not None and len(result_set) > 0:
            idTask = result_set[0]
        else:
            idTask = result_set[0]

        cursor.close()
        connection.close()

        return(idTask)

    def getIdLecture(self, lecture_name, pattern_cern, pattern_umich):
        '''Look up ID of this lecture in database'''

        Logger.get('RecMan').info('lecture_name = [%s]' % lecture_name)

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

        if result_set is not None and len(result_set) > 0 and match_cern:
            Logger.get('RecMan').info("result_set: %s" % str(result_set))
            idLecture = result_set[0]
        elif result_set is not None and len(result_set) > 0 and match_umich:
            idLecture = result_set[0]
        else:
            idLecture = ''

        cursor.close()
        connection.close()

        return(idLecture)

    def createNewMicalaLecture(self, lecture_name, contentType, pattern_cern, pattern_umich):
        '''insert a record into the micala database for a new lecture'''

        Logger.get('RecMan').info('createNewMicalaLecture for [%s]' % lecture_name)

        if contentType == 'plain_video':
            micalaContentType = "PLAINVIDEO"
        elif contentType == 'web_lecture':
            micalaContentType = "WEBLECTURE"

        match_cern  = pattern_cern.search(lecture_name)
        match_umich = pattern_umich.search(lecture_name)

        try:
            connection = MySQLdb.connect(host   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBServer"),
                                         port   = int(CollaborationTools.getOptionValue("RecordingManager", "micalaDBPort")),
                                         user   = CollaborationTools.getOptionValue("RecordingManager", "micalaDBUser"),
                                         passwd = CollaborationTools.getOptionValue("RecordingManager", "micalaDBPW"),
                                         db     = CollaborationTools.getOptionValue("RecordingManager", "micalaDBName"))
        except MySQLdb.Error, e:
            raise RecordingManagerException("MySQL database error %d: %s" % (e.args[0], e.args[1]))


        # Depending on style of lecture ID, search under Michigan style column or CERN style column
        cursor = connection.cursor()

        if match_umich:
            Logger.get('RecMan').info("""INSERT INTO Lectures (LOID, contentType, DateCreated) VALUES(%s, %s, NOW());""" % (lecture_name, micalaContentType))
            cursor.execute("""INSERT INTO Lectures (LOID, contentType, DateCreated) VALUES(%s, %s, NOW());""", (lecture_name, micalaContentType))
        elif match_cern:
            Logger.get('RecMan').info("""INSERT INTO Lectures (IndicoID, contentType, DateCreated) VALUES(%s, %s, NOW());""" % (lecture_name, micalaContentType))
            cursor.execute("""INSERT INTO Lectures (IndicoID, contentType, DateCreated) VALUES(%s, %s, NOW());""", (lecture_name, micalaContentType))

        connection.commit()

        connection.close()

        return self.getIdLecture(lecture_name, pattern_cern, pattern_umich)

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
            Logger.get('RecMan').info(" CDS export pending for: %s" % row["IndicoID"])
            talk_array.append(row["IndicoID"])

        return talk_array

    def updateMicalaCDSExport(self, cds_indico_matches, cds_indico_pending):
        '''If there are records found in CDS but not yet listed in the micala database as COMPLETE, then update it.
        cds_indico_matches is a dictionary of key-value pairs { IndicoID1: CDSID1, IndicoID2: CDSID2, ... }
        cds_indico_pending is a list of IndicoIDs.'''

        for pending in cds_indico_pending:
            Logger.get('RecMan').info('Looping through cds_indico_pending: %s' % pending)
            try:
                new_record = cds_indico_matches[pending]
                idMachine = self.getIdMachine(CollaborationTools.getOptionValue("RecordingManager", "micalaDBMachineName"))
                idTask    = self.getIdTask(CollaborationTools.getOptionValue("RecordingManager", "micalaDBStatusExportCDS"))
                import re
                pattern_cern  = re.compile('([sc\d]+)$')
                pattern_umich = re.compile('(\d+\-[\w\d]+\-\d)$')
                idLecture = self.getIdLecture(pending, pattern_cern, pattern_umich)
                self.reportStatus("COMPLETE", "CDS record: %s" % new_record, idMachine, idTask, idLecture)

                # I should still update the Lectures table to add the CDS record

            except KeyError:
                # current pending lecture still not found in CDS so do nothing.
                pass

