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

"""
Part of Room Booking Module (rb_)
Responsible: Piotr Wlodarek
"""


class DALManagerBase( object ):
    """
    Generic Data Access Layer manager for CRBS.

    Since room booking functionality must be plugable,
    Indico MUST NOT depend on any specific database.
    Therefore we need a generic way to manage data access layer.

    The class provides methods for:
    - connecting and disconnection from the database
    - commiting and rolling back the transactions

    Note: backend is not neccessary database. These may be
    i.e. web services calls or HTTP requests.
    """

    @staticmethod
    def connect():
        """
        Opens database connection. This method is called by Indico engine
        in the beginning of every HTTP request.
        """
        from MaKaC.rb_factory import Factory
        return Factory.getDALManager().connect()

    @staticmethod
    def disconnect():
        """
        Closes database connection. This method is called by Indico engine
        in the end of every HTTP request.
        """
        from MaKaC.rb_factory import Factory
        return Factory.getDALManager().disconnect()

    @staticmethod
    def commit():
        """ Commits the transaction. """
        from MaKaC.rb_factory import Factory
        return Factory.getDALManager().commit()

    @staticmethod
    def rollback():
        """ Rolls back the transaction. """
        from MaKaC.rb_factory import Factory
        return Factory.getDALManager().rollback()
