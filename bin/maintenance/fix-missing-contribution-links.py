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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict

from indico.core.db import DBMgr
from indico.util.console import conferenceHolderIterator, info, success
from indico.web.flask.app import make_app
from MaKaC.conference import ConferenceHolder
from MaKaC.webinterface.urlHandlers import UHContributionDisplay


def main():
    to_fix = defaultdict(list)
    info("Looking for broken contribution links in participants... (This might take a while.)")
    contribs = (x[1] for x in conferenceHolderIterator(ConferenceHolder(), deepness='contrib') if x[0] == 'contrib')
    for contrib in contribs:
        for part in contrib.getPrimaryAuthorList():
            if part.getContribution() is None:
                to_fix[contrib].append(('primary author', part))
        for part in contrib.getCoAuthorList():
            if part.getContribution() is None:
                to_fix[contrib].append(('co-author', part))
        for part in contrib.getAuthorList():
            if part.getContribution() is None:
                to_fix[contrib].append(('author', part))
        for part in contrib.getSpeakerList():
            if part.getContribution() is None:
                to_fix[contrib].append(('speaker', part))

    if not to_fix:
        success("No broken contribution links found.")
        return

    DBMgr.getInstance().sync()  # searching takes a long time, sync to prevent conflicts
    for contrib, parts in to_fix.iteritems():
        conference = contrib.getConference()
        conference_title = conference.getTitle() if conference is not None else 'N/A'
        conference_id = conference.getId() if conference is not None else 'N/A'
        print "Event {} (id {})".format(conference_title, conference_id)
        print "  Contribution {} (id {}):".format(contrib.getTitle(), contrib.getId())
        print "  {}".format(UHContributionDisplay.getURL(contrib))
        for part_type, part in parts:
            if part.getContribution() is not None:  # already fixed
                info("  - link already restored for {} {} (id {})".format(part_type, part.getFullName(), part.getId()))
                continue
            part._contrib = contrib
            success("  - restored link for {} {} (id {})".format(part_type, part.getFullName(), part.getId()))
    DBMgr.getInstance().commit()

if __name__ == '__main__':
    with make_app(set_path=True).app_context():
        with DBMgr.getInstance().global_connection(commit=False):
            main()
