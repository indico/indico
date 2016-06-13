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

from .core import db
from .custom import *


def _patch_sa_cte_fix():
    import pkg_resources
    sa_dist = pkg_resources.get_distribution('sqlalchemy')
    if sa_dist.parsed_version > pkg_resources.parse_version('1.0.12'):
        raise Exception('Remove this monkeypatch; SQLAlchemy contains the CTE fix')
    from sqlalchemy.sql.selectable import CTE
    from sqlalchemy.sql.elements import _clone

    def _copy_internals(self, clone=_clone, **kw):
        super(CTE, self)._copy_internals(clone, **kw)
        if self._cte_alias is not None:
            self._cte_alias = self
        self._restates = frozenset([
            clone(elem, **kw) for elem in self._restates
        ])

    CTE._copy_internals = _copy_internals


_patch_sa_cte_fix()
