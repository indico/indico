# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.util.mimetypes import register_custom_mimetypes


__version__ = '2.1.5'

register_custom_mimetypes()


# monkeypatch for https://github.com/wtforms/wtforms/issues/373
def _patch_wtforms_sqlalchemy():
    from wtforms.ext.sqlalchemy import fields
    from sqlalchemy.orm.util import identity_key

    def get_pk_from_identity(obj):
        key = identity_key(instance=obj)[1]
        return u':'.join(map(unicode, key))

    fields.get_pk_from_identity = get_pk_from_identity


try:
    _patch_wtforms_sqlalchemy()
except ImportError as exc:
    # pip seems to run this sometimes while uninstalling an old sqlalchemy version
    print 'Could not monkeypatch wtforms', exc
finally:
    del _patch_wtforms_sqlalchemy
