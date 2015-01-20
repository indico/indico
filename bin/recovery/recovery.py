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

import os
import sys
import shutil
from distutils import sysconfig
from datetime import datetime
import time
from indico.core.db import MigratedDB
from ZODB.FileStorage import FileStorage
import transaction
from indico.core.db import DBMgr
from indico.core.config import Config
from MaKaC.review import Abstract, AbstractStatusSubmitted, AbstractStatusAccepted,\
AbstractStatusRejected, AbstractStatusUnderReview, AbstractStatusProposedToAccept,\
AbstractStatusProposedToReject, AbstractStatusInConflict, AbstractStatusWithdrawn,\
AbstractStatusDuplicated, AbstractStatusMerged, AbstractAcceptance, AbstractRejection,\
AbstractReallocation, NotifTplCondAccepted
from MaKaC.conference import AccessController, LocalFile, Link, Paper, Slides,\
Video, Poster, Minutes, Material, SubContribParticipation, SubContribution,\
ContributionType, ContributionParticipation, Contribution, AcceptedContribution,\
SessionSlot, Session, Conference, ContribStatusWithdrawn, ContribStatusNotSch,\
ContribSchEntry
from MaKaC.schedule import BreakTimeSchEntry
from MaKaC.trashCan import TrashCanManager
from MaKaC.user import AvatarHolder
from MaKaC.participant import Participant
from MaKaC.domain import DomainHolder
from MaKaC.webinterface import displayMgr

# The folder that contains the current database file.
currentPath = Config.getInstance().getCurrentDBDir()

# The folder that contains the database backups.
backupsPath = Config.getInstance().getDBBackupsDir()

# The folder that contains temporary database files.
tmpPath = Config.getInstance().getTempDir()

# Name of the database file.
dataFile = "data.fs"

python = os.path.join(sysconfig.get_config_vars()["exec_prefix"], "python")
## TO BE CHANGED:
repozo = "/usr/bin/repozo.py"

def incPrintPrefix(pp):
# pp is a print prefix that is used to display the output messages in a
# "level way".
    return "%s| "%pp

class Logger:
# The logger is used to record all the output messages during a recovery.

    def __init__(self):
        self._log = []

    def log(self, text):
        self._log.append(text)

    def getLog(self):
        return "\n".join(self._log)

    def clearLog(self):
        del self._log
        self._log = []

    def createLogFile(self):
        f = file("recovery.log", 'w')
        f.write(self.getLog())
        f.close()

logger = Logger()

def log(text):
    print text
    logger.log(text)

class DatabaseRecovery:
# Recovery for a database.

    def __init__(self, dbm=None):
    # By default the recovery is performed on the current database.
        if dbm == None:
            dbm = DBMgr.getInstance()
        self._dbm = dbm

    def proceed(self, dt, pp=""):
    # Recovers the database as it was at the given dt. However, if there exist
    # backups of the database made after dt, it is more suitable to replace the
    # database with the first backup made after dt and then call this method
    # for it (less transactions to be undone => faster). If the database is
    # modified (new transactions added) during this process, the recovery will
    # fail. pp is a print prefix that is used to display the output messages in
    # a "level way".
        try:
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            ts = time.mktime(dt.timetuple())
            # Undo the transaction(s):
            log("%sRecovering database state..."%pp)
            i = 0; j = 0; stepNumber = 0;
            self._dbm.startRequest()
            ui = self._dbm.undoInfo(stepNumber)
            length = len(ui)
            if length < 1000:
                length -= 1
            while (i < length) and (ui[i]['time'] > ts):
                self._dbm.undo(ui[i]['id'])
                self._dbm.commit()
                i += 1
                if i == 1000:
                    stepNumber += 2 # Because of the added transactions
                                    # (by the commit).
                    ui = self._dbm.undoInfo(stepNumber)
                    length = len(ui)
                    if length < 1000:
                        length -= 1
                    i = 0
                j += 1
            log("%s%s transaction(s) successfully undone."%(pp, j))
            log("%sDatabase state (%s) successfully recovered in %s."%(pp, dt,\
            datetime.now()-now))
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while recovering the database state: %s"%(pp, msg))
            return

class PickleRecovery:
# Recovery for a pickle.

    def __init__(self, oid):
    # oid is the persistent id of the object for which we want to recover the
    # pickle.
        self._oid = oid
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, pp=""):
    # Recovers the pickle as it was at the given dt and returns it. pp is a
    # print prefix that is used to display the output messages in a "level way".
        try:
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering pickle..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            try:
                pickle = self._tmpdbm.loadObject(self._oid, '')[0]
                log("%sPickle successfully recovered in %s."%(pp, datetime.now()-now))
                return pickle
            except Exception, msg:
                log("%s*ERROR* while loading the pickle: %s"%(pp, msg))
                return
        except Exception, msg:
            log("%s*ERROR* while recovering the pickle: %s"%(pp, msg))
            return

class ObjectRecovery:
# Recovery for an object.

    def __init__(self, oid):
    # oid is the persistent id of the object that we want to recover.
        self._oid = oid
        self._pr = PickleRecovery(self._oid)
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, pp=""):
    # Recovers the object as it was at the given dt and returns it. pp is a
    # print prefix that is used to display the output messages in a "level way".
        try:
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering object..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            pickle = self._pr.proceed(dt, incPrintPrefix(pp))
            if pickle == None:
                raise Exception("Problem with the pickle.")
            recobj = self.reconstructObj(pickle, self._tmpdbm, incPrintPrefix(pp))
            if recobj:
                log("%sObject successfully recovered in %s."%(pp, datetime.now()-now))
                return recobj
            else:
                raise Exception("Object couldn't be reconstructed.")
        except Exception, msg:
            log("%s*ERROR* while recovering the object: %s"%(pp, msg))
            return

    def reconstructObj(self, pickle, dbm, pp=""):
    # Reconstructs the object given its pickle and a database manager and
    # returns it. The reconstructed object may contain subobjects that may
    # themselves need to be extracted from the database, that's why the dbm
    # has to be specified. pp is a print prefix that is used to display the
    # output messages in a "level way".
        log("%sReconstructing object..."%pp)
        try:
            objread = None
            try:
                from ZODB.serialize import ObjectReader as objread
            except ImportError:
                from ZODB.serialize import ConnectionObjectReader as objread
            reader = objread(dbm.getDBConnection(), dbm.getDBConnCache(),\
            dbm.getDBClassFactory())
            # Reconstruction of the object:
            recobj=reader.getGhost(pickle)
            reader.setGhostState(recobj, pickle)
            log("%sObject successfully reconstructed."%pp)
            return recobj
        except Exception, msg:
            log("%s*ERROR* while reconstructing the object: %s"%(pp, msg))
            return

class AccessControllerRecovery:
# Recovery for an access controller.

    def __init__(self, ac):
    # ac is the access controller that we want to recover.
        self._ac = ac
        self._dbm = DBMgr.getInstance()
        self._or = ObjectRecovery(self._ac._p_oid)
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, pp=""):
    # Recovers the access controller as it was at the given dt. pp is a print
    # prefix that is used to display the output messages in a "level way".
        try:
            if not isinstance(self._cont, AccessController):
                raise Exception("The given object is not an instance of AccessController.")
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering access controller..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            recac = self._or.proceed(dt, incPrintPrefix(pp))
            if ac == None:
                raise Exception("Problem with the object.")
            if self.setValues(recac, incPrintPrefix(pp)):
                self._dbm.commit()
                log("%sAccess controller successfully recovered in %s."%(pp, datetime.now()-now))
            else:
                raise Exception("Access controller values couldn't be set.")
        except Exception, msg:
            log("%s*ERROR* while recovering the access controller: %s"%(pp, msg))

    def setValues(self, recoveredAC, pp=""):
    # Sets the values of recoveredAC to self._ac (the current access controller).
    # pp is a print prefix that is used to display the output messages in a
    # "level way".
        try:
            log("%sSetting values for access controller..."%pp)
            # Set recovered values:
            self._ac.setProtection(recoveredAC.isItselfProtected())
            self._ac.setFatherProtection(recoveredAC.isFatherProtected())
            # Management recovery:
            for m in self._ac.getModifierList()[:]:
                self._ac.revokeModification(m)
            ah = AvatarHolder()
            for m in recoveredAC.getModifierList():
                log("%sGranting modification privilege for user \"%s\"..."%(incPrintPrefix(pp),\
                m.getEmail()))
                user = None
                try:
                    user = ah.getById(m.getId())
                except KeyError:
                    if ah.match({"email": m.getEmail()}):
                        user = ah.match({"email": m.getEmail()})[0]
                    else:
                        log("%sModification privilege cannot be granted because the user has been deleted."%incPrintPrefix(pp))
                if user:
                    self._ac.grantModification(user)
                    log("%sModification privilege successfully granted."%incPrintPrefix(pp))
            # Access recovery:
            for a in self._ac.getAccessList()[:]:
                self._ac.revokeAccess(a)
            for a in recoveredAC.getAccessList():
                log("%sGranting access privilege for user \"%s\"..."%(incPrintPrefix(pp),\
                a.getEmail()))
                user = None
                try:
                    user = ah.getById(a.getId())
                except Exception:
                    user = TrashCanManager().getById(a._p_oid)
                    ah.add(user)
                    TrashCanManager().remove(user)
                self._ac.grantAccess(user)
                log("%sAccess privilege successfully granted."%incPrintPrefix(pp))
            # Domain recovery:
            for d in self._ac.getRequiredDomainList()[:]:
                self._ac.freeDomain(d)
            dh = DomainHolder()
            for d in recoveredAC.getRequiredDomainList():
                log("%sAdding domain \"%s\" to requirered domains list..."%(incPrintPrefix(pp),\
                d.getName()))
                domain = None
                try:
                    domain = dh.getById(d.getId())
                except Exception:
                    domain = TrashCanManager().getById(d._p_oid)
                    dh.add(domain)
                    TrashCanManager().remove(domain)
                    domain.setName(d.getName())
                    domain.setDescription(d.getDescription())
                    domain.setFilterList(d.getFilterList())
                self._ac.requireDomain(domain)
                log("%sDomain successfully added."%incPrintPrefix(pp))
            self._ac.setAccessKey(recoveredAC.getAccessKey())
            self._dbm.commit(True)
            log("%sAccess controller values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the access controller values: %s"%(pp, msg))
            return

