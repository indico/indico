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

import getopt, sys
from indico.core.db import DBMgr
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.plugins.RoomBooking.default.reservation import Reservation
from MaKaC.rb_reservation import ReservationBase
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.user import AvatarHolder

def changeCreator(oldUser, newUser):
    dbi = DBMgr.getInstance()

    dbi.startRequest()
    Factory.getDALManager().connect()

    # check if the users exist
    if AvatarHolder().getById(oldUser) is None:
        print "There is no user with id %s"%oldUser
        return
    if AvatarHolder().getById(newUser) is None:
        print "There is no user with id %s"%newUser
        return

    resvEx = ReservationBase()
    resvEx.createdBy = oldUser

    allResv4OldUser = CrossLocationQueries.getReservations( resvExample = resvEx)

    if allResv4OldUser == []:
        print "No reservations for user %s"%oldUser
        return

    # resvs = ReservationBase.getReservations()
    # allResv4OldUser = [x for x in allResv if x.createdBy == oldUser]

    if type(allResv4OldUser) is not list:
        allResv4OldUser = [allResv4OldUser]

    # Modify reservations
    for r in allResv4OldUser:
        r.createdBy = newUser
        #print r.createdBy, r.id

    # Update index
    userReservationsIndexBTree = Reservation.getUserReservationsIndexRoot()

    newUserResvs = userReservationsIndexBTree.get( newUser )
    if newUserResvs == None:
        newUserResvs = [] # New list of reservations for this room
        userReservationsIndexBTree.insert( newUser, newUserResvs )
    newUserResvs.extend( allResv4OldUser )
    userReservationsIndexBTree[newUser] = newUserResvs[:]

    if userReservationsIndexBTree.has_key(oldUser):
        userReservationsIndexBTree.pop(oldUser)

    userReservationsIndexBTree._p_changed = 1

    # close DB connection
    Factory.getDALManager().commit()
    Factory.getDALManager().disconnect()
    dbi.endRequest()
    print "%s reservations have moved from creator %s to creator %s" % (len(allResv4OldUser), oldUser, newUser)

def listResv4User(user):
    dbi = DBMgr.getInstance()

    dbi.startRequest()
    Factory.getDALManager().connect()

    resvEx = ReservationBase()
    resvEx.createdBy = user

    allResv = CrossLocationQueries.getReservations( resvExample = resvEx)
    print "User %s has %s resevations created by him/her"%(user, len(allResv))

    Factory.getDALManager().disconnect()
    dbi.endRequest()

def usage():
    print "Usage: %s -o 44 -n 55" % sys.argv[0]

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:n:l:", ["old=", "new=", "list="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(0)
    oldUser = None
    newUser = None
    userToList = None
    for o, a in opts:
        if o == "-o":
            oldUser = str(a)
        elif o == "-n":
            newUser = str(a)
        elif o == "-l":
            userToList = str(a)
        else:
            assert False, "unhandled option"

    if userToList:
        listResv4User(userToList)
    elif oldUser and newUser:
        changeCreator(oldUser, newUser)
    else:
        usage()
        sys.exit(0)


if __name__ == "__main__":
    main()
