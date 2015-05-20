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

from celery.schedules import crontab

from indico.core.celery import celery
from indico.modules.categories import logger
from indico.modules.users import User
from indico.util.suggestions import get_category_scores
from indico.util.redis import write_client as redis_write_client
from indico.util.redis.suggestions import next_scheduled_check, suggest, unschedule_check


# Minimum score for a category to be suggested
SUGGESTION_MIN_SCORE = 0.25


@celery.periodic_task(name='update_category_suggestions', run_every=crontab(minute='0', hour='7'))
def update_category_suggestions():
    if not redis_write_client:
        return
    while True:
        user_id = next_scheduled_check()
        if user_id is None:
            break
        user = User.get(int(user_id))
        if user:
            for category, score in get_category_scores(user).iteritems():
                if score < SUGGESTION_MIN_SCORE:
                    continue
                logger.debug('Suggesting {} with score {:.03} for {}'.format(category, score, user))
                suggest(user, 'category', category.getId(), score)
        unschedule_check(user_id)