class MaterialRecovery:
# Recovery for a material.

    def __init__(self, mat):
    # mat is the material that we want to recover.
        self._mat = mat
        self._dbm = DBMgr.getInstance()
        self._or = ObjectRecovery(self._mat._p_oid)
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, pp=""):
    # Recovers the material as it was at the given dt. pp is a print prefix
    # that is used to display the output messages in a "level way".
        try:
            if not isinstance(self._mat, Material):
                raise Exception("The given object is not an instance of Material.")
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering material..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            recmat = self._or.proceed(dt, incPrintPrefix(pp))
            if recmat == None:
                raise Exception("Problem with the object.")
            if self.setValues(recmat, True, incPrintPrefix(pp)): # We merge the resources.
                self._dbm.commit()
                log("%sMaterial successfully recovered in %s."%(pp, datetime.now()-now))
            else:
                raise Exception("Material values couldn't be set.")
        except Exception, msg:
            log("%s*ERROR* while recovering the material: %s"%(pp, msg))

    def setValues(self, recoveredMat, merge=False, pp=""):
    # Sets the values of recoveredMat to self._mat (the current material). If
    # "merge" is true, the resources of the two materials are merged. pp is a
    # print prefix that is used to display the output messages in a "level way".
        try:
            log("%sSetting values for material \"%s\"..."%(pp, self._mat.getTitle()))
            # Set recovered values:
            self._mat.setTitle(recoveredMat.getTitle())
            self._mat.setDescription(recoveredMat.getDescription())
            currentRes = []
            if merge:
                for r in self._mat.getResourceList():
                    currentRes.append(r.getId())
            else:
            # Remove all the current resources:
                while len(self._mat.getResourceList()) > 0:
                    self._mat.removeResource(self._mat.getResourceList()[0])
            # Recovery of the old resources:
            i = 0
            for r in recoveredMat.getResourceList():
                log("%sRecovering resource \"%s\"..."%(incPrintPrefix(pp), r.getName()))
                if r.getId() in currentRes:
                    self._mat.removeResource(self._mat.getResourceById(r.getId()))
                res = TrashCanManager().getById(r._p_oid)
                if isinstance(r, LocalFile):
                    res.setFileName(r.getFileName(), False)
                elif isinstance(r, Link):
                    res.setURL(r.getURL())
                else:
                    log("%sThis resource is not a local file nor a link."%pp)
                    return
                res.setName(r.getName())
                res.setDescription(r.getDescription())
                self._mat.recoverResource(res) # Resource removed from trash
                                               # can here.
                acrec = AccessControllerRecovery(res.getAccessController())
                acrec.setValues(r.getAccessController(), incPrintPrefix(incPrintPrefix(pp)))
                i += 1
                log("%sResource successfully recovered."%incPrintPrefix(pp))
            if recoveredMat.getMainResource():
                self._mat.setMainResource(self._mat.getResourceById(recoveredMat.getMainResource().getId()))
            log("%s%s resource(s) successfully recovered."%(incPrintPrefix(pp), i))
            # Access control recovery:
            acr = AccessControllerRecovery(self._mat.getAccessController())
            acr.setValues(recoveredMat.getAccessController(), incPrintPrefix(pp))
            self._mat.notifyModification()
            self._dbm.commit(True)
            log("%sMaterial values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the material values: %s"%(pp, msg))
            return

class AbstractRecovery:
# Recovery for an abstract.

    def __init__(self, abs):
    # abs is the abstract that we want to recover.
        self._abs = abs
        self._dbm = DBMgr.getInstance()
        self._or = ObjectRecovery(self._abs._p_oid)
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, pp=""):
    # Recovers the abstract as it was at the given dt. pp is a print prefix
    # that is used to display the output messages in a "level way".
        try:
            if not isinstance(self._abs, Abstract):
                raise Exception("The given object is not an instance of Abstract.")
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering abstract..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            recabs = self._or.proceed(dt, incPrintPrefix(pp))
            if recabs == None:
                raise Exception("Problem with the object.")
            if self.setValues(recabs, incPrintPrefix(pp)):
                self._dbm.commit()
                log("%sAbstract successfully recovered in %s."%(pp, datetime.now()-now))
            else:
                raise Exception("Abstract values couldn't be set.")
        except Exception, msg:
            log("%s*ERROR* while recovering the abstract: %s"%(pp, msg))

    def setValues(self, recoveredA, pp=""):
    # Sets the values of recoveredA to self._abs (the current abstract). pp
    # is a print prefix that is used to display the output messages in a
    # "level way".
        try:
            log("%sSetting values for abstract \"%s\"..."%(pp, self._abs.getTitle()))
            # Set recovered values:
            self._abs.setTitle(recoveredA.getTitle())
            self._abs.setContent(recoveredA.getContent())
            try:
                self._abs.setSummary(recoveredA.getSummary())
            except:
                pass
            self._abs.setComments(recoveredA.getComments())
            self._abs._setSubmissionDate(recoveredA.getSubmissionDate())
            while len(self._abs.getMergeFromList()) > 0:
                self._abs.removeMergeFromAbstract(self._abs.getMergeFromList()[0])
            for m in recoveredA.getMergeFromList():
                a = self._abs.getOwner().getAbstractById(m.getId())
                if not a:
                    a = TrashCanManager().getById(m._p_oid)
                self._abs.addMergeFromAbstract(a)
            # Submitter recovery:
            if self._abs.getSubmitter():
                self._abs.getSubmitter().delete()
                self._abs._submitter = None
            s = recoveredA.getSubmitter()
            log("%sSetting values for submitter \"%s\"..."%(incPrintPrefix(pp),\
            s.getEmail()))
            su = TrashCanManager().getById(s._p_oid)
            self._abs.recoverSubmitter(su)
            su.setFromAbstractParticipation(s)
            log("%sSubmitter values successfully set."%incPrintPrefix(pp))
            # Primary author(s) recovery:
            self._abs.clearPrimaryAuthors()
            for a in recoveredA.getPrimaryAuthorList():
                log("%sSetting values for primary author \"%s\"..."%(incPrintPrefix(pp),\
                a.getEmail()))
                pa = TrashCanManager().getById(a._p_oid)
                self._abs.recoverPrimaryAuthor(pa)
                pa.setFromAbstractParticipation(a)
                log("%sPrimary author values successfully set."%incPrintPrefix(pp))
            # Co-author(s) recovery:
            self._abs.clearCoAuthors()
            for a in recoveredA.getCoAuthorList():
                log("%sSetting values for co-author \"%s\"..."%(incPrintPrefix(pp),\
                a.getEmail()))
                ca = TrashCanManager().getById(a._p_oid)
                self._abs.recoverCoAuthor(ca)
                ca.setFromAbstractParticipation(a)
                log("%sCo-author values successfully set."%incPrintPrefix(pp))
            # Speaker(s) recovery:
            self._abs.clearSpeakers()
            for s in recoveredA.getSpeakerList():
                log("%sSetting values for speaker \"%s\"..."%(incPrintPrefix(pp),\
                s.getEmail()))
                spk = self._abs.getAuthorById(s.getId())
                self._abs.addSpeaker(spk)
                spk.setFromAbstractParticipation(s)
                log("%sSpeaker values successfully set."%incPrintPrefix(pp))
            # Track(s) recovery:
            self._abs.clearTracks()
            tracks = []
            for t in recoveredA.getTrackList():
                track = self._abs.getConference().getTrackById(t.getId())
                if track:
                    tracks.append(track)
            self._abs.setTracks(tracks)
            # Judgement(s) recovery:
            self._abs._clearTrackRejections()
            self._abs._clearTrackAcceptances()
            self._abs._clearTrackReallocations()
            for t in recoveredA.getConference().getTrackList():
                if self._abs.getConference().getTrackById(t.getId()):
                    track = self._abs.getConference().getTrackById(t.getId())
                    recJud = recoveredA.getTrackJudgement(t)
                    if isinstance(recJud, AbstractAcceptance):
                        ah = AvatarHolder()
                        resp = None
                        try:
                            resp = ah.getById(recJud.getResponsible().getId())
                        except Exception:
                            resp = TrashCanManager().getById(recJud.getResponsible()._p_oid)
                        type = None
                        recType = recJud.getContribType()
                        if recType:
                            type = self._abs.getConference().getContribTypeById(recType.getId())
                        jud = AbstractAcceptance(track, resp, type)
                        jud.setComment(recJud.getComment())
                        jud.setDate(recJud.getDate())
                        self._abs._addTrackAcceptance(jud)
                    if isinstance(recJud, AbstractRejection):
                        ah = AvatarHolder()
                        resp = None
                        try:
                            resp = ah.getById(recJud.getResponsible().getId())
                        except Exception:
                            resp = TrashCanManager().getById(recJud.getResponsible()._p_oid)
                        jud = AbstractRejection(track, resp)
                        jud.setComment(recJud.getComment())
                        jud.setDate(recJud.getDate())
                        self._abs._addTrackRejection(jud)
                    if isinstance(recJud, AbstractReallocation):
                        ah = AvatarHolder()
                        resp = None
                        try:
                            resp = ah.getById(recJud.getResponsible().getId())
                        except Exception:
                            resp = TrashCanManager().getById(recJud.getResponsible()._p_oid)
                        propTracks = []
                        for tr in recJud.getProposedTrackList():
                            if self._abs.getConference().getTrackById(tr.getId()):
                                propTracks.append(self._abs.getConference().getTrackById(tr.getId()))
                        if propTracks == []:
                            pass
                        else:
                            jud = AbstractReallocation(track, resp, propTracks)
                            jud.setComment(recJud.getComment())
                            jud.setDate(recJud.getDate())
                            self._abs._addTrackReallocation(jud)
                    else: # No judgement for the track:
                        pass
            # Status recovery:
            if not isinstance(self._abs.getCurrentStatus(), AbstractStatusAccepted):
                status = None
                recStatus = recoveredA.getCurrentStatus()
                if isinstance(recStatus, AbstractStatusWithdrawn):
                    ah = AvatarHolder()
                    resp = None
                    try:
                        resp = ah.getById(recStatus.getResponsible().getId())
                    except Exception:
                        resp = TrashCanManager().getById(recStatus.getResponsible()._p_oid)
                    status = AbstractStatusWithdrawn(self._abs,resp,recStatus.getComments())
                elif isinstance(recStatus, AbstractStatusDuplicated):
                    ah = AvatarHolder()
                    resp = None
                    try:
                        resp = ah.getById(recStatus.getResponsible().getId())
                    except Exception:
                        resp = TrashCanManager().getById(recStatus.getResponsible()._p_oid)
                    orig = self._abs.getOwner().getAbstractById(recStatus.getOriginal().getId())
                    if not orig:
                        status = AbstractStatusSubmitted(self._abs)
                    else:
                        status = AbstractStatusDuplicated(self._abs,resp,orig,recStatus.getComments())
                elif isinstance(recStatus, AbstractStatusMerged):
                    ah = AvatarHolder()
                    resp = None
                    try:
                        resp = ah.getById(recStatus.getResponsible().getId())
                    except Exception:
                        resp = TrashCanManager().getById(recStatus.getResponsible()._p_oid)
                    target = self._abs.getOwner().getAbstractById(recStatus.getTargetAbstract().getId())
                    if not target:
                        status = AbstractStatusSubmitted(self._abs)
                    else:
                        status = AbstractStatusMerged(self._abs,resp,target,recStatus.getComments())
                elif isinstance(recStatus, AbstractStatusInConflict):
                    status = AbstractStatusInConflict(self._abs)
                elif isinstance(recStatus, AbstractStatusProposedToReject):
                    status = AbstractStatusProposedToReject(self._abs)
                elif isinstance(recStatus, AbstractStatusProposedToAccept):
                    if len(self._abs.getTrackAcceptanceList()) > 0:
                        status = AbstractStatusProposedToAccept(self._abs)
                    else:
                        status = AbstractStatusSubmitted(self._abs)
                elif isinstance(recStatus, AbstractStatusUnderReview):
                    status = AbstractStatusUnderReview(self._abs)
                elif isinstance(recStatus, AbstractStatusRejected):
                    ah = AvatarHolder()
                    resp = None
                    try:
                        resp = ah.getById(recStatus.getResponsible().getId())
                    except Exception:
                        resp = TrashCanManager().getById(recStatus.getResponsible()._p_oid)
                    status = AbstractStatusRejected(self._abs,resp,recStatus.getComments())
                elif isinstance(recStatus, AbstractStatusAccepted):
                    cont = self._abs.getConference().getContributionById(recStatus.getContribution().getId())
                    if cont:
                        ah = AvatarHolder()
                        resp = None
                        try:
                            resp = ah.getById(recStatus.getResponsible().getId())
                        except Exception:
                            resp = TrashCanManager().getById(recStatus.getResponsible()._p_oid)
                        track = None
                        recTrack = recStatus.getTrack()
                        if recTrack:
                            track = self._abs.getConference().getTrackById(recTrack.getId())
                        type = None
                        recType = recStatus.getType()
                        if recType:
                            type = self._abs.getConference().getContribTypeById(recType.getId())
                        status = AbstractStatusAccepted(self._abs,resp,track,type,recStatus.getComments())
                        status.setContribution(cont)
                        self._abs._setContribution(cont)
                    else:
                        log("%sThe contribution created from this abstract doesn't exist anymore."%incPrintPrefix(pp))
                        status = AbstractStatusSubmitted(self._abs)
                        self._abs._setContribution(None)
                else: # Status is "submitted":
                    status = AbstractStatusSubmitted(self._abs)
                    self._abs._setContribution(None)
                status._setDate(recStatus.getDate())
                self._abs.setCurrentStatus(status)
            # Other values' recovery:
            type = None
            if recoveredA.getContribType():
                recType = recoveredA.getContribType()
                type = self._abs.getConference().getContribTypeById(recType.getId())
                if not type:
                    type = TrashCanManager().getById(recType._p_oid)
                    type.setName(recType.getName())
                    type.setDescription(recType.getDescription())
                    type.setConference(self._abs.getConference())
                    self._abs.getConference().recoverContribType(type)
            self._abs.setContribType(type)
            self._abs.clearIntCommentList()
            for c in recoveredA.getIntCommentList():
                comm = TrashCanManager().getById(c._p_oid)
                comm.setContent(c.getContent())
                comm._notifyModification(c.getModificationDate())
                self._abs.recoverIntComment(comm)
            notLog = self._abs.getNotificationLog()
            recNotLog = recoveredA.getNotificationLog()
            notLog.clearEntryList()
            for e in recNotLog.getEntryList():
                ent = TrashCanManager().getById(e._p_oid)
                ent._setDate(e.getDate())
                ah = AvatarHolder()
                resp = None
                try:
                    resp = ah.getById(e.getResponsible().getId())
                except Exception:
                    resp = TrashCanManager().getById(e.getResponsible()._p_oid)
                tpl = self._abs.getOwner().getNotificationTplById(e.getTpl().getId())
                if not tpl:
                    tpl = TrashCanManager().getById(e.getTpl()._p_oid)
                ent._setTpl(tpl)
                notLog.recoverEntry(ent)
            self._abs._notifyModification(recoveredA.getModificationDate())
            self._dbm.commit(True)
            log("%sAbstract values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the abstract values: %s"%(pp, msg))
            return
