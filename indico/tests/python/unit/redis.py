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
from __future__ import absolute_import

import random
import string
import subprocess
import time

import redis

from indico.tests.python.unit.util import IndicoTestFeature
from indico.util.redis import set_redis_client


class Redis_Feature(IndicoTestFeature):
    """
    Starts/stops a redis instance
    """

    _requires = []

    def start(self, obj):
        super(Redis_Feature, self).start(obj)
        # Create redis server
        redis_password = ''.join(random.choice(string.letters) for i in xrange(10))
        self._redis_process = subprocess.Popen(['/usr/sbin/redis-server',
                                                '--daemonize', 'no',
                                                '--port', '56379',
                                                '--save', '',
                                                '--requirepass', redis_password,
                                                '--maxclients', '100',
                                                '--loglevel', 'warning',
                                                '--logfile', '/dev/null'])

        # Redis takes some time to start up. Let's do some retries before failing.
        for i in xrange(10):
            obj._redis = redis.StrictRedis(host='127.0.0.1', port=56379, password=redis_password)
            try:
                obj._redis.ping()
            except redis.RedisError, e:
                if i < 9:
                    time.sleep(0.001)
                    continue
                print 'Could not connect to redis (%s); terminating server' % e
                self._redis_process.terminate()
                raise

        set_redis_client(obj._redis)

    def _context_redis_pipeline(self, transaction=False):
        pipe = self._redis.pipeline(transaction=transaction)
        yield pipe
        self._redis_pipeline_result = pipe.execute()

    def destroy(self, obj):
        self._redis_process.kill()
