# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

import os
from indico.util.contextManager import ContextManager
from indico.util.redis.scripts import LazyScriptLoader
from indico.util.proxy import LocalProxy
from MaKaC.common import Config

__all__ = ['scripts', 'client', 'pipeline', 'set_redis_client']

_client = None


def set_redis_client(client):
    """Set/replace the current redis client with a custom one.

    This is useful e.g. during testing when a separate redis instance than the
    one in indico.conf should be used.
    """
    global _client
    _client = client
    scripts.flush()


def _get_redis_client():
    global _client
    if _client is not None:
        return _client
    url = Config.getInstance().getRedisConnectionURL()
    if url:
        import redis
        _client = redis.StrictRedis.from_url(url)
    return _client


def _get_redis_pipeline():
    rh = ContextManager.get('currentRH', None)
    if not rh:
        # If you are reading this because you tried to use this e.g. in a migration script
        # or somewhere else outside a RH context: Use `with client.pipeline() as pipe:` and
        # execute it on your own. The sole reason why this pipeline accessor exists is that
        # the pipeline can be properly executed/discarded in case of a DB commit/conflict.
        raise Exception('Cannot get Redis pipeline outside a request')
    if rh._redisPipeline:
        return rh._redisPipeline
    rh._redisPipeline = client.pipeline(transaction=False)
    return rh._redisPipeline


# The client is proxied since we do not want to actually get it until we need it.
# This has the advantage of allowing e.g. tests to set their own redis client.
client = LocalProxy(_get_redis_client)
# The pipeline is stored per request handler and only available if we actually have one
pipeline = LocalProxy(_get_redis_pipeline)
script_dir = os.path.join(os.path.dirname(__file__), 'lua_scripts')
scripts = LazyScriptLoader(client, script_dir)