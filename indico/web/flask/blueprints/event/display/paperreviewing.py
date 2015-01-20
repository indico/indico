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

from MaKaC.webinterface.rh import paperReviewingDisplay
from indico.web.flask.blueprints.event.display import event


# paperReviewingDisplay.py
event.add_url_rule('/paper-reviewing/', 'paperReviewingDisplay', paperReviewingDisplay.RHPaperReviewingDisplay)
event.add_url_rule('/paper-reviewing/templates/', 'paperReviewingDisplay-downloadTemplate',
                   paperReviewingDisplay.RHDownloadPRTemplate)
event.add_url_rule('/paper-reviewing/templates/<reviewingTemplateId>', 'paperReviewingDisplay-downloadTemplate',
                   paperReviewingDisplay.RHDownloadPRTemplate)
event.add_url_rule('/paper-reviewing/upload', 'paperReviewingDisplay-uploadPaper', paperReviewingDisplay.RHUploadPaper)
