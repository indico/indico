# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.dialects.postgresql import JSON
from werkzeug.utils import cached_property

from indico.core.db import db
from indico.core.errors import IndicoError
from indico.util.decorators import cached_classproperty
from indico.util.string import return_ascii
from MaKaC.errors import MaKaCError

# TODO: remove this whole thing once all linked objects are in SQL


class UserLink(db.Model):
    __tablename__ = 'links'
    __table_args__ = (db.Index(None, 'user_id', 'type', 'role'),
                      {'schema': 'users'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    type = db.Column(
        db.String,
        nullable=False
    )
    role = db.Column(
        db.String,
        nullable=False
    )
    data = db.Column(
        JSON,
        nullable=False
    )
    # relationship backrefs:
    # - user (User.linked_objects)

    @return_ascii
    def __repr__(self):
        return '<UserLink({}, {}, {}, {})>'.format(self.id, self.user_id, self.type, self.role, self.data)

    @cached_property
    def object(self):
        """Retrieves the linked object"""
        from MaKaC.webinterface.locators import WebLocator

        mapping = {
            'category': 'setCategory',
            'conference': 'setConference',
            'session': 'setSession',
            'contribution': 'setContribution',
            'track': 'setTrack',
            'resource': 'setResource',
            'abstract': 'setAbstract',
            'registration': 'setRegistrant',
        }

        try:
            loc = WebLocator()
            getattr(loc, mapping[self.type])(self.data['locator'])
            return loc.getObject()
        except (IndicoError, MaKaCError):
            return None

    @classmethod
    def get_links(cls, user, type_, role):
        return {x.object for x in user.linked_objects.filter_by(type=type_, role=role) if x.object is not None}

    @classmethod
    def get_linked_roles(cls, user, type_):
        query = (db.session
                 .query(db.distinct(UserLink.role))
                 .with_parent(user, 'linked_objects')
                 .filter_by(type=type_))
        return {x[0] for x in query}

    @classmethod
    def create_link(cls, user, obj, role, type_=None):
        if type_ is None:
            type_ = cls._get_type(obj, role)
        data = cls._get_link_data(obj, type_)
        if data['locator']:
            link = cls(type=type_, role=role, data=data)
            user.linked_objects.append(link)
            return link

    @classmethod
    def remove_link(cls, user, obj, role):
        removed = set()
        type_ = cls._get_type(obj, role)
        for link in user.linked_objects.filter_by(type=type_, role=role).all():
            if link.object == obj:
                user.linked_objects.remove(link)
                removed.add(link)
        return removed

    @classmethod
    def _get_type(cls, obj, role=None):
        for type_, data in cls._link_map.iteritems():
            if isinstance(obj, data['cls']):
                if role is not None and role not in data['roles']:
                    raise ValueError('invalid role {} for {}'.format(role, type_))
                return type_
        raise ValueError('invalid object type: {}'.format(type(obj).__name__))

    @classmethod
    def _get_link_data(cls, obj, type_):
        return {'type': type_,
                'locator': dict(obj.getLocator())}

    @cached_classproperty
    @classmethod
    def _link_map(cls):
        import MaKaC.conference
        import MaKaC.registration
        import MaKaC.review
        import MaKaC.user
        return {
            'category': {'cls': MaKaC.conference.Category,
                         'roles': {'access', 'creator', 'manager'}},
            'conference': {'cls': MaKaC.conference.Conference,
                           'roles': {'abstractSubmitter', 'access', 'chair', 'creator', 'editor', 'manager',
                                     'paperReviewManager', 'participant', 'referee', 'registrar', 'reviewer'}},
            'session': {'cls': MaKaC.conference.Session,
                        'roles': {'access', 'coordinator', 'manager'}},
            'contribution': {'cls': MaKaC.conference.Contribution,
                             'roles': {'access', 'editor', 'manager', 'referee', 'reviewer', 'submission'}},
            'track': {'cls': MaKaC.conference.Track,
                      'roles': {'coordinator'}},
            'resource': {'cls': MaKaC.conference.Resource,
                         'roles': {'access'}},
            'abstract': {'cls': MaKaC.review.Abstract,
                         'roles': {'submitter'}},
            'registration': {'cls': MaKaC.registration.Registrant,
                             'roles': {'registrant'}},
        }
