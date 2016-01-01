# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from markupsafe import escape


# XXX: do not use this in new code! use a plain dict instead!
class Locator(dict):
    """Helper class specialising UserDict (dictionary) which contains a locator
        for an object. This is needed due to the id schema chosen and to the
        web needs: it is a relative id schema (a suboject is given an id which
        is unique only inside its superobject) and we need to uniquely identify
        some objects on the web pages so it is needed to handle the "locator"
        which can be made up of various ids. This class will contain the locator
        and provide methods for using it on the web pages so it's use is
        transparent for client.
    """

    def getWebForm(self):
        """Returns the current locator for being used in web pages forms
            (hidden parameters)
        """
        l = []
        for item, val in self.iteritems():
            if isinstance(val, list):
                for v in val:
                    l.append('<input type="hidden" name="{}" value="{}">'.format(item, escape(v)))
            else:
                l.append('<input type="hidden" name="{}" value="{}">'.format(item, escape(val)))
        return "\n".join(l)
