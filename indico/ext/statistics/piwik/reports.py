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

import datetime

from indico.util.fossilize import IFossil, fossilizes, Fossilizable
from indico.ext.statistics.base.reports import BaseStatisticsReport, BaseReportGenerator, IReportFossil
import indico.ext.statistics.piwik.queries as pq
from MaKaC.conference import ConferenceHolder

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
        self._reportSetters = {'images' : 'setImageSource',
                               'widgets' : 'setWidgetSource',
                               'values' : 'setValueSource'}

class PiwikReport(PiwikReportBase):

    fossilizes(IPiwikReportFossil)

    def __init__(self, startDate, endDate, confId, contribId = None):
        """
        Builds the map of generators to fill this object's variables before
        fossilization.
        """
        PiwikReportBase.__init__(self)
        report = BaseReportGenerator

        self._conf = ConferenceHolder().getById(confId)
        self._confId = confId
        self._contribId = contribId
        self._startDate = startDate
        self._endDate = endDate
        self._checkDatesSanity()
        self._contributions = []

        params = {'startDate' : self._startDate,
                  'endDate' : self._endDate,
                  'confId' : confId}

        if contribId:
            params['contribId'] = contribId

        # This report only has need for images and values, not for widgets.
        self._reportGenerators = {
            'images' : {'visitsDay' : report(pq.PiwikQueryGraphConferenceVisits, params),
                        'visitsOS' : report(pq.PiwikQueryGraphConferenceDevices, params),
                        'visitsCountry' : report(pq.PiwikQueryGraphConferenceCountries, params)},

            'values' : {'visits' : report(pq.PiwikQueryMetricConferenceVisits, params),
                        'uniqueVisits' : report(pq.PiwikQueryMetricConferenceUniqueVisits, params),
                        'visitLength' : report(pq.PiwikQueryMetricConferenceVisitLength, params),
                        'referrers' : report(pq.PiwikQueryMetricConferenceReferrers, params),
                        'peakDate' : report(pq.PiwikQueryMetricConferencePeakDateAndVisitors, params)}
             }

        self._buildReports()
        self._buildConferenceContributions()

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
                ctrbTime = str(ctrb.getStartDate().hour) + ':' + str(ctrb.getStartDate().minute)
                ctrbInfo = _('Contribution: ') + ctrb.getTitle() + ' (' + ctrbTime + ')'
                value = (ctrb.getUniqueId(), ctrbInfo)
                self._contributions.append(value)
        else:
            self._contributions = False

    def _checkDatesSanity(self):
        """
        If there are missing dates for startDate or endDate, suitable values
        are determined and applied.
        """
        if self._startDate and self._endDate:
            return

        if not self._endDate:
            self._endDate = datetime.date.today()
        if not self._startDate:
            start = self._conf.getCreationDate()
            self._startDate = str(start.date())

    def _getContributions(self):
        return self._contributions

    def getConferenceId(self):
        return self._confId

    def getContributionId(self):
        return self._contribId
