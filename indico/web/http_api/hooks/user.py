# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

# python stdlib imports
import itertools

# indico imports
from indico.util.redis import client as redis_client
import indico.util.redis.avatar_links as avatar_links

from indico.web.http_api.fossils import IBasicConferenceMetadataFossil
from indico.web.http_api.responses import HTTPAPIError
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.hooks.base import HTTPAPIHook, IteratedDataFetcher

# indico legacy imports
from MaKaC.common.indexes import IndexesHolder
from MaKaC.conference import ConferenceHolder
from MaKaC.user import AvatarHolder


@HTTPAPIHook.register
class UserInfoHook(HTTPAPIHook):
    TYPES = ('user',)
    RE = r'(?P<user_id>[\d]+)'

    def _getParams(self):
        super(UserInfoHook, self)._getParams()
        self._user_id = self._pathParams['user_id']

    def export_user(self, aw):
        requested_user = AvatarHolder().getById(self._user_id)
        user = aw.getUser()
        if not requested_user:
            raise HTTPAPIError('Requested user not found', 404)
        if user:
            if requested_user.canUserModify(user):
                return [requested_user.fossilize()]
            raise HTTPAPIError('You do not have access to that info', 403)
        raise HTTPAPIError('You need to be logged in', 403)


@HTTPAPIHook.register
class UserEventHook(HTTPAPIHook):
    TYPES = ('user',)
    RE = r'(?P<what>linked_events|categ_events)'
    DEFAULT_DETAIL = 'basic_events'
    GUEST_ALLOWED = False

    def _getParams(self):
        super(UserEventHook, self)._getParams()
        self._what = self._pathParams['what']
        self._avatar = None
        # User-specified avatar
        userId = get_query_parameter(self._queryParams, ['uid', 'userid'])
        if userId is not None:
            self._avatar = AvatarHolder().getById(userId)
            if not self._avatar:
                raise HTTPAPIError('Avatar does not exist')

    def _getMethodName(self):
        return self.PREFIX + '_' + self._what

    def _checkProtection(self, aw):
        if not self._avatar:
            # No avatar specified => use self. No need to check any permissinos.
            self._avatar = aw.getUser()
            return
        elif not self._avatar.canUserModify(aw.getUser()):
            raise HTTPAPIError('Access denied', 403)

    def export_linked_events(self, aw):
        if not redis_client:
            raise HTTPAPIError('This API is only available when using Redis')
        self._checkProtection(aw)
        links = avatar_links.get_links(self._avatar, self._fromDT, self._toDT)
        return UserRelatedEventFetcher(aw, self, links).events(links.keys())

    def export_categ_events(self, aw):
        self._checkProtection(aw)
        catIds = [item['categ'].getId() for item in self._avatar.getRelatedCategories().itervalues()]
        return UserCategoryEventFetcher(aw, self).category_events(catIds)


class UserCategoryEventFetcher(IteratedDataFetcher):

    DETAIL_INTERFACES = {
        'basic_events': IBasicConferenceMetadataFossil
    }

    def category_events(self, catIds):
        idx = IndexesHolder().getById('categoryDateAll')
        iters = itertools.chain(*(idx.iterateObjectsIn(catId, self._fromDT, self._toDT) for catId in catIds))
        return self._process(iters)


class UserRelatedEventFetcher(IteratedDataFetcher):

    DETAIL_INTERFACES = {
        'basic_events': IBasicConferenceMetadataFossil
    }

    def __init__(self, aw, hook, roles):
        super(UserRelatedEventFetcher, self).__init__(aw, hook)
        self._roles = roles

    def _postprocess(self, obj, fossil, iface):
        fossil['roles'] = list(self._roles[obj.getId()])
        return fossil

    def events(self, eventIds):
        ch = ConferenceHolder()

        def _iterate_objs(objIds):
            for objId in objIds:
                obj = ch.getById(objId, True)
                if obj is not None:
                    yield obj

        return self._process(_iterate_objs(eventIds))
