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

from indico.core.db import DBMgr

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

        cls._updateStatistics(cat, dbi, 0, logger)
        if logger:
            logger.info("Statistics calculation finished")

        dbi.commit()

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

        stats = cat.getStatistics()
        stats["events"] = {}
        stats["contributions"] = {}
        stats["resources"] = 0

        if len(cat.getSubCategoryList()) > 0:
            for scat in cat.getSubCategoryList():
                # only at top level
                if level == 0 and logger:
                    logger.info("Processing '%s' (%s)" % (scat.getTitle(),
                                                          scat.getId()))

                cls._updateStatistics(scat, dbi, level + 1, logger)

                for year in scat._statistics["events"]:
                    if year in stats["events"]:
                        stats["events"][year] += scat._statistics["events"][year]
                    else:
                        stats["events"][year] = scat._statistics["events"][year]
                for year in scat._statistics["contributions"]:
                    if year in stats["contributions"]:
                        stats["contributions"][year] += scat._statistics["contributions"][year]
                    else:
                        stats["contributions"][year] = scat._statistics["contributions"][year]
                stats["resources"] += scat._statistics["resources"]

        elif cat.conferences:
            for event in cat.conferences:
                cls._processEvent(dbi, event, stats)

        stats["updated"] = nowutc()
        cat._statistics = stats
        cat._p_changed = 1

        dbi.commit()

        if level == 1:
            logger.info("%s : %s" % (cat.getId(), cat._statistics))

        return stats
