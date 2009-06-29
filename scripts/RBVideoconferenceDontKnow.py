from MaKaC.common.db import DBMgr
from MaKaC.rb_factory import Factory
from MaKaC.rb_location import CrossLocationQueries

DBMgr.getInstance().startRequest()
Factory.getDALManager().connect()

idontknow = "I don't know"

rooms = CrossLocationQueries.getRooms( allFast = True )
for room in rooms:
    print "[%s][%s] %s"%(room.id, room.needsAVCSetup,room.getAvailableVC())
    if room.needsAVCSetup:
        if not idontknow in room.getAvailableVC():
            room.avaibleVC.append(idontknow)
            room.update()


Factory.getDALManager().commit()
Factory.getDALManager().disconnect()
DBMgr.getInstance().endRequest()



DBMgr.getInstance().startRequest()
Factory.getDALManager().connect()

rooms = CrossLocationQueries.getRooms( allFast = True )
for room in rooms:
    print "[%s][%s] %s"%(room.id, room.needsAVCSetup,room.getAvailableVC())


Factory.getDALManager().disconnect()
DBMgr.getInstance().endRequest()
