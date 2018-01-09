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

from __future__ import unicode_literals

from uuid import uuid4

from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.urls import url_parse

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.oauth import logger
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum


SCOPES = {'read:user': _("User information (read only)"),
          'read:legacy_api': _('Legacy API (read only)'),
          'write:legacy_api': _('Legacy API (write only)'),
          'registrants': _('Event registrants')}


class SystemAppType(int, IndicoEnum):
    none = 0
    checkin = 1
    flower = 2

    __enforced_data__ = {
        checkin: {'default_scopes': {'registrants'},
                  'redirect_uris': ['http://localhost'],
                  'is_enabled': True},
        flower: {'default_scopes': {'read:user'},
                 'is_enabled': True}
    }

    __default_data__ = {
        checkin: {'is_trusted': True,
                  'name': 'Checkin App',
                  'description': 'The checkin app for mobile devices allows scanning ticket QR codes and '
                                 'checking-in event participants.'},
        flower: {'is_trusted': True,
                 'name': 'Flower',
                 'description': 'Flower allows monitoring Celery tasks. If flower is installed, this app is used to '
                                'restrict access to Indico administrators.'}
    }

    @property
    def enforced_data(self):
        return self.__enforced_data__.get(self, {})

    @property
    def default_data(self):
        return dict(self.__default_data__.get(self, {}), **self.enforced_data)


class OAuthApplication(db.Model):
    """OAuth applications registered in Indico"""

    __tablename__ = 'applications'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_applications_name_lower', db.func.lower(cls.name), unique=True),
                db.Index(None, cls.system_app_type, unique=True,
                         postgresql_where=db.text('system_app_type != {}'.format(SystemAppType.none.value))),
                {'schema': 'oauth'})

    #: the unique id of the application
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: human readable name
    name = db.Column(
        db.String,
        nullable=False
    )
    #: human readable description
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: the OAuth client_id
    client_id = db.Column(
        UUID,
        unique=True,
        nullable=False,
        default=lambda: unicode(uuid4())
    )
    #: the OAuth client_secret
    client_secret = db.Column(
        UUID,
        nullable=False,
        default=lambda: unicode(uuid4())
    )
    #: the OAuth default scopes the application may request access to
    default_scopes = db.Column(
        ARRAY(db.String),
        nullable=False
    )
    #: the OAuth absolute URIs that a application may use to redirect to after authorization
    redirect_uris = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    #: whether the application is enabled or disabled
    is_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: whether the application can access user data without asking for permission
    is_trusted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: the type of system app (if any). system apps cannot be deleted
    system_app_type = db.Column(
        PyIntEnum(SystemAppType),
        nullable=False,
        default=SystemAppType.none
    )

    # relationship backrefs:
    # - tokens (OAuthToken.application)

    @property
    def client_type(self):
        return 'public'

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0] if self.redirect_uris else None

    @property
    def locator(self):
        return {'id': self.id}

    @return_ascii
    def __repr__(self):  # pragma: no cover
        return '<OAuthApplication({}, {}, {})>'.format(self.id, self.name, self.client_id)

    def reset_client_secret(self):
        self.client_secret = unicode(uuid4())
        logger.info("Client secret for %s has been reset.", self)

    def validate_redirect_uri(self, redirect_uri):
        """Called by flask-oauthlib to validate the redirect_uri.

        Uses a logic similar to the one at GitHub, i.e. protocol and
        host/port must match exactly and if there is a path in the
        whitelisted URL, the path of the redirect_uri must start with
        that path.
        """
        uri_data = url_parse(redirect_uri)
        for valid_uri_data in map(url_parse, self.redirect_uris):
            if (uri_data.scheme == valid_uri_data.scheme and uri_data.netloc == valid_uri_data.netloc and
                    uri_data.path.startswith(valid_uri_data.path)):
                return True
        return False
