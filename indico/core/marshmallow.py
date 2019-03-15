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

from __future__ import absolute_import, unicode_literals

from inspect import getmro

from flask_marshmallow import Marshmallow
from flask_marshmallow.sqla import SchemaOpts
from marshmallow import fields, post_dump, pre_load
from marshmallow_enum import EnumField
from marshmallow_sqlalchemy import ModelConverter
from marshmallow_sqlalchemy import ModelSchema as MSQLAModelSchema
from sqlalchemy.orm import ColumnProperty

from indico.core import signals
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime


mm = Marshmallow()


class IndicoModelConverter(ModelConverter):
    SQLA_TYPE_MAPPING = ModelConverter.SQLA_TYPE_MAPPING.copy()
    SQLA_TYPE_MAPPING.update({
        UTCDateTime: fields.DateTime,
        PyIntEnum: EnumField
    })

    def _get_field_kwargs_for_property(self, prop):
        kwargs = super(IndicoModelConverter, self)._get_field_kwargs_for_property(prop)
        if isinstance(prop, ColumnProperty) and hasattr(prop.columns[0].type, 'marshmallow_get_field_kwargs'):
            kwargs.update(prop.columns[0].type.marshmallow_get_field_kwargs())
        return kwargs

    def fields_for_model(self, model, *args, **kwargs):
        # Look up aliases on all classes in the inheritance chain of
        # the model so mixins can define their own aliases if needed.
        def _get_from_mro(attr, key, default=None, _mro=getmro(model)):
            for cls in _mro:
                try:
                    return getattr(cls, attr, {})[key]
                except (TypeError, KeyError, AttributeError):
                    continue
            return default

        # XXX: To allow renaming/aliasing of fields we need to let mm-sqlalchemy
        # generate all fields from the models and leave it up to mm itself to
        # exclude fields we don't care about
        kwargs['fields'] = ()
        fields = super(IndicoModelConverter, self).fields_for_model(model, *args, **kwargs)
        for key, field in fields.items():
            new_key = _get_from_mro('marshmallow_aliases', key)
            if new_key:
                del fields[key]
                fields[new_key] = field
                if field.attribute is None:
                    field.attribute = key
        return fields


class IndicoSchema(mm.Schema):
    @post_dump(pass_many=True, pass_original=True)
    def _call_post_dump_signal(self, data, many, orig):
        data_list = data if many else [data]
        orig_list = orig if many else [orig]
        signals.plugin.schema_post_dump.send(type(self), data=data_list, orig=orig_list, many=many)
        return data_list if many else data_list[0]

    @pre_load
    def _call_pre_load_signal(self, data):
        signals.plugin.schema_pre_load.send(type(self), data=data)
        return data


class _IndicoModelSchemaOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        super(_IndicoModelSchemaOpts, self).__init__(meta, **kwargs)
        self.model_converter = getattr(meta, 'model_converter', IndicoModelConverter)


class IndicoModelSchema(MSQLAModelSchema, IndicoSchema):
    OPTIONS_CLASS = _IndicoModelSchemaOpts


mm.Schema = IndicoSchema
mm.ModelSchema = IndicoModelSchema
