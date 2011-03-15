# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
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

from MaKaC.common import DBMgr

from indico.util.date_time import nowutc


class Statistics(object):
    """
    """
    pass


class CategoryStatistics(Statistics):

    def __init__(self, target):
        # The category for which we want the statistics is attached to the
        # instance at initialization time (target).
        self._target = target

    def getStatistics(self):
        # The returned statistics are composed of a dictionary containing other
        # dictionaries (one per statistic).
        if self._target.getNumConferences() != 0:
            categStats = self._target.getStatistics()
            return categStats
        return None

    @classmethod
    def updateStatistics(cls, cat, logger=None):
        dbi = DBMgr.getInstance()
        cat._statistics = cls._updateStatistics(cat, dbi, 0, logger)
        cat._p_changed = 1
        if logger:
            logger.info("Statistics calculation finished")

    @classmethod
    def _processEvent(cls, dbi, event, statistics):
        nevents = 0
        year = event.getStartDate().year
        if year in statistics["events"]:
            statistics["events"][year] += 1
        else:
            statistics["events"][year] = 1
        if len(event.getContributionList()) > 0:
            for cont in event.getContributionList():
                if cont.getStartDate() != None:
                    year = cont.getStartDate().year
                    if year in statistics["contributions"]:
                        statistics["contributions"][year] += 1
                    else:
                        statistics["contributions"][year] = 1
                    if len(cont.getSubContributionList()) > 0:
                        for scont in cont.getSubContributionList():
                            l = scont.getAllMaterialList()
                            for m in l:
                                statistics["resources"] += m.getNbResources()
                    l = cont.getAllMaterialList()
                    for m in l:
                        statistics["resources"] += m.getNbResources()
        if len(event.getSessionList()) > 0:
            for sess in event.getSessionList():
                l = sess.getAllMaterialList()
                for m in l:
                    statistics["resources"] += m.getNbResources()
        l = event.getAllMaterialList()
        for m in l:
            statistics["resources"] += m.getNbResources()

        # commit every 1000 events
        if nevents % 1000 == 999:
            dbi.commit()

    @classmethod
    def _updateStatistics(cls, cat, dbi, level=0, logger=None):

        ncat = 0
        statistics = cat.getStatistics()
        statistics["events"] = {}
        statistics["contributions"] = {}
        statistics["resources"] = 0

        if len(cat.getSubCategoryList()) > 0:
            for cat in cat.getSubCategoryList():
                cat._p_changed = 1
                cls._updateStatistics(cat, dbi, level + 1, logger)
                # commit after each category
                dbi.commit()

                for year in cat._statistics["events"]:
                    if year in statistics["events"]:
                        statistics["events"][year] += cat._statistics["events"][year]
                    else:
                        statistics["events"][year] = cat._statistics["events"][year]
                for year in cat._statistics["contributions"]:
                    if year in statistics["contributions"]:
                        statistics["contributions"][year] += cat._statistics["contributions"][year]
                    else:
                        statistics["contributions"][year] = cat._statistics["contributions"][year]
                statistics["resources"] += cat._statistics["resources"]

                ncat += 1

                # only at top level
                if level == 0:
                    # notify each 100 categories:
                    if logger and ncat > 0 and ncat % 100 == 0:
                        logger.info("%d categories already processed" % ncat)

        elif len(cat.getConferenceList()) > 0:
            for event in cat.getConferenceList():
                cls._processEvent(dbi, event, statistics)

        statistics["updated"] = nowutc()
        return statistics
