# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from datetime import timedelta

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.config import Config
from indico.core.db import db
from indico.modules.categories import logger, Category
from indico.modules.users import User, UserSetting
from indico.modules.users.models.suggestions import SuggestedCategory
from indico.modules.users.util import get_related_categories
from indico.util.date_time import now_utc
from indico.util.suggestions import get_category_scores


# Minimum score for a category to be suggested
SUGGESTION_MIN_SCORE = 0.25


@celery.periodic_task(name='category_suggestions', run_every=crontab(minute='0', hour='7'))
def category_suggestions():
    users = (User.query
             .filter(~User.is_deleted,
                     User._all_settings.any(db.and_(UserSetting.module == 'users',
                                                    UserSetting.name == 'suggest_categories',
                                                    db.cast(UserSetting.value, db.String) == 'true'))))
    for user in users:
        existing = {x.category: x for x in user.suggested_categories}
        related = set(get_related_categories(user, detailed=False))
        for category, score in get_category_scores(user).iteritems():
            if score < SUGGESTION_MIN_SCORE:
                continue
            if (category in related or category.is_deleted or category.suggestions_disabled or
                    any(p.suggestions_disabled for p in category.parent_chain_query)):
                continue
            logger.debug('Suggesting %s with score %.03f for %s', category, score, user)
            suggestion = existing.get(category) or SuggestedCategory(category=category, user=user)
            suggestion.score = score
        user.settings.set('suggest_categories', False)
        db.session.commit()


@celery.periodic_task(name='category_cleanup', run_every=crontab(minute='0', hour='5'))
def category_cleanup():
    from indico.modules.events import Event
    cfg = Config.getInstance()
    janitor_user = User.get_one(cfg.getJanitorUserId())

    logger.debug("Checking whether any categories should be cleaned up")
    for categ_id, days in cfg.getCategoryCleanup().iteritems():
        try:
            category = Category.get(int(categ_id), is_deleted=False)
        except KeyError:
            logger.warning("Category %s does not exist!", categ_id)
            continue

        now = now_utc()
        to_delete = Event.query.with_parent(category).filter(Event.created_dt < (now - timedelta(days=days))).all()
        if not to_delete:
            continue

        logger.info("Category %s: %s events were created more than %s days ago and will be deleted", categ_id,
                    len(to_delete), days)
        for i, event in enumerate(to_delete, 1):
            logger.info("Deleting %s", event)
            event.delete('Cleaning up category', janitor_user)
            if i % 100 == 0:
                db.session.commit()
        db.session.commit()
