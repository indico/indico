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

from MaKaC.webinterface import wcomponents
import os
import MaKaC.common.Configuration as Configuration

from MaKaC.plugins.EPayment import payPal

class WTemplated(wcomponents.WTemplated):
    
    def _setTPLFile(self):
        """Sets the TPL (template) file for the object. It will try to get
            from the configuration if there's a special TPL file for it and
            if not it will look for a file called as the class name+".tpl"
            in the configured TPL directory.
        """
        cfg = Configuration.Config.getInstance()
        
        dir = os.path.join(payPal.__path__[0], "tpls")
        file = cfg.getTPLFile( self.tplId )
        if file == "":
            file = "%s.tpl"%self.tplId
        self.tplFile = os.path.join(dir, file)
        
        hfile = self._getSpecificTPL(os.path.join(dir,'chelp'),
                                     self.tplId,
                                     extension='wohl')
    
        self.helpFile = os.path.join(dir,'chelp',hfile)