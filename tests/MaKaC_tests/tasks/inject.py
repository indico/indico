import sys
sys.path = ['indico'] + sys.path
from MaKaC.common import db
from MaKaC.tasks.controllers import Supervisor
from MaKaC.tasks.indico import SampleOneShotTask, SamplePeriodicTask
from datetime import timedelta
dbInstance = db.DBMgr.getInstance()
dbInstance.startRequest()
#Supervisor.addTask(SampleOneShotTask())
Supervisor.addTask(SamplePeriodicTask(interval=timedelta(0, 0, 5)))
ok = False
while not ok:
    try:
        dbInstance.endRequest()
    except:
        dbInstance.sync()
    else:
        ok = True
