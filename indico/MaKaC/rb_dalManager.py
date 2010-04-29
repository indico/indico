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
