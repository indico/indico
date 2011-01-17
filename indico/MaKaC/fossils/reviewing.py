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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.ddd

from MaKaC.common.fossilize import IFossil
from MaKaC.common.Conversion import Conversion
from MaKaC.fossils.user import IAvatarMinimalFossil

class IReviewFossil(IFossil):
    """
    Fossil for the review object
    """

    def getRefereeDueDate(self):
        pass
    getRefereeDueDate.convert = Conversion.datetime


class IReviewManagerFossil(IFossil):
    """
    Fossil for review manager
    """

    def getReferee(self):
        pass
    getReferee.convert = lambda r: r and r.getStraightFullName()

    def getEditor(self):
        pass
    getEditor.convert = lambda e: e and e.getStraightFullName()

    def getReviewersList(self):
        pass
    getReviewersList.result = IAvatarMinimalFossil

    def getLastReview(self):
        pass
    getLastReview.result = IReviewFossil


class IReviewingQuestionFossil(IFossil):
    """
    Fossil for the reviewing questions
    """
    def getId(self):
        pass

    def getText(self):
        pass







