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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


class Negotiator:
    """
        Abstract class - shall be inherited by all classes participating in
        time negotiations supported by Negotiation module
    """
    def __init__(self, avator):
        self._avator = avator
    
    def getNegotiatorInfo(self):
        """
            Must be replaced in an inheriting class..!!
        """
        return "[abstract negotiator]"
    
    def getAvator(self):
        return self._avator
        
    def setAvatar(self, avatar):
        if self._avatar is not None :
            return False            
        self._avatar = avatar
        return True
    
#-----------------------------------------------------------------------------------

class Negotiation :
    
    def __init__(self):
        self._negotiationRange = None
        self._negotiationStep = None
        self._restrictionList = []
        self._fixedRestrictionList = []
        self._solutionList = []
        self._proposedSolution = None
        self._finished = False
        self._automaticChoice = False
    
    def isAutomatic(self):
        return self._automaticChoice
        
    def isFinished(self):
        return self._finished
        
    def addRestriction(self, restriction):
        """
            Guaranties that resriction list will be sorted by Min
        """
        if restriction is None :
            return False
        added = False
        for i in range(len(self._restrictionList)) :
            if restriction.isMinSmallerMin(self._restrictionList[i]) :
                self._restrictionList.insert(i,restriction)
                added = True
                break
        if not added :
            self._restrictionList.append(restriction)
        return True
    
    def addFixedRestriction(self, restriction):
        """
            Fixed restriction list need not to be sorted
        """
        if restriction is None :
            return False
        self._fixedRestrictionList.append(restriction)
        return True
        
    def _applyFixedRestrictions(self):
        if negotiationRange is None :
            return False
        for restriction in self._fixedRestrictions :
            newRestrictionList = restriction.apply(negotiationRange)
            for newRestriction in newRestrictionList :
                self.addRestriction(newRestriction)
        return True
            
        
    def getNegotiationStep(self):
        return self._negotiationStep
        
    def setNegotiationStep(self, range):
        if range is None :
            return False
        if self._negotiationRange is not None :
            if self._negotiationRange.compareSpan(range)  <= 0 :
                return False
        self._negotiationStep = range
        return True
        
    def getNegotiationRange(self):
        return self._negotiationRange
        
    def setNegotiationRange(self, range):
        if range is None :
            return False
        self._negotiationRange = range
        return True
        
    def getProposedSolution(self):
        return self._proposedSolution
        
    def setProposedSolution(self, range):
        if range is None :
            return False
        if self._negotiationRange is None :
            return False
        if not(self._negotiationRange.isMinSmallerMin(range) and range.isMaxSmallerMax(self._negotiationRange)) :
            return False
        self._proposedSolution = range
        return True
    
    def getSolutionList(self):
        return self._solutionList
        
    def getSolution(self, index = 0):
        if len(self._solutionList) == 0 :
            return None
        if index >= len(self._solutionList) or index < 0 : 
            return None
        return self._solutionList[index]
        
        
    def findAllSolutions(self):
        if restrictionList is None :
            return False
        if self._negotiationRange is None :
            return False
        if self._negotiationStep is None :
            return False
        if self._proposedSolution is None :
            return False
        if not self._applyFixedRestrictions() :
            return False
            
        if not self._findSolutions(self._restrictionList) :
            return False
        if len(self._solutionList) > 0 :
            return True
        
        restrictionIndex = 0
        while restrictionIndex < len(self._restrictionList) :
            rl = self._restrictionList[:]
            if not rl[restrictionIndex] :
                rl.remove(restrictionIndex)
                self._findSolutions(rl)
            restrictionIndex += 1
        
        self._finished = True
        return True
        
    def _findSolutions(self, restrictionList):
        actualSolution = Solution(self._negotiationRange,self._proposedSolution) 
        restrictionIndex = 0
        
        while restrictionIndex < len(self._restrictionList) :
            actualRestriction = restrictionList[restrictionIndex]
            actualPoint = actualRestriction.moveForward(actualRestriction)
            if actualRestriction.isMinSmallerMin(actualSolution) or actualRestriction.isMinEqualMin(actualSolution) :
                if self._negotiationRange.isMaxEqualMin(actualPoint) or self._negotiationRange.isMaxSmalerlMin(actualPoint) :
                    break
            if actualSolution.isMaxSmallerMin(actualRestriction) :
                self._solutionList.append(actualSolution)
            actualPoint = actualPoint.movedForward(self._negotiationStep)
            actualSolution = Solution(actualPoint,self._proposedSolution)
            restrictionIndex = restrictionIndex + 1
            
        return True
    
#-----------------------------------------------------------------------------------