class SubContributionRecovery:
# Recovery for a subcontribution.

    def __init__(self, subcont):
    # subcont is the subcontribution that we want to recover.
        self._subcont = subcont
        self._dbm = DBMgr.getInstance()
        self._or = ObjectRecovery(self._subcont._p_oid)
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, pp=""):
    # Recovers the subcontribution as it was at the given dt. pp is a print
    # prefix that is used to display the output messages in a "level way".
        try:
            if not isinstance(self._subcont, SubContribution):
                raise Exception("The given object is not an instance of SubContribution.")
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering subcontribution..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            recsubcont = self._or.proceed(dt, incPrintPrefix(pp))
            if recsubcont == None:
                raise Exception("Problem with the object.")
            if self.setValues(recsubcont, incPrintPrefix(pp)):
                self._dbm.commit()
                log("%sSubcontribution successfully recovered in %s."%(pp, datetime.now()-now))
            else:
                raise Exception("Subcontribution values couldn't be set.")
        except Exception, msg:
            log("%s*ERROR* while recovering the subcontribution: %s"%(pp, msg))

    def setValues(self, recoveredSC, pp=""):
    # Sets the values of recoveredSC to self._subcont (the current
    # subcontribution). pp is a print prefix that is used to display the output
    # messages in a "level way".
        try:
            log("%sSetting values for subcontribution \"%s\"..."%(pp, self._subcont.getTitle()))
            # Set recovered values:
            self._subcont.setTitle(recoveredSC.getTitle())
            self._subcont.setDescription(recoveredSC.getDescription())
            self._subcont.setDuration(None, dur=recoveredSC.getDuration())
            # Speaker(s) recovery:
            while len(self._subcont.getSpeakerList()) > 0:
                self._subcont.removeSpeaker(self._subcont.getSpeakerList()[0])
            for s in recoveredSC.getSpeakerList():
                log("%sSetting values for speaker \"%s\"..."%(incPrintPrefix(pp),\
                s.getEmail()))
                spk = TrashCanManager().getById(s._p_oid)
                self._subcont.recoverSpeaker(spk)
                spk.setDataFromSpeaker(s)
                log("%sSpeaker values successfully set."%incPrintPrefix(pp))
            self._subcont.setSpeakerText(recoveredSC.getSpeakerText())
            # Material(s) recovery:
            while len(self._subcont.getMaterialList()) > 0:
                self._subcont.removeMaterial(self._subcont.getMaterialList()[0])
            for m in recoveredSC.getMaterialList():
                mat = TrashCanManager().getById(m._p_oid)
                self._subcont.recoverMaterial(mat)
                mr = MaterialRecovery(mat)
                mr.setValues(m, pp=incPrintPrefix(pp))
            # Paper recovery:
            self._subcont.removePaper()
            if recoveredSC.getPaper():
                p = TrashCanManager().getById(recoveredSC.getPaper()._p_oid)
                self._subcont.recoverPaper(p)
                mr = MaterialRecovery(p)
                mr.setValues(recoveredSC.getPaper(), pp=incPrintPrefix(pp))
            # Slides recovery:
            self._subcont.removeSlides()
            if recoveredSC.getSlides():
                s = TrashCanManager().getById(recoveredSC.getSlides()._p_oid)
                self._subcont.recoverSlides(s)
                mr = MaterialRecovery(s)
                mr.setValues(recoveredSC.getSlides(), pp=incPrintPrefix(pp))
            # Video recovery:
            self._subcont.removeVideo()
            if recoveredSC.getVideo():
                v = TrashCanManager().getById(recoveredSC.getVideo()._p_oid)
                self._subcont.recoverVideo(v)
                mr = MaterialRecovery(v)
                mr.setValues(recoveredSC.getVideo(), pp=incPrintPrefix(pp))
            # Poster recovery:
            self._subcont.removePoster()
            if recoveredSC.getPoster():
                p = TrashCanManager().getById(recoveredSC.getPoster()._p_oid)
                self._subcont.recoverPoster(p)
                mr = MaterialRecovery(p)
                mr.setValues(recoveredSC.getPoster(), pp=incPrintPrefix(pp))
            # Minutes recovery:
            self._subcont.removeMinutes()
            if recoveredSC.getMinutes():
                m = TrashCanManager().getById(recoveredSC.getMinutes()._p_oid)
                self._subcont.recoverMinutes(m)
                mr = MaterialRecovery(m)
                mr.setValues(recoveredSC.getMinutes(), pp=incPrintPrefix(pp))
            self._subcont.notifyModification()
            self._dbm.commit(True)
            log("%sSubcontribution values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the subcontribution values: %s"%(pp, msg))
            return

