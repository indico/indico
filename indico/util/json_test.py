# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

from flask import jsonify


def test_jsonify_no_args():
    assert json.loads(jsonify().data) == {}
