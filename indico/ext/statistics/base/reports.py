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
from indico.util.fossilize import IFossil, fossilizes, Fossilizable

from MaKaC.common.timezoneUtils import nowutc, utc2server


class IReportFossil(IFossil):
    """
    The design of this fossil, and any which inherit from it, is that there
    should be at least 3 distinct groups of what is stored for view logic and
    for caching. 'images' refers to base64 encoded image data.
    """

    def getImagesSources(self):
        pass
    getImagesSources.name = 'images'

    def getWidgetSources(self):
        pass
    getWidgetSources.name = 'widgets'

    def getValueSources(self):
        pass
    getValueSources.name = 'metrics'

    def getStartDate(self):
        pass

    def getEndDate(self):
        pass

    def getDateGenerated(self):
        pass


class BaseStatisticsReport(Fossilizable, object):

    fossilizes(IReportFossil)

    def __init__(self):
        # These are the containers which the report returns to the view.
        self._reportImageSources = {}
        self._reportWidgetSources = {}
        self._reportValueSources = {}

        self._reportGenerators = {}
        self._reportMethods = {}
        self._reportSetters = {}

        self._reportGenerated = None

        self._startDate = None
        self._endDate = None

    def _buildReports(self):
        """
        All reports for this instance should be logged with a generator
        in self._reportGenerators. This method cyclces through these
        generators, executes the get command on the query object and then
        the set command on the report object.
        """

        for resultType, generators in self._reportGenerators.iteritems():
            for resultName, gen in generators.iteritems():
                setMethod = self._reportSetters.get(resultType)
                setFunc = getattr(self, setMethod)

                if setFunc is None:
                    raise Exception('Method %s not implemented' % setMethod)

                setFunc(resultName, gen.getResult())

        self._reportGenerated = utc2server(nowutc(), naive=False)

    def getDateGenerated(self):
        return self._reportGenerated

    def getImagesSources(self):
        return self._reportImageSources

    def getValueSources(self):
        return self._reportValueSources

    def getWidgetSources(self):
        return self._reportWidgetSources

    def getStartDate(self):
        return self._startDate

    def getEndDate(self):
        return self._endDate

    def setImageSource(self, name, source):
        """
        Only want a 1:1 map of key value, each image should have its own
        title, therefore no appending to lists etc. The values of these
        associations will be the raw, base64 encoded value of the image
        itself.
        """
        sources = self.getImagesSources()
        sources[name] = source

    def setValueSource(self, name, source):
        """
        This is a map of key : value relating to metrics retrieved from
        the API which have only a string or numerical value.
        """
        sources = self.getValueSources()
        sources[name] = source

    def setWidgetSource(self, name, source):
        """
        The values of this dictionary will be the full Piwik API URLs for
        widget iframe values.
        """
        sources = self.getWidgetSources()
        sources[name] = source


class BaseReportGenerator(object):
    """
    Acts as a wrapper around a query object allowing for the Report
    object to iterate through queries to propagate with their args
    and populate its own data structures.

    @param query: Reference to uninstantiated query object
    @params arg: Dictionary of params to be passed on query instantiation.
    @param method: String name of method to be called, defaults to 'getQueryResult'
    @params funcArgs: Dictionary of args to be passed through to the called
    method, if left as None, no args passed.
    """

    def __init__(self, query, args, method='getQueryResult', funcArgs=None):
        self._query = query
        self._method = method
        self._args = args
        self._funcArgs = funcArgs

    def _performCall(self):
        """
        Instantiates the query object with the arguements provided,
        creates a reference to the required method call and returns the
        value.
        """
        queryObject = self._query(**self._args)
        func = getattr(queryObject, self._method)

        if self._funcArgs:
            return func(**self._funcArgs)
        else:
            return func()

    def getResult(self):
        """
        Wrapper around _performCall in case inheriting classes need to
        do some actions around the result before passing back.
        """
        return self._performCall()

    def getMethod(self):
        """ Returns the string method name associated with this object. """
        return self._method
