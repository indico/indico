# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

import datetime

from indico.util.fossilize import fossilizes
from indico.ext.statistics.base.reports import BaseStatisticsReport, BaseReportGenerator, IReportFossil
import indico.ext.statistics.piwik.queries as pq

from MaKaC.i18n import _
from MaKaC.conference import ConferenceHolder
from MaKaC.common.timezoneUtils import nowutc


class IPiwikReportFossil(IReportFossil):

    def _getContributions(self):
        pass
    _getContributions.name = 'contributions'

    def getContributionId(self):
        pass
    getContributionId.name = 'contribId'

    def getConferenceId(self):
        pass
    getConferenceId.name = 'confId'


class PiwikReportBase(BaseStatisticsReport):

    def __init__(self):
        BaseStatisticsReport.__init__(self)
        self._reportSetters = {'images': 'setImageSource',
                               'values': 'setValueSource'}


class PiwikReport(PiwikReportBase):

    fossilizes(IPiwikReportFossil)
    _defaultReportInterval = 14

    def __init__(self, startDate, endDate, confId, contribId=None):
        """
        Builds the map of generators to fill this object's variables before
        fossilization.
        """

        PiwikReportBase.__init__(self)
        report = BaseReportGenerator

        self._conf = ConferenceHolder().getById(confId)
        self._confId = confId
        self._contribId = contribId
        self._buildDateRange(startDate, endDate)
        self._contributions = []

        params = {'startDate': self._startDate,
                  'endDate': self._endDate,
                  'confId': confId}

        if contribId:
            params['contribId'] = contribId

        # This report only has need for images and values, not for widgets.
        self._reportGenerators = {
            'values': {'visits': report(pq.PiwikQueryMetricConferenceVisits, params),
                    'uniqueVisits': report(pq.PiwikQueryMetricConferenceUniqueVisits, params),
                    'visitLength': report(pq.PiwikQueryMetricConferenceVisitLength, params),
                    'referrers': report(pq.PiwikQueryMetricConferenceReferrers, params),
                    'peakDate': report(pq.PiwikQueryMetricConferencePeakDateAndVisitors, params)}
             }

        self._buildReports()
        self._buildConferenceContributions()

    def _buildDateRange(self, startDate, endDate):
        """
        If the default values are passed through, computes the appropriate date
        range based on whether today is before or after the conference end date.
        If after, end of period is set as conference end date. Start date is then
        calculated by the _defaultReportInterval difference.
        """

        def getStartDate():
            interval = datetime.timedelta(days=self._defaultReportInterval)
            adjustedStartDate = self._endDateTime - interval

            return str(adjustedStartDate.date())

        def getEndDate():
            today = nowutc()
            confEndDate = self._conf.getEndDate()

            self._endDateTime = confEndDate if today > confEndDate else today

            return str(self._endDateTime.date())

        self._endDate = endDate if endDate else getEndDate()
        self._startDate = startDate if startDate else getStartDate()

    def _buildConferenceContributions(self):
        """
        As this implementation permits the viewing of individual contributions,
        we make a list of tuples associating the uniqueId with the title
        (and start time) to be fossilized.
        """
        contributions = self._conf.getContributionList()

        if contributions:
            self._contributions.append(('None', str(_('Conference: ') + self._conf.getTitle())))

            for ctrb in contributions:

                if not ctrb.isScheduled():
                    continue

                ctrbTime = str(ctrb.getStartDate().hour) + ':' + str(ctrb.getStartDate().minute)
                ctrbInfo = _('Contribution: ') + ctrb.getTitle() + ' (' + ctrbTime + ')'
                value = (ctrb.getUniqueId(), ctrbInfo)
                self._contributions.append(value)
        else:
            self._contributions = False

    def _getContributions(self):
        return self._contributions

    def getConferenceId(self):
        return self._confId

    def getContributionId(self):
        return self._contribId