class Range :
    """
        Class used as an interface - base interface of all negitiable units
    """
    def __init__(self):
        """
            Must be replaced in an inheriting class..!!
        """
        pass
    
    def __init__(self, startRange, scopeRange):
        """
            Must be replaced in an inheriting class..!!
        """
        pass
    
    def getMin(self):
        """
            Must be replaced in an inheriting class..!!
        """
        pass
        
    def getMax(self):
        """
            Must be replaced in an inheriting class..!!
        """
        pass

    def isMinSmallerMin(self,range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False

    def isMinSmallerMax(self,range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False
        
    def isMaxSmallerMin(self, range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False
        
    def isMaxSmallermax(self, range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False
        
    def isMinEqualMin(self, range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False
        
    def isMinEqualMin(self, range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False
        
    def isMaxEqualMin(self, range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False
        
    def isMaxEqualMax(self, range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False
        
    def isEqual(self, range):
        """
            Must be replaced in an inheriting class..!!
        """
        return False

    def compareSpan(self, range):
        """
            Must be replaced in an inheriting class..!!
            Returns :
                -2 : Error
                -1 : Smaller
                 0 : Equal
                 1 : Bigger
        """
        return -2
        
    def moveForward(self, range):
        """
            Must be replaced in an inheriting class..!!
        """
        return None
        

#-----------------------------------------------------------------------------------        

class Restriction(Range) :
    """
        Class used as an interface - to be inherited by all restriction implementations
    """
    def isFixed(self):
        """
            Indicates wheather restriction is or cames from a fixed restriction
            Must be replaced in an inheriting class..!!
        """
        return False
        
    def apply(self, range):
        """
            Applies fixed restriction to the given range - returns list of 
            'applied' restrictions
            Only for fixed restrictions..!!
            Must be replaced in an inheriting class..!!
        """
        return None
    
class Solution(Range):
    """
        Class used as an interface -  to be inherited by all restriction implementations
    """
    
#-----------------------------------------------------------------------------------        
#-----------------------------------------------------------------------------------        

class DateRange(Range):
    """
        Implements interface Range
    """
    def __init__(self):
        self._minDate = None
        self._MaxDate = None
        
    def __init__(self, startRange, scopeRange):
        if type(startRange) != negotiations.DateRange :
            return
        if type(scopeRange) != negotiations.DateRange :
            return
        self._minDate = startRange.getMin()
        scope = scopeRange.getMax() - scopeRange.getMin()
        self._maxDate = self._minDate + scope
        
    def getMin(self):
        return self._minDate
               
    def getMax(self):
        return self._maxDate
        
    def isMinSmallerMin(self, dataRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._minDate < dataRange._minDate :
            return True
        return False
    
    def isMinSmallerMax(self, dataRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._minDate < dateRange._maxDate :
            return True
        return False
    
    def isMaxSmallerMin(self, dataRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._maxDate < dateRange._minDate :
            return True
        return False
        
    def isMaxSmallerMax(self, dataRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._maxDate < dateRange._maxDate :
            return True
        return False
        
    def isMinEqualMin(self, dataRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._minDate == dateRange._minDate :
            return True
        return False
        
    def isMinEqualMax(self, dataRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._minDate == dateRange._maxDate :
            return True
        return False
        
    def isMaxEqualMin(self, dataRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._maxDate == dateRange._minDate :
            return True
        return False
        
    def isMaxEqualMax(self, dataRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._maxDate == dateRange._maxDate :
            return True
        return False
        
    def isEqual(self, dateRange):
        if type(dataRange) != negotiations.DateRange :
            return False
        if self._maxDate == dateRange._maxDate and self._minDate == dateRange._minDate :
            return True
        return False
        
    def compateSpan(self, dateRange):
        if type(dataRange) != negotiations.DateRange :
            return -2
        if (self._maxDate - self._minDate) < (dateRange._maxDate - dateRange._minDate) :
            return -1
        if (self._maxDate - self._minDate) == (dateRange._maxDate - dateRange._minDate) :
            return 0
        if (self._maxDate - self._minDate) > (dateRange._maxDate - dateRange._minDate) :
            return 1
        return -2
    
    def movedForward(self, dateRange):
        """
            Must be replaced in an inheriting class..!!
        """
        return None
        
    
#-----------------------------------------------------------------------------------        

class DateRestriction(DateRange, Restriction):
    """
        Inherits from class DateRange
        Implements interfase Restriction
    """
    
    def __init__(self, fixed = False):
        self._fixed = fixed
        self._type = None
        
    def isFixed(self):
        return self._fixed
        
    def setType(self, type):
        if not self._fixed :
            return False
        if type not in ["exact","day","week","month","year"] :
            return False
        self._type = type
        return True
        
    def _apply(self, dateRange):
        if type(dataRange) != negotiations.DateRange :
            return None
        
        restrictionList = []
        if self._type == "exact" :
            restriction = DateRestriction(True)
            restriction._minDate = self._minDate
            restriction._maxDate = self._maxDate
            restrictionList.appedn(restriction)
        if self._type == "day" :
            restriction = DateRestriction(True)                
            restriction._minDate = datetime(dateRange._minDate.year,dateRange._minDate.month,dateRange._minDate.day,self.minDate.seconds,0)
            restriction._maxDate = datetime(dateRange._minDate.year,dateRange._minDate.month,dateRange._minDate.day,self.maxDate.seconds,0)
            while True :
                if dateRange.isMaxSmallerMin(restriction) or dateRange.isMaxEqualMin(restriction) :
                    break
                restrictionList.append(restriction)
                newRestriction = DateRestriction(True)
                newRestriction._minDate = datetime(restriction._minDate.year,restriction._minDate.month, restriction._minDate.day,restriction._minDate.seconds, 0)
                newRestriction._maxDate = datetime(restriction._maxDate.year,restriction._maxDate.month, restriction._maxDate.day,restriction._maxDate.seconds, 0)
                newRestriction._minDate += timedelta(days=1)
                newRestriction._maxDate += timedelta(days=1)
                restriction = newRestriction
                
        if self._type == "week" :
            restriction = DateRestriction(True)
            restriction._minDate = datetime(dateRange._minDate.year,dateRange._minDate.month,dateRange._minDate.day,self.minDate.seconds,0)
            restriction._maxDate = datetime(dateRange._minDate.year,dateRange._minDate.month,dateRange._minDate.day,self.maxDate.seconds,0)
            while True :
                if dateRange.isMaxSmallerMin(restriction) or dateRange.isMaxEqualMin(restriction) :
                    break
                if dateRange.getMin().weekday() == restriction.getMin().weekday() :
                    restrictionList.append(restriction)
                newRestriction = DateRestriction(True)
                newRestriction._minDate = datetime(restriction._minDate.year,restriction._minDate.month, restriction._minDate.day,restriction._minDate.seconds, 0)
                newRestriction._maxDate = datetime(restriction._maxDate.year,restriction._maxDate.month, restriction._maxDate.day,restriction._maxDate.seconds, 0)
                newRestriction._minDate += timedelta(days=1)
                newRestriction._maxDate += timedelta(days=1)
                restriction = newRestriction
        
        if self._type == "month" :
            restriction = DateRestriction(True)
            restriction._minDate = datetime(dateRange._minDate.year,dateRange._minDate.month,self._minDate.day,self.minDate.seconds,0)
            restriction._maxDate = datetime(dateRange._minDate.year,dateRange._minDate.month,self._maxDate.day,self.maxDate.seconds,0)
            while True :
                if dateRange.isMaxSmallerMin(restriction) or dateRange.isMaxEqualMin(restriction) :
                    break
                restrictionList.append(restriction)
                newRestriction = DateRestriction(True)
                month = restriction._minDate.month + 1
                year = restriction._minDate.year
                if month > 12 :
                    month = month%12
                    year += 1
                newRestriction._minDate = datetime(year,month, restriction._minDate.day,restriction._minDate.seconds, 0)
                newRestriction._maxDate = datetime(year,month, restriction._maxDate.day,restriction._maxDate.seconds, 0)
                restriction = newRestriction
                
        if self._type == "year" :
            restriction = DateRestriction(True)
            restriction._minDate = datetime(dateRange._minDate.year,self._minDate.month,self._minDate.day,self.minDate.seconds,0)
            restriction._maxDate = datetime(dateRange._minDate.year,self._minDate.month,self._maxDate.day,self.maxDate.seconds,0)
            while True :
                if dateRange.isMaxSmallerMin(restriction) or dateRange.isMaxEqualMin(restriction) :
                    break
                restrictionList.append(restriction)
                newRestriction = DateRestriction(True)
                newRestriction._minDate = datetime(restriction._minDate.year+1,restriction._minDate.month, restriction._minDate.day,restriction._minDate.seconds, 0)
                newRestriction._maxDate = datetime(restriction._maxDate.year+1,restriction._maxDate.month, restriction._maxDate.day,restriction._maxDate.seconds, 0)
                restriction = newRestriction
        
        return restrictionList
        
    def movedForward(self, dateRange):
        if type(dataRange) != negotiations.DateRange :
            return None
        newRestriction = DateRestriction()
        scope = dateRange.getMax() - dateRange.getMin()
        newRestriction._minDate = self._minDate + scope
        newRestriction._maxDate = self._maxDate + scope
        return newRestriction
        
    
#-----------------------------------------------------------------------------------        
    
class DateSolution(DateRange, Solution):
    """
        Inherits from class DateRange
        Implements interfase Solution
    """
    def __init__(self, startRange, scopeRange):
        DateRange(startRange, scopeRange)

    def movedForward(self, dateRange):
        if type(dataRange) != negotiations.DateRange :
            return None
        newSolution = DateSolution()
        scope = dateRange.getMax() - dateRange.getMin()
        newSolution._minDate = self._minDate + scope
        newSolution._maxDate = self._maxDate + scope
        return newSolution
        