# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.web.http_api.metadata.json import JSONSerializer


class JSONPSerializer(JSONSerializer):
    """Add prefix."""

    _mime = 'application/javascript'

    def _execute(self, results):
        return "// fetched from Indico\n%s(%s);" % \
               (self._query_params.get('jsonp', 'read'),
                super(JSONPSerializer, self)._execute(results))
