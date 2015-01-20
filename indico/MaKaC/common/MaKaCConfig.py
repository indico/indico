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

## WARNING: THE FOLLOWING LINE WILL BE OVERWRITTEN AT INSTALLATION TIME
indico_conf = "" # path to indico.conf
##

import os

if indico_conf == '': # we may be in development mode or in installation mode
    indico_conf = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'etc', 'indico.conf')
    if not os.path.exists(indico_conf):
        # eggmode
        indico_conf = os.path.join(os.path.dirname(__file__), '..', '..', 'etc', 'indico.conf.sample')
    if not os.path.exists(indico_conf):
        indico_conf = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'etc', 'indico.conf.sample')

execfile(indico_conf)