class ContributionRecovery:
# Recovery for a contribution.

    def __init__(self, cont):
    # cont is the contribution that we want to recover. The session, the track
    # and the schedule of the contribution are not recovered. This means that it
    # is left in its current context and timetable (same duartion), but all the
    # attributes are recovered.
        self._cont = cont
        self._dbm = DBMgr.getInstance()
        self._or = ObjectRecovery(self._cont._p_oid)
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, pp=""):
    # Recovers the contribution as it was at the given dt. pp is a print prefix
    # that is used to display the output messages in a "level way".
        try:
            if not isinstance(self._cont, Contribution):
                raise Exception("The given object is not an instance of Contribution.")
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering contribution..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            reccont = self._or.proceed(dt, incPrintPrefix(pp))
            if reccont == None:
                raise Exception("Problem with the object.")
            if self.setValues(reccont, incPrintPrefix(pp)):
                self._dbm.commit()
                log("%sContribution successfully recovered in %s."%(pp, datetime.now()-now))
            else:
                raise Exception("Contribution values couldn't be set.")
        except Exception, msg:
            log("%s*ERROR* while recovering the contribution: %s"%(pp, msg))

    def setValues(self, recoveredC, pp=""):
    # Sets the values of recoveredC to self._cont (the current contribution).
    # pp is a print prefix that is used to display the output messages in a
    # "level way".
        try:
            log("%sSetting values for contribution \"%s\"..."%(pp, self._cont.getTitle()))
            # Set recovered values:
            locationName = ""
            locationAddress = ""
            if recoveredC.getOwnLocation():
                locationName = recoveredC.getOwnLocation().getName()
                locationAddress = recoveredC.getOwnLocation().getAddress()
            roomName = ""
            try:
                summary = recoveredC.getSummary()
            except:
                summary = ""
            if recoveredC.getOwnRoom():
                roomName = recoveredC.getOwnRoom().getName()
            self._cont.setValues({"title": recoveredC.getTitle(), "description":\
            recoveredC.getDescription(), "summary": summary, "locationName":\
            locationName, "locationAddress": locationAddress, "roomName": roomName, "durTimedelta":\
            self._cont.getDuration(), "boardNumber": recoveredC.getBoardNumber()}, 0, 0)
            # Primary author(s) recovery:
            while len(self._cont.getPrimaryAuthorList()) > 0:
                self._cont.removePrimaryAuthor(self._cont.getPrimaryAuthorList()[0])
            for a in recoveredC.getPrimaryAuthorList():
                log("%sSetting values for primary author \"%s\"..."%(incPrintPrefix(pp),\
                a.getEmail()))
                pa = TrashCanManager().getById(a._p_oid)
                self._cont.recoverPrimaryAuthor(pa, a.isPendingSubmitter())
                pa.setDataFromOtherCP(a)
                log("%sPrimary author values successfully set."%incPrintPrefix(pp))
            # Co-author(s) recovery:
            while len(self._cont.getCoAuthorList()) > 0:
                self._cont.removeCoAuthor(self._cont.getCoAuthorList()[0])
            for a in recoveredC.getCoAuthorList():
                log("%sSetting values for co-author \"%s\"..."%(incPrintPrefix(pp),\
                a.getEmail()))
                ca = TrashCanManager().getById(a._p_oid)
                self._cont.recoverCoAuthor(ca, a.isPendingSubmitter())
                ca.setDataFromOtherCP(a)
                log("%sCo-author values successfully set."%incPrintPrefix(pp))
            # Speaker(s) recovery:
            while len(self._cont.getSpeakerList()) > 0:
                self._cont.removeSpeaker(self._cont.getSpeakerList()[0])
            for s in recoveredC.getSpeakerList():
                log("%sSetting values for speaker \"%s\"..."%(incPrintPrefix(pp),\
                s.getEmail()))
                spk = None
                try:
                # Try to get the speaker from the trash can:
                    spk = TrashCanManager().getById(s._p_oid)
                    self._cont.recoverSpeaker(spk, s.isPendingSubmitter())
                    spk.setDataFromOtherCP(s)
                except Exception:
                # Executed if the speaker was added from an author:
                    spk = self._cont.getAuthorById(s.getId())
                    self._cont.addSpeaker(spk)
                log("%sSpeaker values successfully set."%incPrintPrefix(pp))
            self._cont.setSpeakerText(recoveredC.getSpeakerText())
            # Material(s) recovery:
            while len(self._cont.getMaterialList()) > 0:
                self._cont.removeMaterial(self._cont.getMaterialList()[0])
            for m in recoveredC.getMaterialList():
                mat = TrashCanManager().getById(m._p_oid)
                self._cont.recoverMaterial(mat)
                mr = MaterialRecovery(mat)
                mr.setValues(m, pp=incPrintPrefix(pp))
            # Paper recovery:
            self._cont.removePaper()
            if recoveredC.getPaper():
                p = TrashCanManager().getById(recoveredC.getPaper()._p_oid)
                self._cont.recoverPaper(p)
                mr = MaterialRecovery(p)
                mr.setValues(recoveredC.getPaper(), pp=incPrintPrefix(pp))
            # Slides recovery:
            self._cont.removeSlides()
            if recoveredC.getSlides():
                s = TrashCanManager().getById(recoveredC.getSlides()._p_oid)
                self._cont.recoverSlides(s)
                mr = MaterialRecovery(s)
                mr.setValues(recoveredC.getSlides(), pp=incPrintPrefix(pp))
            # Video recovery:
            self._cont.removeVideo()
            if recoveredC.getVideo():
                v = TrashCanManager().getById(recoveredC.getVideo()._p_oid)
                self._cont.recoverVideo(v)
                mr = MaterialRecovery(v)
                mr.setValues(recoveredC.getVideo(), pp=incPrintPrefix(pp))
            # Poster recovery:
            self._cont.removePoster()
            if recoveredC.getPoster():
                p = TrashCanManager().getById(recoveredC.getPoster()._p_oid)
                self._cont.recoverPoster(p)
                mr = MaterialRecovery(p)
                mr.setValues(recoveredC.getPoster(), pp=incPrintPrefix(pp))
            # Minutes recovery:
            self._cont.removeMinutes()
            if recoveredC.getMinutes():
                m = TrashCanManager().getById(recoveredC.getMinutes()._p_oid)
                self._cont.recoverMinutes(m)
                mr = MaterialRecovery(m)
                mr.setValues(recoveredC.getMinutes(), pp=incPrintPrefix(pp))
            # Subcontribution(s) recovery:
            while len(self._cont.getSubContributionList()) > 0:
                self._cont.removeSubContribution(self._cont.getSubContributionList()[0])
            for s in recoveredC.getSubContributionList():
                sc = TrashCanManager().getById(s._p_oid)
                self._cont.recoverSubContribution(sc)
                scr = SubContributionRecovery(sc)
                scr.setValues(s, incPrintPrefix(pp))
            # Submitter(s) recovery:
            for s in self._cont.getSubmitterList()[:]:
                self._cont.revokeSubmission(s)
            ah = AvatarHolder()
            for s in recoveredC.getSubmitterList():
                log("%sGranting submission privilege for user \"%s\"..."%(incPrintPrefix(pp),\
                s.getEmail()))
                user = None
                try:
                    user = ah.getById(s.getId())
                except KeyError:
                    if ah.match({"email": s.getEmail()}):
                        user = ah.match({"email": s.getEmail()})[0]
                    else:
                        log("%sSubmission privilege cannot be granted because the user has been deleted."%incPrintPrefix(pp))
                if user:
                    self._cont.grantSubmission(user)
                    log("%sSubmission privilege successfully granted."%incPrintPrefix(pp))
            # Other values' recovery:
            type = None
            if recoveredC.getType():
                recType = recoveredC.getType()
                type = self._cont.getConference().getContribTypeById(recType.getId())
            self._cont.setType(type)
            if isinstance(self._cont, AcceptedContribution):
                self._cont.setAbstract(self._cont.getConference().getAbstractMgr().getAbstractById(recoveredC.getAbstract().getId()))
                self._cont.getAbstract()._setContribution(self._cont)
            # Access control recovery:
            acr = AccessControllerRecovery(self._cont.getAccessController())
            acr.setValues(recoveredC.getAccessController(), incPrintPrefix(pp))
            self._cont.notifyModification(recoveredC.getModificationDate())
            self._dbm.commit(True)
            log("%sContribution values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the contribution values: %s"%(pp, msg))
            return

