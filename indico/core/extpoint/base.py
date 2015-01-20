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

from zope.interface import Interface

class Component(object):
    """
    Base class for components
    """
    def __init__(self):
        # the lowest priority possible
        self.priority = 10

    def getPriority(self):
        return self.priority


class IListener(Interface):
    """
    Base IListener interface. All listeners should inherit from this one.
    """


class IContributor(Interface):
    """
    Base IContributor interface. All contributors should inherit from this one.
    """

# TODO: Should contain ComponentManager, Observable, etc...
