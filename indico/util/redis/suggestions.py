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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.
from collections import OrderedDict

from indico.util.redis import scripts
from indico.util.redis import client as redis_client
from indico.util.redis import write_client as redis_write_client


def schedule_check(avatar, client=None):
    if client is None:
        client = redis_write_client
    client.sadd('suggestions/scheduled_checks', avatar.getId())


def unschedule_check(avatar_id, client=None):
    if client is None:
        client = redis_write_client
    client.srem('suggestions/scheduled_checks', avatar_id)


def next_scheduled_check(client=None):
    """Returns an avatar id that is scheduled to be checked"""
    if client is None:
        client = redis_client
    return client.srandmember('suggestions/scheduled_checks')


def suggest(avatar, what, id, score, client=None):
    if client is None:
        client = redis_write_client
    scripts.suggestions_suggest(avatar.getId(), what, id, score, client=client)


def unsuggest(avatar, what, id, ignore=False, client=None):
    if client is None:
        client = redis_write_client
    client.zrem('suggestions/suggested:%s:%s' % (avatar.getId(), what), id)
    if ignore:
        client.sadd('suggestions/ignored:%s:%s' % (avatar.getId(), what), id)


def unignore(avatar, what, id, client=None):
    if client is None:
        client = redis_write_client
    client.srem('suggestions/ignored:%s:%s' % (avatar.getId(), what), id)


def get_suggestions(avatar, what, client=None):
    if client is None:
        client = redis_client
    key = 'suggestions/suggested:%s:%s' % (avatar.getId(), what)
    return OrderedDict(client.zrevrangebyscore(key, '+inf', '-inf', withscores=True))


def merge_avatars(destination, source, client=None):
    if client is None:
        client = redis_write_client
    scripts.suggestions_merge_avatars(destination.getId(), source.getId(), client=client)


def delete_avatar(avatar, client=None):
    if client is None:
        client = redis_write_client
    client.srem('suggestions/scheduled_checks', avatar.getId())
    client.delete('suggestions/suggested:%s:category' % avatar.getId())
    client.delete('suggestions/ignored:%s:category' % avatar.getId())
