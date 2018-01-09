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

from collections import OrderedDict
from datetime import timedelta

from pytz import timezone
from sqlalchemy.orm import load_only
from sqlalchemy.orm.attributes import set_committed_value

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.attachments import Attachment
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.categories import upcoming_events_settings
from indico.modules.events import Event
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.sessions import Session
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.caching import memoize_redis
from indico.util.date_time import now_utc
from indico.util.i18n import _, ngettext
from indico.util.struct.iterables import materialize_iterable


def get_events_by_year(category_id=None):
    """Get the number of events for each year.

    :param category_id: The category ID to get statistics for. Events
                        from subcategories are also included.
    :return: An `OrderedDict` mapping years to event counts.
    """
    category_filter = Event.category_chain_overlaps(category_id) if category_id else True
    query = (db.session
             .query(db.cast(db.extract('year', Event.start_dt), db.Integer).label('year'),
                    db.func.count())
             .filter(~Event.is_deleted,
                     category_filter)
             .order_by('year')
             .group_by('year'))
    return OrderedDict(query)


def get_contribs_by_year(category_id=None):
    """Get the number of contributions for each year.

    :param category_id: The category ID to get statistics for.
                        Contributions from subcategories are also
                        included.
    :return: An `OrderedDict` mapping years to contribution counts.
    """
    category_filter = Event.category_chain_overlaps(category_id) if category_id else True
    query = (db.session
             .query(db.cast(db.extract('year', TimetableEntry.start_dt), db.Integer).label('year'),
                    db.func.count())
             .join(TimetableEntry.event)
             .filter(TimetableEntry.type == TimetableEntryType.CONTRIBUTION,
                     ~Event.is_deleted,
                     category_filter)
             .order_by('year')
             .group_by('year'))
    return OrderedDict(query)


def get_attachment_count(category_id=None):
    """Get the number of attachments in events in a category.

    :param category_id: The category ID to get statistics for.
                        Attachments from subcategories are also
                        included.
    :return: The number of attachments
    """
    category_filter = Event.category_chain_overlaps(category_id) if category_id else True
    subcontrib_contrib = db.aliased(Contribution)
    query = (db.session
             .query(db.func.count(Attachment.id))
             .join(Attachment.folder)
             .join(AttachmentFolder.event)
             .outerjoin(AttachmentFolder.session)
             .outerjoin(AttachmentFolder.contribution)
             .outerjoin(AttachmentFolder.subcontribution)
             .outerjoin(subcontrib_contrib, subcontrib_contrib.id == SubContribution.contribution_id)
             .filter(AttachmentFolder.link_type != LinkType.category,
                     ~Attachment.is_deleted,
                     ~AttachmentFolder.is_deleted,
                     ~Event.is_deleted,
                     # we have exactly one of those or none if the attachment is on the event itself
                     ~db.func.coalesce(Session.is_deleted, Contribution.is_deleted, SubContribution.is_deleted, False),
                     # in case of a subcontribution we also need to check that the contrib is not deleted
                     (subcontrib_contrib.is_deleted.is_(None) | ~subcontrib_contrib.is_deleted),
                     category_filter))
    return query.scalar()


@memoize_redis(86400)
def get_category_stats(category_id=None):
    """Get category statistics.

    This function is mainly a helper so we can get and cache
    all values at once and keep a last-update timestamp.

    :param category_id: The category ID to get statistics for.
                        Subcategories are also included.
    """
    return {'events_by_year': get_events_by_year(category_id),
            'contribs_by_year': get_contribs_by_year(category_id),
            'attachments': get_attachment_count(category_id),
            'updated': now_utc()}


@memoize_redis(3600)
@materialize_iterable()
def get_upcoming_events():
    """Get the global list of upcoming events"""
    from indico.modules.events import Event
    data = upcoming_events_settings.get_all()
    if not data['max_entries'] or not data['entries']:
        return
    tz = timezone(config.DEFAULT_TIMEZONE)
    now = now_utc(False).astimezone(tz)
    base_query = (Event.query
                  .filter(Event.effective_protection_mode == ProtectionMode.public,
                          ~Event.is_deleted,
                          Event.end_dt.astimezone(tz) > now)
                  .options(load_only('id', 'title', 'start_dt', 'end_dt')))
    queries = []
    cols = {'category': Event.category_id,
            'event': Event.id}
    for entry in data['entries']:
        delta = timedelta(days=entry['days'])
        query = (base_query
                 .filter(cols[entry['type']] == entry['id'])
                 .filter(db.cast(Event.start_dt.astimezone(tz), db.Date) > (now - delta).date())
                 .with_entities(Event, db.literal(entry['weight']).label('weight')))
        queries.append(query)

    query = (queries[0].union(*queries[1:])
             .order_by(db.desc('weight'), Event.start_dt, Event.title)
             .limit(data['max_entries']))
    for row in query:
        event = row[0]
        # we cache the result of the function and is_deleted is used in the repr
        # and having a broken repr on the cached objects would be ugly
        set_committed_value(event, 'is_deleted', False)
        yield event


def get_visibility_options(category_or_event, allow_invisible=True):
    """Return the visibility options available for the category or event."""
    if isinstance(category_or_event, Event):
        category = category_or_event.category
        event = category_or_event
    else:
        category = category_or_event
        event = None

    def _category_above_message(number):
        return ngettext('From the category above', 'From {} categories above', number).format(number)

    options = [(n + 1, ('{} \N{RIGHTWARDS ARROW} "{}"'.format(_category_above_message(n).format(n), title)))
               for n, title in enumerate(category.chain_titles[::-1])]
    if event is None:
        options[0] = (1, _("From this category only"))
    else:
        options[0] = (1, '{} \N{RIGHTWARDS ARROW} "{}"'.format(_("From the current category only"), category.title))
    options[-1] = ('', _("From everywhere"))

    if allow_invisible:
        options.insert(0, (0, _("Invisible")))

    # In case the current visibility is higher than the distance to the root category
    if category_or_event.visibility is not None and not any(category_or_event.visibility == x[0] for x in options):
        options.append((category_or_event.visibility,
                        '({} \N{RIGHTWARDS ARROW} {})'.format(_category_above_message(category_or_event.visibility),
                                                              _("Everywhere"))))
    return options


def get_image_data(image_type, category):
    url = getattr(category, image_type + '_url')
    metadata = getattr(category, image_type + '_metadata')
    return {
        'url': url,
        'filename': metadata['filename'],
        'size': metadata['size'],
        'content_type': metadata['content_type']
    }
