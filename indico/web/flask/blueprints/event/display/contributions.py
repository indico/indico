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
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import conferenceDisplay, contribDisplay, subContribDisplay, authorDisplay
from indico.web.flask.blueprints.event.display import event


# Contribution list
event.add_url_rule('/contributions', 'contributionListDisplay', conferenceDisplay.RHContributionList)
event.add_url_rule('/contributions.pdf', 'contributionListDisplay-contributionsToPDF',
                   conferenceDisplay.RHContributionListToPDF, methods=('POST',))

with event.add_prefixed_rules('/session/<sessionId>'):
    # Display contribution
    event.add_url_rule('/contribution/<contribId>', 'contributionDisplay', contribDisplay.RHContributionDisplay)
    event.add_url_rule('/contribution/<contribId>.ics', 'contributionDisplay-ical', contribDisplay.RHContributionToiCal)
    event.add_url_rule('/contribution/<contribId>.marc.xml', 'contributionDisplay-marcxml',
                       contribDisplay.RHContributionToMarcXML)
    event.add_url_rule('/contribution/<contribId>.xml', 'contributionDisplay-xml', contribDisplay.RHContributionToXML)
    event.add_url_rule('/contribution/<contribId>.pdf', 'contributionDisplay-pdf', contribDisplay.RHContributionToPDF)
    event.add_url_rule('/contribution/<contribId>/<subContId>', 'subContributionDisplay',
                       subContribDisplay.RHSubContributionDisplay)
    event.add_url_rule('/contribution/<contribId>/<subContId>.marc.xml', 'subContributionDisplay-marcxml',
                       subContribDisplay.RHSubContributionToMarcXML)
    event.add_url_rule('/contribution/<contribId>/author/<authorId>', 'contribAuthorDisplay',
                       authorDisplay.RHAuthorDisplay)

# Authors/Speakers
event.add_url_rule('/authors', 'confAuthorIndex', conferenceDisplay.RHAuthorIndex)
event.add_url_rule('/speakers', 'confSpeakerIndex', conferenceDisplay.RHSpeakerIndex)
