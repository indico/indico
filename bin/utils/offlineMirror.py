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

import re, os, sys, time, datetime, urllib
from indico.core.db import DBMgr
from MaKaC.common.indexes import IndexesHolder
from MaKaC.webinterface import urlHandlers
from MaKaC.conference import ConferenceHolder
from indico.web.flask.app import make_app

WGET_COMMAND = """wget -nv -mk --accept '*confId=%s*,*conferenceTimeTable.py*,*confAuthorIndex.py*,*internalPage.py*,*materialDisplay.py*,*access*,*sessionDisplay.py*,*contributionDisplay.py*,*contributionListDisplay.py*,*conferenceProgram.py*,*getVars*,*.ico,*.png,*.jpg,*.gif,*.css,*.js' --html-extension %s -P %s --domains='%s'"""


def main():
    if len(sys.argv) == 2:
        day = datetime.datetime.now()
    elif len(sys.argv) == 3:
        day = time.strptime(sys.argv[2], "%Y%m%d")
    else:
        print "Usage: %s folder [date YYMMDD]" % (sys.argv[0])
        sys.exit(-1)

    dest = sys.argv[1]

    if not os.path.exists(dest):
        os.makedirs(dest)

    index = cacheDay(dest, day)

    generateIndex(dest, index, day)

def cacheDay(dest, day):
    """
    Cache a day, by calling wget in "mirror" mode
    """

    dbi = DBMgr.getInstance()
    dbi.startRequest()

    index = {}

    calIdx = IndexesHolder().getIndex('calendar')

    objs = calIdx.getObjectsInDay(day)

    for confId in objs:

	if confId == '': continue

        obj = ConferenceHolder().getById(confId)
        url = str(urlHandlers.UHConferenceDisplay.getURL(obj))

        savedDirs = re.match(r'http:\/\/(.*)', url).group(1).split('/')

        print "Calling wget for %s..." % url
        os.system(WGET_COMMAND % (confId, url,
                                  os.path.join(dest, confId),
                                  savedDirs[0]))

        print "done!"

        index[confId] = (os.path.join(confId,*savedDirs)+'.html', obj.getTitle())

    dbi.endRequest(False)

    return index

def generateIndex(dest, index, day):

    print "Generating index..."

    fLastUpdateDate = datetime.datetime.now().strftime("%c")
    fDayDate = day.strftime("%a, %d %b %Y")

    liItems = []

    for k, (url, title) in index.iteritems():
        print "\tAdding %s (%s)" % (k, title)
        liItems.append("<li><a href=\"%s\">%s</a></li>" % (urllib.quote(url), title))

    html = """
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
    "http://www.w3.org/TR/html4/strict.dtd">

    <html>

    <head>

    <title>Indico offline mirror - %s</title>
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />

    </head>

    <body>

    <h1>Indico offline mirror</h1>
    <h2>%s</h2>

    <ul>
    %s
    </ul>

    <small>Last update: %s</small>

    </body>
    </html>

    """ % (fDayDate, fDayDate, ''.join(liItems),  fLastUpdateDate)

    f = open(os.path.join(dest, 'index.html'), 'w')
    f.write(html)
    f.close()

    print "done!"

if __name__ == '__main__':
    appplication = make_app(True)
    with appplication.app_context():
        main()
