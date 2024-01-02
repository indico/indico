# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import simplejson

from indico.util.json import IndicoJSONEncoder
from indico.web.http_api.metadata.serializer import Serializer


class JSONSerializer(Serializer):
    """Basically direct translation from the fossil."""

    _mime = 'application/json'

    def _execute(self, fossil):
        indent = ' ' * 4 if self.pretty else None
        return simplejson.dumps(fossil, cls=IndicoJSONEncoder, indent=indent).replace('/', '\\/')


Serializer.register('json', JSONSerializer)
