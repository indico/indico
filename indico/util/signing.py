# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import current_app
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer
from werkzeug.local import LocalProxy


#: An *itsdangerous*-based serializer that can be used to pass small
#: amounts of data through untrusted channels such as a verification
#: email. It includes the generation time so validity can be limited.
#: :type: :class:`~itsdangerous.URLSafeTimedSerializer`
secure_serializer: URLSafeTimedSerializer = LocalProxy(
    lambda: URLSafeTimedSerializer(current_app.config['SECRET_KEY'], b'indico')
)

#: An *itsdangerous*-based serializer that can be used to pass small
#: amounts of data through untrusted channels such as URLs.
#: :type: :class:`~itsdangerous.URLSafeSerializer`
static_secure_serializer: URLSafeSerializer = LocalProxy(
    lambda: URLSafeSerializer(current_app.config['SECRET_KEY'], b'indico')
)
