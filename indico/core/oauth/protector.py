# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import flask
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc6750.validator import BearerTokenValidator
from flask import after_this_request, jsonify
from werkzeug.exceptions import HTTPException

from indico.core.db import db
from indico.core.oauth.models.applications import SystemAppType
from indico.core.oauth.models.tokens import OAuthToken
from indico.core.oauth.util import query_token
from indico.util.date_time import now_utc


class IndicoAuthlibHTTPError(HTTPException):
    def __init__(self, status_code, payload, headers):
        super().__init__(payload.get('error_description') or payload['error'])
        resp = jsonify(payload)
        resp.headers.update(headers)
        resp.status_code = status_code
        self.response = resp


class IndicoResourceProtector(ResourceProtector):
    def raise_error_response(self, error):
        payload = dict(error.get_body())
        headers = error.get_headers()
        raise IndicoAuthlibHTTPError(error.status_code, payload, headers)

    def parse_request_authorization(self, request):
        access_token_querystring = flask.request.args.get('access_token')
        if access_token_querystring and not request.headers.get('Authorization', '').lower().startswith('bearer '):
            validator = self.get_token_validator('legacy_qs')
            return validator, access_token_querystring
        return super().parse_request_authorization(request)


class IndicoBearerTokenValidator(BearerTokenValidator):
    def authenticate_token(self, token_string):
        return query_token(token_string)

    def validate_token(self, token, scopes):
        super().validate_token(token, scopes)

        # if we get here, the token is valid so we can mark it as used at the end of the request

        # XXX: should we wait or do it just now? even if the request failed for some reason, the
        # token could be considered used, since it was valid and most likely used by a client who
        # expected to do something with it...

        token_id = token.id  # avoid DetachedInstanceError in the callback

        @after_this_request
        def _update_last_use(response):
            with db.tmp_session() as sess:
                # do not modify `token` directly, it's attached to a different session!
                sess.query(OAuthToken).filter_by(id=token_id).update({OAuthToken.last_used_dt: now_utc()})
                sess.commit()
            return response


class IndicoLegacyQueryStringBearerTokenValidator(IndicoBearerTokenValidator):
    TOKEN_TYPE = 'legacy_qs'

    def authenticate_token(self, token_string):
        token = super().authenticate_token(token_string)
        if token and token.application.system_app_type == SystemAppType.checkin:
            # Only the checkin app is allowed to pass tokens insecurely via query string
            return token
