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

from MaKaC.user import AvatarHolder
from indico.modules.scheduler.tasks.periodic import PeriodicTask
from indico.util.suggestions import get_category_scores
from indico.util.redis import write_client as redis_write_client
import indico.util.redis.suggestions as redis_suggestions

# Minimum score for a category to be suggested
SUGGESTION_MIN_SCORE = 0.25


class CategorySuggestionTask(PeriodicTask):
    def _update_suggestions(self, avatar):
        for category, score in get_category_scores(avatar).iteritems():
            if score < SUGGESTION_MIN_SCORE:
                continue
            #print 'Suggest category for %r: %r (%.03f)' % (avatar, category, score)
            redis_suggestions.suggest(avatar, 'category', category.getId(), score)

    def run(self):
        if not redis_write_client:
            return
        while True:
            avatar_id = redis_suggestions.next_scheduled_check()
            if avatar_id is None:
                break
            avatar = AvatarHolder().getById(avatar_id)
            if avatar:
                self._update_suggestions(avatar)
            redis_suggestions.unschedule_check(avatar_id)