class SessionRecovery:
# Recovery for a session.

    def __init__(self, sess):
    # sess is the session that we want to recover.
        self._sess = sess
        self._dbm = DBMgr.getInstance()
        self._or = ObjectRecovery(self._sess._p_oid)
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, full=False, pp=""):
    # Recovers the session as it was at the given dt. If "full" is true, the
    # contributions that were in recoveredS and that have been deleted from the
    # conference are put back into it and all the contributions' content is
    # recovered. pp is a print prefix that is used to display the output
    # messages in a "level way".
        try:
            if not isinstance(self._sess, Session):
                raise Exception("The given object is not an instance of Session.")
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering session..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            recsess = self._or.proceed(dt, incPrintPrefix(pp))
            if recsess == None:
                raise Exception("Problem with the object.")
            if self.setValues(recsess, full, incPrintPrefix(pp)):
                self._dbm.commit()
                log("%sSession successfully recovered in %s."%(pp, datetime.now()-now))
            else:
                raise Exception("Session values couldn't be set.")
        except Exception, msg:
            log("%s*ERROR* while recovering the session: %s"%(pp, msg))

    def setValues(self, recoveredS, full=False, pp=""):
    # Sets the values of recoveredS to self._sess (the current session). If
    # "full" is true, the contributions that were in recoveredS and that have
    # been deleted from the conference are put back into it and all the
    # contributions' content is recovered. pp is a print prefix that is used
    # to display the output messages in a "level way".
        try:
            log("%sSetting values for session \"%s\"..."%(pp, self._sess.getTitle()))
            # Set recovered values:
            locationName = ""
            locationAddress = ""
            if recoveredS.getOwnLocation():
                locationName = recoveredS.getOwnLocation().getName()
                locationAddress = recoveredS.getOwnLocation().getAddress()
            roomName = ""
            if recoveredS.getOwnRoom():
                roomName = recoveredS.getOwnRoom().getName()
            self._sess.setValues({"title": recoveredS.getTitle(), "description":\
            recoveredS.getDescription(), "code": recoveredS.getCode(), "backgroundColor":\
            recoveredS.getBgColor(), "textColor": recoveredS.getTextColor(), "locationName":\
            locationName, "locationAddress": locationAddress, "roomName": roomName,\
            "contribDuration": recoveredS.getContribDuration()})
            self._sess.setClosed(recoveredS.isClosed())
            self._sess.setComments(recoveredS.getComments())
            # Convener(s) recovery:
            while len(self._sess.getConvenerList()) > 0:
                self._sess.removeConvener(self._sess.getConvenerList()[0])
            for c in recoveredS.getConvenerList():
                log("%sSetting values for convener \"%s\"..."%(incPrintPrefix(pp),\
                c.getEmail()))
                con = TrashCanManager().getById(c._p_oid)
                self._sess.recoverConvener(con)
                con.setDataFromOtherCP(c)
                log("%sConvener values successfully set."%incPrintPrefix(pp))
            self._sess.setConvenerText(recoveredS.getConvenerText())
            # Material(s) recovery:
            while len(self._sess.getMaterialList()) > 0:
                self._sess.removeMaterial(self._sess.getMaterialList()[0])
            for m in recoveredS.getMaterialList():
                mat = TrashCanManager().getById(m._p_oid)
                self._sess.recoverMaterial(mat)
                mr = MaterialRecovery(mat)
                mr.setValues(m, pp=incPrintPrefix(pp))
            # Minutes recovery:
            self._sess.removeMinutes()
            if recoveredS.getMinutes():
                m = TrashCanManager().getById(recoveredS.getMinutes()._p_oid)
                self._sess.recoverMinutes(m)
                mr = MaterialRecovery(m)
                mr.setValues(recoveredS.getMinutes(), pp=incPrintPrefix(pp))
            # Coordinator(s) recovery:
            for c in self._sess.getCoordinatorList()[:]:
                self._sess.removeCoordinator(c)
            ah = AvatarHolder()
            for c in recoveredS.getCoordinatorList():
                log("%sGranting coordination privilege for user \"%s\"..."%(incPrintPrefix(pp),\
                c.getEmail()))
                user = None
                try:
                    user = ah.getById(c.getId())
                except KeyError:
                    if ah.match({"email": c.getEmail()}):
                        user = ah.match({"email": c.getEmail()})[0]
                    else:
                        log("%sCoordination privilege cannot be granted because the user has been deleted."%incPrintPrefix(pp))
                if user:
                    self._sess.addCoordinator(user)
                    log("%sCoordination privilege successfully granted."%incPrintPrefix(pp))
            # Contribution(s) recovery:
            while len(self._sess.getContributionList()) > 0:
                self._sess.removeContribution(self._sess.getContributionList()[0])
            for c in recoveredS.getContributionList():
                con = self._sess.getConference().getContributionById(c.getId())
                if full:
                    if not con:
                        con = TrashCanManager().getById(c._p_oid)
                        con.recover()
                    session = con.getSession()
                    if not session:
                        session = self._sess
                    if session.getId() == recoveredS.getId():
                        track = c.getTrack()
                        if track:
                            con.setTrack(self._sess.getConference().getTrackById(track.getId()))
                        else:
                            con.setTrack(None)
                        self._sess.addContribution(con, con.getId())
                        cr = ContributionRecovery(con)
                        cr.setValues(c, incPrintPrefix(pp))
                        if c.isWithdrawn():
                            ah = AvatarHolder()
                            resp = None
                            try:
                                resp = ah.getById(c.getCurrentStatus().getResponsible().getId())
                            except Exception:
                                resp = TrashCanManager().getById(c.getCurrentStatus().getResponsible()._p_oid)
                            status = ContribStatusWithdrawn(con,resp,c.getCurrentStatus().getComment())
                        else:
                            status = ContribStatusNotSch(con)
                        status.setDate(c.getCurrentStatus().getDate())
                        con.setStatus(status)
                    else:
                        log("%sContribution \"%s\" is already in another session."%(incPrintPrefix(pp),\
                        con.getTitle()))
                else:
                    if not con:
                        log("%sContribution \"%s\" has been deleted from the conference."%(incPrintPrefix(pp),\
                        c.getTitle()))
                    else:
                        session = con.getSession()
                        if not session:
                            session = self._sess
                        if session.getId() == recoveredS.getId():
                            log("%sAdding contribution \"%s\"..."%(incPrintPrefix(pp),\
                            con.getTitle()))
                            self._sess.addContribution(con, con.getId())
                            log("%sContribution successfully added."%incPrintPrefix(pp))
                            if c.isWithdrawn():
                                ah = AvatarHolder()
                                resp = None
                                try:
                                    resp = ah.getById(c.getCurrentStatus().getResponsible().getId())
                                except Exception:
                                    resp = TrashCanManager().getById(c.getCurrentStatus().getResponsible()._p_oid)
                                status = ContribStatusWithdrawn(con,resp,c.getCurrentStatus().getComment())
                            else:
                                status = ContribStatusNotSch(con)
                            status.setDate(c.getCurrentStatus().getDate())
                            con.setStatus(status)
                        else:
                            log("%sContribution \"%s\" is already in another session."%(incPrintPrefix(pp),\
                            con.getTitle()))
            # Schedule recovery:
            while len(self._sess.getSlotList()) > 0:
                self._sess.removeSlot(self._sess.getSlotList()[0], True)
            self._sess.setScheduleType(recoveredS.getScheduleType())
            self._sess.setDates(recoveredS.getStartDate(), recoveredS.getEndDate(), 2)
            for e in recoveredS.getSchedule().getEntries():
                ss = e.getOwner()
                sslot = TrashCanManager().getById(ss._p_oid)
                self.setSessionSlotValues(sslot, ss, incPrintPrefix(pp))
                self._sess.recoverSlot(sslot)
            # Access control recovery:
            acr = AccessControllerRecovery(self._sess.getAccessController())
            acr.setValues(recoveredS.getAccessController(), incPrintPrefix(pp))
            self._sess.notifyModification()
            self._dbm.commit(True)
            log("%sSession values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the session values: %s"%(pp, msg))
            return

    def setSessionSlotValues(self, currentSS, recoveredSS, pp=""):
    # Sets the values of recoveredSS to currentSS (the current session slot).
    # pp is a print prefix that is used to display the output messages in a
    # "level way".
        try:
            log("%sSetting values for session slot \"%s\"..."%(pp, currentSS.getTitle()))
            # Set recovered values:
            currentSS.session = self._sess
            currentSS.setDates(recoveredSS.getStartDate(), recoveredSS.getEndDate(), 0)
            locationName = ""
            locationAddress = ""
            if recoveredSS.getOwnLocation():
                locationName = recoveredSS.getOwnLocation().getName()
                locationAddress = recoveredSS.getOwnLocation().getAddress()
            roomName = ""
            if recoveredSS.getOwnRoom():
                roomName = recoveredSS.getOwnRoom().getName()
            currentSS.setValues({"title": recoveredSS.getTitle(), "locationName":\
            locationName, "locationAddress": locationAddress, "roomAction": "define",\
            "roomName": roomName, "contribDuration": recoveredSS.getContribDuration()},\
            0, 0)
            # Schedule recovery:
            currentSS.setScheduleType(recoveredSS.getSession().getScheduleType())
            for e in recoveredSS.getSchedule().getEntries():
                if isinstance(e, ContribSchEntry):
                    con = currentSS.getSession().getContributionById(e.getOwner().getId())
                    if con:
                        currentSS.getSchedule().addEntry(con.getSchEntry(), 0)
                        con.setStartDate(e.getOwner().getStartDate(), 0, 0)
                        con.setDuration(check=0, dur=e.getOwner().getDuration())
                        con.getCurrentStatus().setDate(e.getOwner().getCurrentStatus().getDate())
                elif isinstance(e, BreakTimeSchEntry):
                    b = TrashCanManager().getById(e._p_oid)
                    locationName = ""
                    locationAddress = ""
                    if e.getOwnLocation():
                        locationName = e.getOwnLocation().getName()
                        locationAddress = e.getOwnLocation().getAddress()
                    roomName = ""
                    if e.getOwnRoom():
                        roomName = e.getOwnRoom().getName()
                    b.setValues({"startDate": e.getStartDate(), "durTimedelta": e.getDuration(),\
                    "locationName": locationName, "locationAddress": locationAddress,\
                    "roomName": roomName, "backgroundColor": e.getColor(),\
                    "textColor": e.getTextColor(), "title": e.getTitle(),
                    "description": e.getDescription()}, 0, 0)
                    currentSS.getSchedule().addEntry(b, 0)
                    b.recover()
            # Convener(s) recovery:
            while len(currentSS.getOwnConvenerList()) > 0:
                currentSS.removeConvener(currentSS.getOwnConvenerList()[0])
            for c in recoveredSS.getOwnConvenerList():
                log("%sSetting values for convener \"%s\"..."%(incPrintPrefix(pp),\
                c.getEmail()))
                con = TrashCanManager().getById(c._p_oid)
                currentSS.recoverConvener(con)
                con.setDataFromOtherCP(c)
                log("%sConvener values successfully set."%incPrintPrefix(pp))
            currentSS.notifyModification()
            self._dbm.commit(True)
            log("%sSession slot values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the session slot values: %s"%(pp, msg))
            return

