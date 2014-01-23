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

"""This script is used to convert all mx.DateTime objects from Indico
database into standard datetime and timedelta objects"""
import sys

from indico.core.db import DBMgr
from MaKaC.conference import CategoryManager
from MaKaC.common import indexes, timerExec
from datetime import datetime,timedelta

def main():
    """This script deletes existing category indexes and recreates them."""
    DBMgr.getInstance().startRequest()
    ch = CategoryManager()
    for cat in ch.getList():
      for conf in cat.getConferenceList():
        chconf(conf)
      get_transaction().commit()

    # Tasks
    # tl = Supervisor.
    htl = timerExec.HelperTaskList.getTaskListInstance()
    for task in htl.getTasks():
        chtask(task)
    DBMgr.getInstance().endRequest()

def chconf(conf):
    conf.startDate = chdt(conf.startDate)
    conf.endDate = chdt(conf.endDate)
    conf._creationDS = chdt(conf._creationDS)
    conf._modificationDS = chdt(conf._modificationDS)
    try:
	conf._archivingDate = chdt(conf._archivingDate)
    except:
	pass
    try:
	conf._submissionDate = chdt(conf._submissionDate)
    except:
	pass
    try:
	conf._archivingRequestDate = chdt(conf._archivingRequestDate)
    except:
	pass
    for sess in conf.getSessionList():
 	chsession(sess)
    for cont in conf.getContributionList():
	chcontrib(cont)
    chschedule(conf.getSchedule())
    chabstractmgr(conf.getAbstractMgr())

def chtask(task):
    try:
      task.startDate = chdt(task.startDate)
    except:
	pass
    try:
      task.endDate = chdt(task.endDate)
    except:
	pass
    try:
      task.lastDate = chdt(task.lastDate)
    except:
	pass
    try:
      task.interval = chtd(task.interval)
    except:
	pass

def chschedule(sch):
    try:
        if sch._startDate is not None:
            sch._startDate = chdt(sch._startDate)
    except:
	pass
    try:
        if sch._endDate is not None:
            sch._endDate = chdt(sch._endDate)
    except:
	pass
    for entry in sch.getEntries():
        chentry(entry)

def chentry(ent):
    try:
      ent.startDate = chdt(ent.startDate)
    except:
	pass
    try:
      ent.duration = chtd(ent.duration)
    except:
	pass

def chsession(sess):
    sess.startDate = chdt(sess.startDate)
    sess.duration = chtd(sess.duration)
    sess._contributionDuration = chtd(sess._contributionDuration)
    for slot in sess.getSlotList():
	chslot(slot)
    chschedule(sess.getSchedule())

def chslot(slot):
    slot.startDate = chdt(slot.startDate)
    slot.duration = chtd(slot.duration)
    slot._contributionDuration = chtd(slot._contributionDuration)
    chschedule(slot.getSchedule())

def chcontrib(cont):
    cont.startDate = chdt(cont.startDate)
    cont.duration = chtd(cont.duration)
    try:
	cont._modificationDS = chdt(cont._modificationDS)
    except:
	pass
    try:
	cont._archivingDate = chdt(cont._archivingDate)
    except:
	pass
    try:
      cont.getCurrentStatus()._date = chdt(cont.getCurrentStatus()._date)
    except:
      pass
    for sc in cont.getSubContributionList():
	chsubcont(sc)

def chsubcont(sc):
   sc.duration=chtd(sc.duration)

def chabstractmgr(abstmgr):
    try:
      abstmgr._submissionStartDate = chdt(abstmgr._submissionStartDate)
    except:
	pass
    try:
      abstmgr._submissionEndDate = chdt(abstmgr._submissionEndDate)
    except:
	pass
    try:
      abstmgr._modifDeadline = chdt(abstmgr._modifDeadline)
    except:
	pass
    for abs in abstmgr.getAbstractList():
        chabstract(abs)

def chabstract(abs):
    try:
      abs._modificationDate = chdt(abs._modificationDate)
    except:
	pass
    try:
      abs._submissionDate = chdt(abs._submissionDate)
    except:
	pass
    try:
      abs.getCurrentStatus()._date = chdt(abs.getCurrentStatus()._date)
    except:
      pass
    for track in abs.getTrackListSorted():
      judg = abs.getTrackJudgement(track)
      try:
        judg._date = chdt(judg._date)
      except:
        pass
    for entry in abs.getNotificationLog().getEntryList():
      entry._date = chdt(entry._date)
    for intComment in abs.getIntCommentList():
      intComment._creationDate = chdt(intComment._creationDate)
      intComment._modificationDate = chdt(intComment._modificationDate)



def chtd(DTD):
    try:
      return timedelta(seconds=DTD.seconds)
    except:
      return timedelta()

def chdt(DT):
    try:
      return datetime(int(DT.year),int(DT.month),int(DT.day),int(DT.hour),int(DT.minute),int(DT.second))
    except Exception, e:
      return None

if __name__ == "__main__":
    main()
