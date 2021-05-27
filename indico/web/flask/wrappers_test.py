# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import request


@pytest.mark.parametrize(('raw_ip', 'ip'), (
    ('::ffff:127.0.0.1', '127.0.0.1'),
    ('127.0.0.1', '127.0.0.1'),
    ('2001:db8::d34d:b33f', '2001:db8::d34d:b33f'),
))
def test_request_remote_addr(app, raw_ip, ip):
    with app.test_request_context(environ_base={'REMOTE_ADDR': raw_ip}):
        assert request.remote_addr == ip