class ConferenceRecovery:
# Recovery for a conference.

    def __init__(self, conf):
    # conf is the conference that we want to recover.
        self._conf = conf
        self._dbm = DBMgr.getInstance()
        self._or = ObjectRecovery(self._conf._p_oid)
        self._tmpdbm = TmpDBMgr.getInstance()

    def proceed(self, dt, pp=""):
    # Recovers the conference as it was at the given dt. pp is a print prefix
    # that is used to display the output messages in a "level way".
        try:
            if not isinstance(self._conf, Conference):
                raise Exception("The given object is not an instance of Conference.")
            now = datetime.now()
            if dt > now:
                raise Exception("Recovery from future is not possible.")
            log("%sRecovering conference..."%pp)
            if (dt != self._tmpdbm.getDBDatetime()) or (self._tmpdbm.getDBDatetime() == None):
                self._dbm.endRequest()
                self._tmpdbm.setDB(dt, incPrintPrefix(pp))
                self._dbm.startRequest()
            if self._tmpdbm.getDBDatetime() != dt:
                raise Exception("Problem with the temporary database.")
            recconf = self._or.proceed(dt, incPrintPrefix(pp))
            if recconf == None:
                raise Exception("Problem with the object.")
            if self.setValues(recconf, incPrintPrefix(pp)):
                self._dbm.commit()
                log("%sConference successfully recovered in %s."%(pp, datetime.now()-now))
            else:
                raise Exception("Conference values couldn't be set.")
        except Exception, msg:
            log("%s*ERROR* while recovering the conference: %s"%(pp, msg))

    def setValues(self, recoveredC, pp=""):
    # Sets the values of recoveredC to self._conf (the current conference). pp
    # is a print prefix that is used to display the output messages in a "level
    # way".
        try:
            log("%sSetting values for conference \"%s\"..."%(pp, self._conf.getTitle()))
            # Set recovered values:
            locationName = ""
            locationAddress = ""
            if recoveredC.getLocation():
                locationName = recoveredC.getLocation().getName()
                locationAddress = recoveredC.getLocation().getAddress()
            roomName = ""
            if recoveredC.getRoom():
                roomName = recoveredC.getRoom().getName()
            self._conf.setValues({"visibility": recoveredC.getVisibility(),\
            "title": recoveredC.getTitle(), "description": recoveredC.getDescription(),\
            "supportEmail": recoveredC.getSupportInfo().getEmail(), "contactInfo": recoveredC.getContactInfo(),\
            "locationName": locationName, "locationAddress": locationAddress,\
            "roomName": roomName})
            self._conf.setClosed(recoveredC.isClosed())
            # Chair(s) recovery:
            while len(self._conf.getChairList()) > 0:
                self._conf.removeChair(self._conf.getChairList()[0])
            for c in recoveredC.getChairList():
                log("%sSetting values for chair \"%s\"..."%(incPrintPrefix(pp),\
                c.getEmail()))
                ch = TrashCanManager().getById(c._p_oid)
                self._conf.recoverChair(ch)
                ch.setDataFromOtherCP(c)
                log("%sChair values successfully set."%incPrintPrefix(pp))
            self._conf.setChairmanText(recoveredC.getChairmanText())
            # Material(s) recovery:
            while len(self._conf.getMaterialList()) > 0:
                self._conf.removeMaterial(self._conf.getMaterialList()[0])
            for m in recoveredC.getMaterialList():
                mat = TrashCanManager().getById(m._p_oid)
                self._conf.recoverMaterial(mat)
                mr = MaterialRecovery(mat)
                mr.setValues(m, pp=incPrintPrefix(pp))
            # Paper recovery:
            self._conf.removePaper()
            if recoveredC.getPaper():
                p = TrashCanManager().getById(recoveredC.getPaper()._p_oid)
                self._conf.recoverPaper(p)
                mr = MaterialRecovery(p)
                mr.setValues(recoveredC.getPaper(), pp=incPrintPrefix(pp))
            # Slides recovery:
            self._conf.removeSlides()
            if recoveredC.getSlides():
                s = TrashCanManager().getById(recoveredC.getSlides()._p_oid)
                self._conf.recoverSlides(s)
                mr = MaterialRecovery(s)
                mr.setValues(recoveredC.getSlides(), pp=incPrintPrefix(pp))
            # Video recovery:
            self._conf.removeVideo()
            if recoveredC.getVideo():
                v = TrashCanManager().getById(recoveredC.getVideo()._p_oid)
                self._conf.recoverVideo(v)
                mr = MaterialRecovery(v)
                mr.setValues(recoveredC.getVideo(), pp=incPrintPrefix(pp))
            # Poster recovery:
            self._conf.removePoster()
            if recoveredC.getPoster():
                p = TrashCanManager().getById(recoveredC.getPoster()._p_oid)
                self._conf.recoverPoster(p)
                mr = MaterialRecovery(p)
                mr.setValues(recoveredC.getPoster(), pp=incPrintPrefix(pp))
            # Minutes recovery:
            self._conf.removeMinutes()
            if recoveredC.getMinutes():
                m = TrashCanManager().getById(recoveredC.getMinutes()._p_oid)
                self._conf.recoverMinutes(m)
                mr = MaterialRecovery(m)
                mr.setValues(recoveredC.getMinutes(), pp=incPrintPrefix(pp))
            # Contribution type(s) recovery:
            while len(self._conf.getContribTypeList()) > 0:
                    self._conf.removeContribType(self._conf.getContribTypeList()[0])
            for t in recoveredC.getContribTypeList():
                type = TrashCanManager().getById(t._p_oid)
                type.setName(t.getName())
                type.setDescription(t.getDescription())
                type.setConference(self._conf)
                self._conf.recoverContribType(type)
            # Track(s) recovery:
            while len(self._conf.getTrackList()) > 0:
                    self._conf.removeTrack(self._conf.getTrackList()[0])
            for t in recoveredC.getTrackList():
                track = TrashCanManager().getById(t._p_oid)
                self.setTrackValues(track, t, incPrintPrefix(pp))
                self._conf.recoverTrack(track)
            # Abstract manager recovery:
            log("%sSetting values for abstract manager..."%incPrintPrefix(pp))
            curAM = self._conf.getAbstractMgr()
            recAM = recoveredC.getAbstractMgr()
            curAM.setActive(recAM.isActive())
            curAM.setStartSubmissionDate(recAM.getStartSubmissionDate())
            curAM.setEndSubmissionDate(recAM.getEndSubmissionDate())
            curAM.setModificationDeadline(recAM.getModificationDeadline())
            curAM.setAnnouncement(recAM.getAnnouncement())
            #   Authorised submitter(s) recovery:
            for s in curAM.getAuthorizedSubmitterList()[:]:
                curAM.removeAuthorizedSubmitter(s)
            ah = AvatarHolder()
            for s in recAM.getAuthorizedSubmitterList():
                log("%sGranting late submission privilege for user \"%s\"..."%(incPrintPrefix(incPrintPrefix(pp)),\
                s.getEmail()))
                user = None
                try:
                    user = ah.getById(s.getId())
                except KeyError:
                    if ah.match({"email": s.getEmail()}):
                        user = ah.match({"email": s.getEmail()})[0]
                    else:
                        log("%sLate submission privilege cannot be granted because the user has been deleted."%incPrintPrefix(pp))
                if user:
                    curAM.addAuthorizedSubmitter(user)
                    log("%sLate submission privilege successfully granted."%incPrintPrefix(incPrintPrefix(pp)))
            log("%sAbstract manager values successfully set."%incPrintPrefix(pp))
            #   Notification template(s) recovery:
            for nt in curAM.getNotificationTplList()[:]:
                curAM.removeNotificationTpl(nt)
            for nt in recAM.getNotificationTplList():
                ntpl = TrashCanManager().getById(nt._p_oid)
                ntpl.setName(nt.getName())
                ntpl.setDescription(nt.getDescription())
                ntpl.setTplSubject(nt.getTplSubject())
                ntpl.setTplBody(nt.getTplBody())
                ntpl.setFromAddr(nt.getFromAddr())
                ntpl.setCCAddrList(nt.getCCAddrList())
                ntpl.setCAasCCAddr(nt.getCAasCCAddr())
                for a in nt.getToAddrList():
                    add = TrashCanManager().getById(a._p_oid)
                    ntpl.recoverToAddr(add)
                for c in nt.getConditionList():
                    con = TrashCanManager().getById(c._p_oid)
                    if isinstance(con, NotifTplCondAccepted):
                        con.setContribType()
                        if c.getContribType() != "--any--":
                            con.setContribType(self._conf.getContribTypeById(c.getContribType().getId()))
                        con.setTrack()
                        if c.getTrack() != "--any--":
                            con.setTrack(self._conf.getTrackById(c.getTrack().getId()))
                    ntpl.recoverCondition(con)
                curAM.recoverNotificationTpl(ntpl)
            # Abstract(s) and contribution(s) recovery:
            while len(self._conf.getContributionList()) > 0:
                self._conf.removeContribution(self._conf.getContributionList()[0])
            while len(curAM.getAbstractList()) > 0:
                curAM.removeAbstract(curAM.getAbstractList()[0])
            for c in recoveredC.getContributionList():
                con = TrashCanManager().getById(c._p_oid)
                self._conf.recoverContribution(con)
            for a in recAM.getAbstractList():
                abs = TrashCanManager().getById(a._p_oid)
                curAM.recoverAbstract(abs)
            for a in recAM.getAbstractList():
                abs = curAM.getAbstractById(a.getId())
                ar = AbstractRecovery(abs)
                ar.setValues(a, incPrintPrefix(pp))
            for c in recoveredC.getContributionList():
                con = self._conf.getContributionById(c.getId())
                track = c.getTrack()
                if track:
                    con.setTrack(self._conf.getConference().getTrackById(track.getId()))
                else:
                    con.setTrack(None)
                cr = ContributionRecovery(con)
                cr.setValues(c, incPrintPrefix(pp))
                status = None
                if c.isWithdrawn():
                    ah = AvatarHolder()
                    resp = None
                    try:
                        resp = ah.getById(c.getCurrentStatus().getResponsible().getId())
                    except Exception:
                        resp = TrashCanManager().getById(c.getCurrentStatus().getResponsible()._p_oid)
                    status = ContribStatusWithdrawn(con,resp,c.getCurrentStatus().getComment())
                else:
                    status = ContribStatusNotSch(con)
                status.setDate(c.getCurrentStatus().getDate())
                con.setStatus(status)
            # Registration form recovery:
            log("%sSetting values for registration form..."%incPrintPrefix(pp))
            self._conf.removeRegistrationForm()
            curRF = TrashCanManager().getById(recoveredC.getRegistrationForm()._p_oid)
            self._conf.recoverRegistrationForm(curRF)
            recRF = recoveredC.getRegistrationForm()
            curRF.setActivated(recRF.isActivated())
            curRF.setMandatoryAccount(recRF.isMandatoryAccount())
            curRF.setTitle(recRF.getTitle())
            curRF.setAnnouncement(recRF.getAnnouncement())
            curRF.setUsersLimit(recRF.getUsersLimit())
            curRF.setContactInfo(recRF.getContactInfo())
            curRF.setStartRegistrationDate(recRF.getStartRegistrationDate())
            curRF.setEndRegistrationDate(recRF.getEndRegistrationDate())
            #   Notification recovery:
            curN = curRF.getNotification()
            recN = recRF.getNotification()
            curN.clearToList()
            curN.clearCCList()
            for to in recN.getToList():
                curN.addToList(to)
            for cc in recN.getCCList():
                curN.addCCList(cc)
            #   Sessions form recovery:
            curSF = curRF.getSessionsForm()
            recSF = recRF.getSessionsForm()
            curSF.setEnabled(recSF.isEnabled())
            curSF.setValues({"title": recSF.getTitle(), "description": recSF.getDescription()})
            curSF.setType(recSF.getType())
            #   Accommodation form recovery:
            curAF = curRF.getAccommodationForm()
            recAF = recRF.getAccommodationForm()
            curAF.setEnabled(recAF.isEnabled())
            curAF.setValues({"title": recAF.getTitle(), "description": recAF.getDescription(), "currency": recAF.getCurrency()})
            curAF.clearAccommodationTypesList()
            for at in recAF.getAccommodationTypesList():
                acty = TrashCanManager().getById(at._p_oid)
                acty.setRegistrationForm(curRF)
                acty.setValues({"caption": at.getCaption(), "cancelled": at.isCancelled(),\
                "placesLimit": at.getPlacesLimit()})
                curAF.recoverAccommodationType(acty)
            #   Reason participation form recovery:
            curRPF = curRF.getReasonParticipationForm()
            recRPF = recRF.getReasonParticipationForm()
            curRPF.setEnabled(recRPF.isEnabled())
            curRPF.setValues({"title": recRPF.getTitle(), "description": recRPF.getDescription()})
            #   Further information form recovery:
            curFIF = curRF.getFurtherInformationForm()
            recFIF = recRF.getFurtherInformationForm()
            curFIF.setEnabled(recFIF.isEnabled())
            curFIF.setValues({"title": recFIF.getTitle(), "content": recFIF.getContent()})
            #   Social event form recovery:
            curSEF = curRF.getSocialEventForm()
            recSEF = recRF.getSocialEventForm()
            curSEF.setEnabled(recSEF.isEnabled())
            curSEF.setValues({"title": recSEF.getTitle(), "description": recSEF.getDescription()})
            curSEF.clearSocialEventList()
            for se in recSEF.getSocialEventList():
                soev = TrashCanManager().getById(se._p_oid)
                soev.setRegistrationForm(curRF)
                soev.setValues({"caption": se.getCaption(), "cancelled": se.isCancelled(),\
                "reason": se.getCancelledReason()})
                curSEF.recoverSocialEvent(soev)
            log("%sRegistration form values successfully set."%incPrintPrefix(pp))
            # Schedule recovery:
            while len(self._conf.getSchedule().getEntries()) > 0:
                self._conf.getSchedule().removeEntry(self._conf.getSchedule().getEntries()[0])
            self._conf.setDates(recoveredC.getStartDate(), recoveredC.getEndDate())
            self._conf.setStartTime(recoveredC.getStartDate().hour, recoveredC.getStartDate().minute)
            self._conf.setEndTime(recoveredC.getEndDate().hour, recoveredC.getEndDate().minute)
            for e in recoveredC.getSchedule().getEntries():
                if isinstance(e, ContribSchEntry):
                    con = self._conf.getContributionById(e.getOwner().getId())
                    self._conf.getSchedule().addEntry(con.getSchEntry(), 0)
                    con.setStartDate(e.getOwner().getStartDate(), 0, 0)
                    con.setDuration(check=0, dur=e.getOwner().getDuration())
                    con.getCurrentStatus().setDate(e.getOwner().getCurrentStatus().getDate())
                elif isinstance(e, BreakTimeSchEntry):
                    b = TrashCanManager().getById(e._p_oid)
                    locationName = ""
                    locationAddress = ""
                    if e.getOwnLocation():
                        locationName = e.getOwnLocation().getName()
                        locationAddress = e.getOwnLocation().getAddress()
                    roomName = ""
                    if e.getOwnRoom():
                        roomName = e.getOwnRoom().getName()
                    b.setValues({"startDate": e.getStartDate(), "durTimedelta": e.getDuration(),\
                    "locationName": locationName, "locationAddress": locationAddress,\
                    "roomName": roomName, "backgroundColor": e.getColor(),\
                    "textColor": e.getTextColor(), "title": e.getTitle(),
                    "description": e.getDescription()}, 0, 0)
                    self._conf.getSchedule().addEntry(b, 0)
                    b.recover()
            # Session(s) recovery:
            for s in self._conf.getSessionList():
                self._conf.removeSession(s)
            for s in recoveredC.getSessionList():
                sess = TrashCanManager().getById(s._p_oid)
                isCancelled = False
                rs = s.getRegistrationSession()
                if rs:
                    isCancelled = rs.isCancelled()
                self._conf.recoverSession(sess, 0, isCancelled)
                sr = SessionRecovery(sess)
                sr.setValues(s, incPrintPrefix(pp))
            # Display recovery:
            log("%sSetting values for conference display..."%incPrintPrefix(pp))
            recDBRoot = self._tmpdbm.getDBConnection().root()
            if recDBRoot.has_key("displayRegistery"):
                if recDBRoot["displayRegistery"].has_key(recoveredC.getId()):
                    dM = recDBRoot["displayRegistery"][recoveredC.getId()]
                    recF = dM.getFormat()
                    curF = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getFormat()
                    curF.setColorCode("titleBgColor", recF.getFormatOption("titleBgColor")['code'])
                    curF.setColorCode("titleTextColor", recF.getFormatOption("titleTextColor")['code'])
                    recM = dM.getMenu()
                    curM = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
                    for l in curM.getLinkList()[:]:
                        curM.removeLink(l)
                    for l in recM.getLinkList():
                        link = TrashCanManager().getById(l._p_oid)
                        self.setLinkValuesAndRecover(link, l, curM)
                else:
                    log("%sConference display values couldn't be set: No display manager found."%incPrintPrefix(pp))
            else:
                log("%sConference display values couldn't be set: No display registry found."%incPrintPrefix(pp))
            self._conf.removeLogo()
            if recoveredC.getLogo():
                l = recoveredC.getLogo()
                logo = TrashCanManager().getById(l._p_oid)
                self._conf.recoverLogo(logo)
            log("%sConfrence display values successfully set."%incPrintPrefix(pp))
            # Alarm(s) recovery:
            log("%sSetting values for conference alarm(s)..."%incPrintPrefix(pp))
            for a in self._conf.getAlarmList():
                self._conf.removeAlarm(a)
            for a in recoveredC.getAlarmList():
                al = TrashCanManager().getById(a._p_oid)
                sm = TrashCanManager().getById(a.mail._p_oid)
                al.mail = sm
                al.addObj(al.mail)
                sm.recover()
                if a.getTimeBefore():
                    al.setTimeBefore(a.getTimeBefore())
                else:
                    al.setStartDate(a.getStartDate())
                al.setEndDate(a.getEndDate())
                al.setInterval(a.getInterval())
                al.setLastDate(a.getLastDate())
                al.setSubject(a.getSubject())
                al.setFromAddr(a.getFromAddr())
                al.initialiseToAddr()
                for ad in a.getToAddrList():
                    al.addToAddr(ad)
                for u in al.getToUserList()[:]:
                    al.removeToUser(u)
                ah = AvatarHolder()
                for u in a.getToUserList():
                    user = None
                    try:
                        user = ah.getById(u.getId())
                    except KeyError:
                        if ah.match({"email": u.getEmail()}):
                            user = ah.match({"email": u.getEmail()})[0]
                        else:
                            log("%sUser \"%s\" cannot be added to the mailing list for alarm \"%s\" because it has been deleted."%(incPrintPrefix(pp),\
                            u.getEmail(), al.getSubject()))
                    if user:
                        al.addToUser(u)
                al.setText(a.getText())
                al.setNote(a.getNote())
                al.setConfSumary(a.getConfSumary())
                self._conf.recoverAlarm(al)
            log("%sConference alarm(s) values successfully set."%incPrintPrefix(pp))
            # Other values' recovery:
            self._conf._submissionDate = recoveredC.getSubmittedDate()
            self._conf._archivingRequestDate = recoveredC.getRequestedToArchiveDate()
            self._conf.getBOAConfig().setText(recoveredC.getBOAConfig().getText())
            for r in self._conf.getSessionCoordinatorRights()[:]:
                self._conf.removeSessionCoordinatorRight(r)
            for r in recoveredC.getSessionCoordinatorRights():
                self._conf.addSessionCoordinatorRight(r)
            # Access control recovery:
            self._conf.setAccessKey(recoveredC.getAccessKey())
            self._conf.setModifKey(recoveredC.getModifKey())
            acr = AccessControllerRecovery(self._conf.getAccessController())
            acr.setValues(recoveredC.getAccessController(), incPrintPrefix(pp))
            self._conf.notifyModification(recoveredC.getModificationDate())
            self._dbm.commit(True)
            log("%sConference values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the conference values: %s"%(pp, msg))
            return

    def setTrackValues(self, currentT, recoveredT, pp=""):
    # Sets the values of recoveredT to currentT (the current track). pp is a
    # print prefix that is used to display the output messages in a "level way".
        try:
            log("%sSetting values for track \"%s\"..."%(pp, currentT.getTitle()))
            # Set recovered values:
            currentT.conference = self._conf
            currentT.setTitle(recoveredT.getTitle())
            currentT.setDescription(recoveredT.getDescription())
            currentT.setCode(recoveredT.getCode())
            # Subtrack(s) recovery:
            for st in currentT.getSubTrackList():
                currentT.removeSubTrack(st)
            for st in recoveredT.getSubTrackList():
                subtrack = TrashCanManager().getById(st._p_oid)
                subtrack.setTitle(st.getTitle())
                subtrack.setDescription(st.getDescription())
                currentT.recoverSubTrack(subtrack)
            # Coordinator(s) recovery:
            for c in currentT.getCoordinatorList()[:]:
                currentT.removeCoordinator(c)
            ah = AvatarHolder()
            for c in recoveredT.getCoordinatorList():
                log("%sGranting coordination privilege for user \"%s\"..."%(incPrintPrefix(pp),\
                c.getEmail()))
                user = None
                try:
                    user = ah.getById(c.getId())
                except KeyError:
                    if ah.match({"email": c.getEmail()}):
                        user = ah.match({"email": c.getEmail()})[0]
                    else:
                        log("%sCoordination privilege cannot be granted because the user has been deleted."%incPrintPrefix(pp))
                if user:
                    currentT.addCoordinator(user)
                    log("%sCoordination privilege successfully granted."%incPrintPrefix(pp))
            currentT.notifyModification()
            self._dbm.commit(True)
            log("%sTrack values successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the track values: %s"%(pp, msg))
            return

    def setLinkValuesAndRecover(self, currentL, recoveredL, parent):
    # Done here as a method because it can be called recursively.
        parent.addLink(currentL)
        currentL.recover()
        currentL.setName(recoveredL.getName())
        currentL.setEnabled(recoveredL.isEnabled())
        if currentL.getType() == "spacer":
            return
        # The link is not a spacer, so it is a system link or an external link:
        if currentL.getType() == "extern":
            currentL.setURL(recoveredL.getURL())
        currentL.setDisplayTarget(recoveredL.getDisplayTarget())
        currentL._caption = recoveredL._caption
        for l in recoveredL.getLinkList():
            link = TrashCanManager().getById(l._p_oid)
            self.setLinkValuesAndRecover(link, l, currentL)


