import sys
sys.path = ['indico'] + sys.path
from MaKaC.tasks.controllers import Supervisor
Supervisor.getInstance().run()
