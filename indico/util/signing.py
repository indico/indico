# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from werkzeug.local import LocalProxy


#: An *itsdangerous*-based serializer that can be used to pass small
#: amounts of data through untrusted channels such as a verification
#: email.
#: :type: :class:`~itsdangerous.URLSafeTimedSerializer`
secure_serializer = LocalProxy(lambda: URLSafeTimedSerializer(current_app.config['SECRET_KEY'], b'indico'))