class ParticipantRecovery(ConferenceRecovery):
# Recovery of a participant list for a conference.

    def setValues(self, recoveredC, pp=""):
    # Sets the values of recoveredC to self._conf (the current conference). pp
    # is a print prefix that is used to display the output messages in a "level
    # way".
        try:
            log("%sSetting Participants for conference \"%s\"..."%(pp, self._conf.getTitle()))
            # Set recovered values:
            participation = self._conf.getParticipation()
            for part in participation.getParticipantList():
                participation.removeParticipant(part.getId())
            recoveredP = recoveredC.getParticipation()
            participation._obligatory = recoveredP._obligatory
            participation._allowedForApplying = recoveredP._allowedForApplying
            participation._addedInfo = True
            clonedStatuses = ["added", "excused", "refused"]
            ah = AvatarHolder()
            for p in recoveredP._participantList.values():
                if p.getStatus() in clonedStatuses :
                    newPart = Participant(self._conf)
                    user = None
                    try:
                        user = ah.getById(p._avatar.getId())
                    except KeyError:
                        user = None
                    newPart._avatar = user
                    newPart._firstName = p._firstName
                    newPart._familyName = p._familyName
                    newPart._title = p._title
                    newPart._address = p._address
                    newPart._affiliation = p._affiliation
                    newPart._telephone = p._telephone
                    newPart._fax = p._fax
                    newPart._email = p._email
                    newPart._status = p.getStatus()
                    newPart._present = p.isPresent()
                    participation.addParticipant(newPart)
            self._dbm.commit(True)
            log("%sEvent participants successfully set."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* while setting the participants: %s"%(pp, msg))
            return



class TmpDBMgr:
# Temporary database manager.

    _instance = None

    def __init__(self):
        self._storage = None
        self._db = None
        self._conn = None
        self._dbDatetime = None
        self._dr = DatabaseRecovery(self)

    def getInstance(cls):
        if cls._instance == None:
            cls._instance = TmpDBMgr()
        return cls._instance
    getInstance = classmethod(getInstance)

    def setDB(self, dt, pp=""):
    # Sets up the database as it was at the given datetime. Can take some
    # minutes because an index may have to be generated after the file creation.
    # pp is a print prefix that is used to display the output messages in a
    # "level way".
        now = datetime.now()
        if (self._dbDatetime != None):
            self.unsetDB(pp)
        log("%sSetting temporary database..."%pp)
        if self._createDBFile(dt, incPrintPrefix(pp)):
            self._storage = FileStorage(os.path.join(tmpPath, dataFile))
            self._db = MigratedDB(self._storage)
            if self._dr.proceed(dt, incPrintPrefix(pp)):
                self._dbDatetime = dt
                log("%sTemporary database set in %s."%(pp, datetime.now()-now))
                return
        log("%sTemporary database could not be set."%pp)

    def unsetDB(self, pp=""):
    # pp is a print prefix that is used to display the output messages in a
    # "level way".
        log("%sUnsetting previous temporary database..."%pp)
        self._storage.close()
        self._storage = None
        self._db = None
        self._dbDatetime = None
        log("%sTemporary database unset."%pp)

    def getDBDatetime(self):
        return self._dbDatetime

    def _createDBFile(self, dt, pp=""):
    # Creates the database file and returns 1 if it succeeded, 0 otherwise. pp
    # is a print prefix that is used to display the output messages in a "level
    # way".
        try:
            if currentPath == "":
                raise Exception("No folder defined for the database files. Check the configuration files.")
            if backupsPath == "":
                raise Exception("No folder defined for the database backups. Check the configuration files.")
            log("%sCreating new temporary database file..."%pp)
            ts = time.mktime(dt.timetuple())
            # dt has to be converted to UTC time, because the names of the backups
            # are the UTC times of these backups.
            dt = datetime.utcfromtimestamp(ts)
            dt = dt.strftime("%Y-%m-%d-%H-%M-%S")
            names = []
            l = os.listdir(backupsPath)
            for f in l:
                if os.path.isfile(os.path.join(backupsPath, f)) and (".fsz" in f):
                    names.append(os.path.splitext(f)[0])
            names.append("current")
            names.sort()
            index = 0
            # Find the right backup file. This file can also be the current database
            # file.
            for name in names:
                if name >= dt:
                    break
                index += 1
            if names[index] == "current":
            # Copy the current database file.
                shutil.copy(os.path.join(currentPath, dataFile), tmpPath)
                try:
                    shutil.copy("%s.index"%os.path.join(currentPath, dataFile), tmpPath)
                except Exception:
                    log("%sDatabase index file doesn't exist. It will be created later."%pp)
            else:
            # Database file recovery using compressed backup and repozo.
                os.system("%s %s %s %s %s %s %s %s %s"%(python, repozo, "-R",\
                "-D", names[index], "-o", "\"%s\""%os.path.join(tmpPath, dataFile),\
                "-r", "\"%s\""%backupsPath))
            log("%sTemporary database file created."%pp)
            return "OK"
        except Exception, msg:
            log("%s*ERROR* during the creation of the temporary database file: %s"%(pp, msg))
            return

    def startRequest( self ):
    # Initialises the temporary database and starts a new transaction.
        self._conn=self._db.open()

    def endRequest( self, commit=True ):
    # Closes the temporary database and commits changes.
        if commit:
            self.commit()
        else:
            self.abort()
        self._conn.close()
        self._conn = None

    def getDBConnection(self):
        if self._conn == None:
            raise Exception("Request not started.")
        return self._conn

    def getDBConnCache(self):
        if self._conn == None:
            raise Exception("Request not started.")
        return self._conn._cache

    def getDBClassFactory(self):
        if self._db == None:
            raise Exception("Database not set.")
        return self._db.classFactory

    def commit(self, sub=False):
        transaction.commit(sub)

    def abort(self):
        transaction.abort()

    def sync(self):
        self._conn.sync()

    def undoInfo(self, stepNumber=0):
    # One step is made of 1000 transactions. First step is 0 and returns
    # transactions 0 to 999.
        return self._db.undoInfo(stepNumber*1000, (stepNumber+1)*1000)

    def undo(self, trans_id):
        self._db.undo(trans_id)

    def loadObject(self, oid, version):
        return self._storage.load(oid, version)

    def storeObject(self, oid, serial, data, version, trans):
        return self._storage.store(oid, serial, data, version, trans)

    def tpcBegin(self, trans):
        self._storage.tpc_begin(trans)

    def tpcVote(self, trans):
        self._storage.tpc_vote(trans)

    def tpcFinish(self, trans):
        self._storage.tpc_finish(trans)

