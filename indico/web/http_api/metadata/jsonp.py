# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.web.http_api.metadata.json import JSONSerializer


class JSONPSerializer(JSONSerializer):
    """Add prefix."""

    _mime = 'application/javascript'

    def _execute(self, results):
        func = self._query_params.get('jsonp', 'read')
        res = super()._execute(results)
        return f'// fetched from Indico\n{func}({res});'
