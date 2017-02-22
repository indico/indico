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

from flask import request, has_request_context, session
from persistent import Persistent
from pytz import utc
from sqlalchemy.orm import joinedload

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.modules.events.cloning import EventCloner
from indico.modules.events.features import features_event_settings
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.modules.events.operations import create_event
from indico.modules.users.legacy import AvatarUserWrapper
from indico.util.caching import memoize_request
from indico.util.i18n import _
from indico.util.string import return_ascii, is_legacy_id

from MaKaC.common.fossilize import Fossilizable
from MaKaC.common.Locators import Locator
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.errors import NotFoundError
from MaKaC.trashCan import TrashCanManager


class CoreObject(Persistent):
    pass


class CommonObjectBase(CoreObject, Fossilizable):
    """
    This class is for holding commonly used methods that are used by several classes.
    It is inherited by the following classes:
      * Category
      * Conference
      * Session
      * Contribution
      * SubContribution
      * Material
      * Resource
    """

    @property
    @memoize_request
    def attached_items(self):
        """
        CAUTION: this won't return empty directories (used by interface), nor things the
        current user can't see
        """
        from indico.modules.attachments.util import get_attached_items
        if isinstance(self, Conference):
            return get_attached_items(self.as_event, include_empty=False, include_hidden=False, preload_event=True)
        else:
            raise ValueError("Object of type '{}' cannot have attachments".format(type(self)))


def warn_on_access(fn):
    import warnings
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if Config.getInstance().getDebug():
            warnings.warn('Called {}'.format(fn.__name__), stacklevel=2)
        return fn(*args, **kwargs)

    return wrapper


class Conference(CommonObjectBase):
    """This class represents the real world conferences themselves. Objects of
        this class will contain basic data about the confence and will provide
        access to other objects representing certain parts of the conferences
        (ex: contributions, sessions, ...).
    """

    def __init__(self, id=''):
        self.id = id

    @return_ascii
    def __repr__(self):
        return '<Conference({0}, {1}, {2})>'.format(self.id, self.title, self.startDate)

    @property
    @warn_on_access
    def startDate(self):
        return self.as_event.start_dt

    @property
    @warn_on_access
    def endDate(self):
        return self.as_event.end_dt

    @property
    @warn_on_access
    def timezone(self):
        return self.as_event.timezone.encode('utf-8')

    @property
    @warn_on_access
    def title(self):
        return self.as_event.title.encode('utf-8')

    @property
    @warn_on_access
    def description(self):
        return self.as_event.description.encode('utf-8')

    @property
    @memoize_request
    def as_event(self):
        """Returns the :class:`.Event` for this object

        :rtype: indico.modules.events.models.events.Event
        """
        from indico.modules.events.models.events import Event
        event_id = int(self.id)
        # this is pretty ugly, but the api sends queries in a loop in
        # some cases and we can't really avoid this for now.  If we
        # already have the event in the identity map we keep using
        # the simple id-based lookup though as lazyloading the acl
        # entries is just one query anyway
        if (has_request_context() and request.blueprint == 'api' and request.endpoint != 'api.jsonrpc' and
                (Event, (event_id,)) not in db.session.identity_map):
            acl_user_strategy = joinedload('acl_entries').defaultload('user')
            # remote group membership checks will trigger a load on _all_emails
            # but not all events use this so there's no need to eager-load them
            acl_user_strategy.noload('_primary_email')
            acl_user_strategy.noload('_affiliation')
            return Event.find(id=event_id).options(acl_user_strategy).one()
        else:
            # use get() so sqlalchemy can make use of the identity cache
            return Event.get_one(event_id)

    def __cmp__(self, toCmp):
        if isinstance(toCmp, Conference):
            return cmp(self.getId(), toCmp.getId())
        else:
            return cmp(hash(self), hash(toCmp))

    def __eq__(self, toCmp):
        return self is toCmp

    def __ne__(self, toCmp):
        return not(self is toCmp)

    def getURL(self):
        return self.as_event.short_external_url

    @warn_on_access
    def getId( self ):
        """returns (string) the unique identifier of the conference"""
        return self.id

    def setId(self, newId):
        """changes the current unique identifier of the conference to the
            one which is specified"""
        self.id = str(newId)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the conference instance """
        d = Locator()
        d["confId"] = self.id
        return d

    def delete(self, user=None):
        signals.event.deleted.send(self, user=user)
        ConferenceHolder().remove(self)
        TrashCanManager().add(self)
        self._p_changed = True

    def clone(self, startDate):
        # startDate is in the timezone of the event
        old_event = self.as_event
        start_dt = old_event.tzinfo.localize(startDate).astimezone(utc)
        end_dt = start_dt + old_event.duration
        data = {
            'start_dt': start_dt,
            'end_dt': end_dt,
            'timezone': old_event.timezone,
            'title': old_event.title,
            'description': old_event.description,
            'visibility': old_event.visibility
        }
        event = create_event(old_event.category, old_event.type_, data,
                             features=features_event_settings.get(self, 'enabled'),
                             add_creator_as_manager=False)
        conf = event.as_legacy

        # Run the new modular cloning system
        EventCloner.run_cloners(old_event, event)
        signals.event.cloned.send(old_event, new_event=event)

        # Grant access to the event creator -- must be done after modular cloners
        # since cloning the event ACL would result in a duplicate entry
        with event.logging_disabled:
            event.update_principal(session.user, full_access=True)

        return conf


class ConferenceHolder( ObjectHolder ):
    """Specialised ObjectHolder dealing with conference objects. It gives a
            common entry point and provides simple methods to access and
            maintain the collection of stored conferences (DB).
    """
    idxName = "conferences"
    counterName = "CONFERENCE"

    def _newId(self):
        raise RuntimeError('Tried to get new event id from zodb')

    def add(self, conf, event):
        event.assign_id()
        conf.setId(event.id)
        if conf.id in self._getIdx():
            raise RuntimeError('{} is already in ConferenceHolder'.format(conf.id))
        ObjectHolder.add(self, conf)

    def getById(self, id, quiet=False):
        id = str(id)
        if is_legacy_id(id):
            mapping = LegacyEventMapping.find_first(legacy_event_id=id)
            id = str(mapping.event_id) if mapping is not None else None
        event = self._getIdx().get(id) if id is not None else None
        if event is None and not quiet:
            raise NotFoundError(_("The event with id '{}' does not exist or has been deleted").format(id),
                                title=_("Event not found"))
        return event
