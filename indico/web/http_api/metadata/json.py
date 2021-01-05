# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.util import json
from indico.web.http_api.metadata.serializer import Serializer


class JSONSerializer(Serializer):
    """Basically direct translation from the fossil."""

    _mime = 'application/json'

    def _execute(self, fossil):
        return json.dumps(fossil, pretty=self.pretty)


Serializer.register('json', JSONSerializer)
