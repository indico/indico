# IMPORTANT!
# This file is not part of Indico, it has been done to work with the
# framework web.py, and it should be placed in the same folder as Jappix,
# which means that if Jappix is in /var/www/html, code.py has to be placed
# in /var/www/html/jappix/
# Once this is set you can activate the "Make possible to see chat
# logs and attach them to the material" checkbox in the Indico admin

import web, os, re, string
import dateutil.parser

CONF_FILE = '/var/www/html/jappix/code.py.conf'

urls = (
    '/', 'getlogs',
    '/delete', 'deletedir'
)
app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()


class getlogs:

    def GET(self):
        # get the range of dates to pick logs
        params = web.input()

        if hasattr(params,'cr'):
                name = params.cr
        else:
                return Exception('Chat room name not specified')

        if hasattr(params, 'sdate'):
                sDate = dateutil.parser.parse(params.sdate)
        else:
                sDate = None

        if hasattr(params, 'edate'):
                eDate = dateutil.parser.parse(params.edate)
        else:
                eDate = None

        # get the path of the logs dir from the conf file and get the list of log files
        logsPathFile = open(CONF_FILE, 'r')
        logsPath = logsPathFile.read()
        logsPathFile.close()
        logsPath = re.sub("\n","",logsPath)

        try:
                files = os.listdir(logsPath+name)
        except Exception, e:
                # file doesn't exist in our server, someone deleted it manually
                return ''
        filesToFetch = []
        for file in files:
                fDate = dateutil.parser.parse(string.replace(file, '.html',''))
                # we add it to the list if it's in the range of dates or there's no range specified
                if self._selectFile(fDate, sDate, eDate):
                        filesToFetch.append(fDate)

        # order the result and transform the dates into strings with the file name
        result = ''
        filesToFetch.sort()
        for file in filesToFetch:
                file = str(file.date())+'.html'
                file = open(logsPath+name+'/'+file, 'r')
                result += file.read()

        return result

    def _selectFile(self, fDate, sDate, eDate):
        if sDate and eDate:
                # both specified, compare with the two limits
                if fDate >= sDate and fDate <= eDate:
                        return True
                else:
                        return False
        elif sDate and not eDate:
                # only one specified
                if fDate >= sDate:
                        return True
                else:
                        return False
        elif not sDate and eDate:
                if fDate <= eDate:
                        return True
                else:
                        return False
        else:
                # no limits, we add all
                return True

class deletedir:

    def GET(self):
        params = web.input()
        logsPathFile = open(CONF_FILE, 'r')
        logsPath = logsPathFile.read()
        logsPathFile.close()
        logsPath = re.sub("\n","",logsPath)

        if params.cr is None:
                return Exception('Chat room name not specified')
        else:
                cr = params.cr
        newNumber = self._getDirName(logsPath, cr, 0)
        try:
                os.rename(logsPath+cr, logsPath+cr+'.'+str(newNumber))
        except Exception, e:
                # The directory is not there. Maybe some other request changed its name
                # quite at the same time, or maybe someone deleted the file manually.
                # In any case, there's nothing to change in this case
                pass

        return True

    def _getDirName(self, logsPath, cr, number):
        if os.path.exists(os.path.join(logsPath,cr+'.'+str(number))):
                number = self._getDirName(logsPath, cr, number+1)
        return number



if __name__ == "__main__":
    app.run()

