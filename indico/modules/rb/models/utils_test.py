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

import pytest

from indico.core.errors import IndicoError
from indico.modules.rb.models.utils import unimplemented


@pytest.mark.parametrize(('raised', 'caught', 'message'), (
    (RuntimeError, IndicoError, 'foo'),
    (Exception,    Exception,   'bar'),
    (ValueError,   ValueError,  'bar')
))
def test_unimplemented(raised, caught, message):
    @unimplemented(RuntimeError, message='foo')
    def _func():
        raise raised('bar')

    exc_info = pytest.raises(caught, _func)
    assert exc_info.value.message == message
