# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools

from sqlalchemy.orm import contains_eager, joinedload, load_only, raiseload, selectinload, subqueryload, undefer
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.db.sqlalchemy.util.queries import get_n_matching
from indico.modules.attachments.models.attachments import Attachment
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.models.principals import AttachmentFolderPrincipal, AttachmentPrincipal
from indico.modules.categories import Category
from indico.modules.categories.models.principals import CategoryPrincipal
from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.notes.models.notes import EventNote, EventNoteRevision
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.search.base import IndicoSearchProvider, SearchTarget
from indico.modules.search.result_schemas import (AttachmentResultSchema, CategoryResultSchema,
                                                  ContributionResultSchema, EventNoteResultSchema, EventResultSchema)
from indico.modules.search.schemas import (AttachmentSchema, DetailedCategorySchema, HTMLStrippingContributionSchema,
                                           HTMLStrippingEventNoteSchema, HTMLStrippingEventSchema)


def _apply_acl_entry_strategy(rel, principal):
    user_strategy = rel.joinedload('user')
    user_strategy.lazyload('*')
    user_strategy.load_only('id')
    rel.joinedload('local_group').load_only('id')
    if principal.allow_networks:
        rel.joinedload('ip_network_group').load_only('id')
    if principal.allow_category_roles:
        rel.joinedload('category_role').load_only('id')
    if principal.allow_event_roles:
        rel.joinedload('event_role').load_only('id')
    if principal.allow_registration_forms:
        rel.joinedload('registration_form').load_only('id')
    return rel


def _apply_event_access_strategy(rel):
    rel.load_only('id', 'category_id', 'access_key', 'protection_mode')
    return rel


def _apply_contrib_access_strategy(rel):
    rel.load_only('id', 'session_id', 'event_id', 'protection_mode', 'title')
    return rel


class InternalSearch(IndicoSearchProvider):
    def search(self, query, user=None, page=None, object_types=(), *, admin_override_enabled=False,
               **params):
        category_id = params.get('category_id')
        event_id = params.get('event_id')
        if object_types == [SearchTarget.category]:
            pagenav, results = self.search_categories(query, user, page, category_id,
                                                      admin_override_enabled)
        elif object_types == [SearchTarget.event]:
            pagenav, results = self.search_events(query, user, page, category_id,
                                                  admin_override_enabled)
        elif set(object_types) == {SearchTarget.contribution, SearchTarget.subcontribution}:
            pagenav, results = self.search_contribs(query, user, page, category_id, event_id,
                                                    admin_override_enabled)
        elif object_types == [SearchTarget.attachment]:
            pagenav, results = self.search_attachments(query, user, page, category_id, event_id,
                                                       admin_override_enabled)
        elif object_types == [SearchTarget.event_note]:
            pagenav, results = self.search_notes(query, user, page, category_id, event_id,
                                                 admin_override_enabled)
        else:
            pagenav, results = {}, []
        return {
            'total': -1 if results else 0,
            'pagenav': pagenav,
            'results': results,
        }

    def _preload_categories(self, objs, preloaded_categories):
        obj_types = {type(o) for o in objs}
        assert len(obj_types) == 1
        obj_type = obj_types.pop()

        if obj_type == Event:
            chain_query = db.session.query(Event.category_chain).filter(Event.id.in_(o.id for o in objs))
        elif obj_type == Category:
            chain_query = db.session.query(Category.chain_ids).filter(Category.id.in_(o.id for o in objs))
        elif obj_type == Contribution:
            chain_query = (db.session.query(Event.category_chain)
                           .join(Contribution.event)
                           .filter(Contribution.id.in_(o.id for o in objs)))
        elif obj_type == Attachment:
            chain_query = (db.session.query(Event.category_chain)
                           .join(Attachment.folder)
                           .join(AttachmentFolder.event)
                           .filter(Attachment.id.in_(o.id for o in objs)))
        elif obj_type == EventNote:
            chain_query = (db.session.query(Event.category_chain)
                           .join(EventNote.event)
                           .filter(EventNote.id.in_(o.id for o in objs)))
        else:
            raise Exception(f'Unhandled object type: {obj_type}')
        category_ids = set(itertools.chain.from_iterable(id for id, in chain_query))
        query = (
            Category.query
            .filter(Category.id.in_(category_ids))
            .options(load_only('id', 'parent_id', 'protection_mode'))
        )
        Category.preload_relationships(query, 'acl_entries',
                                       strategy=lambda rel: _apply_acl_entry_strategy(subqueryload(rel),
                                                                                      CategoryPrincipal))
        preloaded_categories |= set(query)

    def _can_access(self, user, obj, allow_effective_protection_mode=True, admin_override_enabled=False):
        if isinstance(obj, (Category, Event, Session, Contribution)):
            # more efficient for events/categories/contribs since it avoids climbing up the chain
            protection_mode = (obj.effective_protection_mode if allow_effective_protection_mode
                               else obj.protection_mode)
        elif isinstance(obj, Attachment):
            # attachments don't have it so we can only skip access checks if they
            # are public themselves
            protection_mode = obj.protection_mode
        elif isinstance(obj, EventNote):
            # notes inherit from their parent
            return self._can_access(user, obj.object, allow_effective_protection_mode=False,
                                    admin_override_enabled=admin_override_enabled)
        elif isinstance(obj, SubContribution):
            # subcontributions inherit from their contribution
            return self._can_access(user, obj.contribution, allow_effective_protection_mode=False,
                                    admin_override_enabled=admin_override_enabled)
        else:
            raise TypeError(f'Unexpected object: {obj}')

        if isinstance(obj, Event) and not obj.can_display(user, allow_admin=admin_override_enabled):
            return False

        return (protection_mode == ProtectionMode.public or
                obj.can_access(user, allow_admin=admin_override_enabled))

    def _paginate(self, query, page, column, user, admin_override_enabled):
        reverse = False
        pagenav = {'prev': None, 'next': None}
        if not page:
            query = query.order_by(column.desc())
        elif page > 0:  # next page
            query = query.filter(column < page).order_by(column.desc())
            # since we asked for a next page we know that a previous page exists
            pagenav['prev'] = -(page - 1)
        elif page < 0:  # prev page
            query = query.filter(column > -page).order_by(column)
            # since we asked for a previous page we know that a next page exists
            pagenav['next'] = -(page - 1)
            reverse = True

        preloaded_categories = set()
        res = get_n_matching(
            query, self.RESULTS_PER_PAGE + 1,
            lambda obj: self._can_access(user, obj, admin_override_enabled=admin_override_enabled),
            prefetch_factor=20,
            preload_bulk=lambda objs: self._preload_categories(objs, preloaded_categories)
        )

        if len(res) > self.RESULTS_PER_PAGE:
            # we queried 1 more so we can see if there are more results available
            del res[self.RESULTS_PER_PAGE:]
            if reverse:
                pagenav['prev'] = -res[-1].id
            else:
                pagenav['next'] = res[-1].id

        if reverse:
            res.reverse()

        return res, pagenav

    def search_categories(self, q, user, page, category_id, admin_override_enabled):
        if not category_id:
            query = Category.query
        else:
            category = Category.get(category_id)
            if category is None:
                raise BadRequest('Invalid category')
            query = category.deep_children_query

        query = (query
                 .filter(Category.title_matches(q),
                         ~Category.is_deleted)
                 .options(undefer('chain'),
                          undefer(Category.effective_protection_mode),
                          subqueryload(Category.acl_entries)))

        objs, pagenav = self._paginate(query, page, Category.id, user, admin_override_enabled)
        res = DetailedCategorySchema(many=True).dump(objs)
        return pagenav, CategoryResultSchema(many=True).load(res)

    def search_events(self, q, user, page, category_id, admin_override_enabled):
        filters = [
            Event.title_matches(q),
            ~Event.is_deleted,
            ~Event.is_unlisted
        ]

        if category_id is not None:
            filters.append(Event.category_chain_overlaps(category_id))

        query = (
            Event.query
            .filter(*filters)
            .options(
                load_only('id', 'category_id', 'access_key', 'protection_mode'),
                undefer(Event.effective_protection_mode),
                _apply_acl_entry_strategy(selectinload(Event.acl_entries), EventPrincipal)
            )
        )
        objs, pagenav = self._paginate(query, page, Event.id, user, admin_override_enabled)

        query = (
            Event.query
            .filter(Event.id.in_(e.id for e in objs))
            .options(
                undefer(Event.detailed_category_chain),
                selectinload(Event.person_links).joinedload('person').joinedload('user').load_only('is_system'),
                joinedload(Event.own_venue),
                joinedload(Event.own_room).options(raiseload('*'), joinedload('location')),
            )
        )
        events_by_id = {e.id: e for e in query}
        events = [events_by_id[e.id] for e in objs]

        res = HTMLStrippingEventSchema(many=True).dump(events)
        return pagenav, EventResultSchema(many=True).load(res)

    def search_contribs(self, q, user, page, category_id, event_id, admin_override_enabled):
        # XXX: Ideally we would search in subcontributions as well, but our pagination
        # does not really work when we do not have a single unique ID

        contrib_filters = [
            Contribution.title_matches(q) | Contribution.description_matches(q),
            ~Contribution.is_deleted,
            ~Event.is_deleted,
            ~Event.is_unlisted
        ]

        if category_id is not None:
            contrib_filters.append(Event.category_chain_overlaps(category_id))
        if event_id is not None:
            contrib_filters.append(Contribution.event_id == event_id)

        query = (
            Contribution.query
            .filter(*contrib_filters)
            .join(Contribution.event)
            .options(
                load_only('id', 'session_id', 'event_id', 'protection_mode'),
                undefer(Contribution.effective_protection_mode),
                _apply_acl_entry_strategy(selectinload(Contribution.acl_entries), ContributionPrincipal),
                joinedload(Contribution.session).options(
                    load_only('id', 'protection_mode', 'event_id'),
                    selectinload(Session.acl_entries)
                ),
                contains_eager('event').options(
                    _apply_acl_entry_strategy(selectinload(Event.acl_entries), EventPrincipal)
                )
            )
        )

        objs, pagenav = self._paginate(query, page, Contribution.id, user, admin_override_enabled)

        event_strategy = joinedload(Contribution.event)
        event_strategy.joinedload(Event.own_venue)
        event_strategy.joinedload(Event.own_room).options(raiseload('*'), joinedload('location'))
        event_strategy.undefer(Event.detailed_category_chain)

        session_strategy = joinedload(Contribution.session)
        session_strategy.joinedload(Session.own_venue)
        session_strategy.joinedload(Session.own_room).options(raiseload('*'), joinedload('location'))

        session_block_strategy = joinedload(Contribution.session_block)
        session_block_strategy.joinedload(SessionBlock.own_venue)
        session_block_strategy.joinedload(SessionBlock.own_room).options(raiseload('*'), joinedload('location'))
        session_block_session_strategy = session_block_strategy.joinedload(SessionBlock.session)
        session_block_session_strategy.joinedload(Session.own_venue)
        session_block_session_strategy.joinedload(Session.own_room).options(raiseload('*'), joinedload('location'))

        query = (
            Contribution.query
            .filter(Contribution.id.in_(c.id for c in objs))
            .options(
                selectinload(Contribution.person_links).joinedload('person').joinedload('user').load_only('is_system'),
                event_strategy,
                session_strategy,
                session_block_strategy,
                joinedload(Contribution.type),
                joinedload(Contribution.own_venue),
                joinedload(Contribution.own_room).options(raiseload('*'), joinedload('location')),
                joinedload(Contribution.timetable_entry),
            )
        )
        contribs_by_id = {c.id: c for c in query}
        contribs = [contribs_by_id[c.id] for c in objs]

        res = HTMLStrippingContributionSchema(many=True).dump(contribs)
        return pagenav, ContributionResultSchema(many=True).load(res)

    def search_attachments(self, q, user, page, category_id, event_id, admin_override_enabled):
        contrib_event = db.aliased(Event)
        contrib_session = db.aliased(Session)
        subcontrib_contrib = db.aliased(Contribution)
        subcontrib_session = db.aliased(Session)
        subcontrib_event = db.aliased(Event)
        session_event = db.aliased(Event)

        attachment_strategy = _apply_acl_entry_strategy(selectinload(Attachment.acl_entries), AttachmentPrincipal)
        folder_strategy = contains_eager(Attachment.folder)
        folder_strategy.load_only('id', 'protection_mode', 'link_type', 'category_id', 'event_id', 'linked_event_id',
                                  'contribution_id', 'subcontribution_id', 'session_id')
        _apply_acl_entry_strategy(folder_strategy.selectinload(AttachmentFolder.acl_entries), AttachmentFolderPrincipal)
        # event
        event_strategy = folder_strategy.contains_eager(AttachmentFolder.linked_event)
        _apply_event_access_strategy(event_strategy)
        _apply_acl_entry_strategy(event_strategy.selectinload(Event.acl_entries), EventPrincipal)
        # contribution
        contrib_strategy = folder_strategy.contains_eager(AttachmentFolder.contribution)
        _apply_contrib_access_strategy(contrib_strategy)
        _apply_acl_entry_strategy(contrib_strategy.selectinload(Contribution.acl_entries), ContributionPrincipal)
        contrib_event_strategy = contrib_strategy.contains_eager(Contribution.event.of_type(contrib_event))
        _apply_event_access_strategy(contrib_event_strategy)
        _apply_acl_entry_strategy(contrib_event_strategy.selectinload(contrib_event.acl_entries), EventPrincipal)
        contrib_session_strategy = contrib_strategy.contains_eager(Contribution.session.of_type(contrib_session))
        contrib_session_strategy.load_only('id', 'event_id', 'protection_mode')
        _apply_acl_entry_strategy(contrib_session_strategy.selectinload(contrib_session.acl_entries), SessionPrincipal)
        # subcontribution
        subcontrib_strategy = folder_strategy.contains_eager(AttachmentFolder.subcontribution)
        subcontrib_strategy.load_only('id', 'contribution_id', 'title')
        subcontrib_contrib_strategy = subcontrib_strategy.contains_eager(
            SubContribution.contribution.of_type(subcontrib_contrib)
        )
        _apply_contrib_access_strategy(subcontrib_contrib_strategy)
        _apply_acl_entry_strategy(subcontrib_contrib_strategy
                                  .selectinload(subcontrib_contrib.acl_entries), ContributionPrincipal)
        subcontrib_event_strategy = subcontrib_contrib_strategy.contains_eager(
            subcontrib_contrib.event.of_type(subcontrib_event)
        )
        _apply_event_access_strategy(subcontrib_event_strategy)
        _apply_acl_entry_strategy(subcontrib_event_strategy.selectinload(subcontrib_event.acl_entries), EventPrincipal)
        subcontrib_session_strategy = subcontrib_contrib_strategy.contains_eager(
            subcontrib_contrib.session.of_type(subcontrib_session)
        )
        subcontrib_session_strategy.load_only('id', 'event_id', 'protection_mode')
        _apply_acl_entry_strategy(subcontrib_session_strategy.selectinload(subcontrib_session.acl_entries),
                                  SessionPrincipal)
        # session
        session_strategy = folder_strategy.contains_eager(AttachmentFolder.session)
        session_strategy.load_only('id', 'event_id', 'protection_mode')
        session_event_strategy = session_strategy.contains_eager(Session.event.of_type(session_event))
        _apply_event_access_strategy(session_event_strategy)
        session_event_strategy.selectinload(session_event.acl_entries)
        _apply_acl_entry_strategy(session_strategy.selectinload(Session.acl_entries), SessionPrincipal)

        attachment_filters = [
            Attachment.title_matches(q),
            ~Attachment.is_deleted,
            ~AttachmentFolder.is_deleted,
            AttachmentFolder.link_type != LinkType.category,
            db.or_(
                AttachmentFolder.link_type != LinkType.event,
                (~Event.is_deleted & ~Event.is_unlisted),
            ),
            db.or_(
                AttachmentFolder.link_type != LinkType.contribution,
                ~Contribution.is_deleted & ~contrib_event.is_deleted & ~contrib_event.is_unlisted
            ),
            db.or_(
                AttachmentFolder.link_type != LinkType.subcontribution,
                db.and_(
                    ~SubContribution.is_deleted,
                    ~subcontrib_contrib.is_deleted,
                    ~subcontrib_event.is_deleted,
                    ~subcontrib_event.is_unlisted,
                )
            ),
            db.or_(
                AttachmentFolder.link_type != LinkType.session,
                ~Session.is_deleted & ~session_event.is_deleted & ~session_event.is_unlisted
            )
        ]

        if category_id is not None:
            attachment_filters.append(AttachmentFolder.event.has(Event.category_chain_overlaps(category_id)))
        if event_id is not None:
            attachment_filters.append(AttachmentFolder.event_id == event_id)

        query = (
            Attachment.query
            .join(Attachment.folder)
            .filter(*attachment_filters)
            .options(folder_strategy, attachment_strategy, joinedload(Attachment.user))
            .outerjoin(AttachmentFolder.linked_event)
            .outerjoin(AttachmentFolder.contribution)
            .outerjoin(Contribution.event.of_type(contrib_event))
            .outerjoin(Contribution.session.of_type(contrib_session))
            .outerjoin(AttachmentFolder.subcontribution)
            .outerjoin(SubContribution.contribution.of_type(subcontrib_contrib))
            .outerjoin(subcontrib_contrib.event.of_type(subcontrib_event))
            .outerjoin(subcontrib_contrib.session.of_type(subcontrib_session))
            .outerjoin(AttachmentFolder.session)
            .outerjoin(Session.event.of_type(session_event))
        )

        objs, pagenav = self._paginate(query, page, Attachment.id, user, admin_override_enabled)

        query = (
            Attachment.query
            .filter(Attachment.id.in_(a.id for a in objs))
            .options(
                joinedload(Attachment.folder).options(
                    joinedload(AttachmentFolder.subcontribution),
                    joinedload(AttachmentFolder.event).options(
                        undefer(Event.detailed_category_chain)
                    )
                )
            )
        )
        attachments_by_id = {a.id: a for a in query}
        attachments = [attachments_by_id[a.id] for a in objs]

        res = AttachmentSchema(many=True).dump(attachments)
        return pagenav, AttachmentResultSchema(many=True).load(res)

    def search_notes(self, q, user, page, category_id, event_id, admin_override_enabled):
        contrib_event = db.aliased(Event)
        contrib_session = db.aliased(Session)
        subcontrib_contrib = db.aliased(Contribution)
        subcontrib_session = db.aliased(Session)
        subcontrib_event = db.aliased(Event)
        session_event = db.aliased(Event)

        note_strategy = load_only('id', 'link_type', 'event_id', 'linked_event_id', 'contribution_id',
                                  'subcontribution_id', 'session_id', 'html')
        # event
        event_strategy = note_strategy.contains_eager(EventNote.linked_event)
        event_strategy.undefer(Event.effective_protection_mode)
        _apply_event_access_strategy(event_strategy)
        _apply_acl_entry_strategy(event_strategy.selectinload(Event.acl_entries), EventPrincipal)
        # contribution
        contrib_strategy = note_strategy.contains_eager(EventNote.contribution)
        _apply_contrib_access_strategy(contrib_strategy)
        _apply_acl_entry_strategy(contrib_strategy.selectinload(Contribution.acl_entries), ContributionPrincipal)
        contrib_event_strategy = contrib_strategy.contains_eager(Contribution.event.of_type(contrib_event))
        _apply_event_access_strategy(contrib_event_strategy)
        _apply_acl_entry_strategy(contrib_event_strategy.selectinload(contrib_event.acl_entries), EventPrincipal)
        contrib_session_strategy = contrib_strategy.contains_eager(Contribution.session.of_type(contrib_session))
        contrib_session_strategy.load_only('id', 'event_id', 'protection_mode')
        _apply_acl_entry_strategy(contrib_session_strategy.selectinload(contrib_session.acl_entries), SessionPrincipal)
        # subcontribution
        subcontrib_strategy = note_strategy.contains_eager(EventNote.subcontribution)
        subcontrib_contrib_strategy = subcontrib_strategy.contains_eager(
            SubContribution.contribution.of_type(subcontrib_contrib)
        )
        _apply_contrib_access_strategy(subcontrib_contrib_strategy)
        _apply_acl_entry_strategy(subcontrib_contrib_strategy
                                  .selectinload(subcontrib_contrib.acl_entries), ContributionPrincipal)
        subcontrib_event_strategy = subcontrib_contrib_strategy.contains_eager(
            subcontrib_contrib.event.of_type(subcontrib_event)
        )
        _apply_event_access_strategy(subcontrib_event_strategy)
        _apply_acl_entry_strategy(subcontrib_event_strategy.selectinload(subcontrib_event.acl_entries), EventPrincipal)
        subcontrib_session_strategy = subcontrib_contrib_strategy.contains_eager(
            subcontrib_contrib.session.of_type(subcontrib_session)
        )
        subcontrib_session_strategy.load_only('id', 'event_id', 'protection_mode')
        _apply_acl_entry_strategy(subcontrib_session_strategy.selectinload(subcontrib_session.acl_entries),
                                  SessionPrincipal)
        # session
        session_strategy = note_strategy.contains_eager(EventNote.session)
        session_strategy.load_only('id', 'event_id', 'protection_mode')
        session_event_strategy = session_strategy.contains_eager(Session.event.of_type(session_event))
        _apply_event_access_strategy(session_event_strategy)
        session_event_strategy.selectinload(session_event.acl_entries)
        _apply_acl_entry_strategy(session_strategy.selectinload(Session.acl_entries), SessionPrincipal)

        note_filters = [
            EventNote.html_matches(q),
            ~EventNote.is_deleted,
            db.or_(
                EventNote.link_type != LinkType.event,
                (~Event.is_deleted & ~Event.is_unlisted)
            ),
            db.or_(
                EventNote.link_type != LinkType.contribution,
                ~Contribution.is_deleted & ~contrib_event.is_deleted & ~contrib_event.is_unlisted
            ),
            db.or_(
                EventNote.link_type != LinkType.subcontribution,
                db.and_(
                    ~SubContribution.is_deleted,
                    ~subcontrib_contrib.is_deleted,
                    ~subcontrib_event.is_deleted,
                    ~subcontrib_event.is_unlisted,
                )
            ),
            db.or_(
                EventNote.link_type != LinkType.session,
                ~Session.is_deleted & ~session_event.is_deleted & ~session_event.is_unlisted
            )
        ]

        if category_id is not None:
            note_filters.append(EventNote.event.has(Event.category_chain_overlaps(category_id)))
        if event_id is not None:
            note_filters.append(EventNote.event_id == event_id)

        query = (
            EventNote.query
            .filter(*note_filters)
            .options(note_strategy)
            .outerjoin(EventNote.linked_event)
            .outerjoin(EventNote.contribution)
            .outerjoin(Contribution.event.of_type(contrib_event))
            .outerjoin(Contribution.session.of_type(contrib_session))
            .outerjoin(EventNote.subcontribution)
            .outerjoin(SubContribution.contribution.of_type(subcontrib_contrib))
            .outerjoin(subcontrib_contrib.event.of_type(subcontrib_event))
            .outerjoin(subcontrib_contrib.session.of_type(subcontrib_session))
            .outerjoin(EventNote.session)
            .outerjoin(Session.event.of_type(session_event))
        )

        objs, pagenav = self._paginate(query, page, EventNote.id, user, admin_override_enabled)

        query = (
            EventNote.query
            .filter(EventNote.id.in_(n.id for n in objs))
            .options(
                joinedload(EventNote.contribution),
                joinedload(EventNote.subcontribution).joinedload(SubContribution.contribution),
                joinedload(EventNote.event).options(undefer(Event.detailed_category_chain)),
                joinedload(EventNote.current_revision).joinedload(EventNoteRevision.user),
            )
        )
        notes_by_id = {n.id: n for n in query}
        notes = [notes_by_id[n.id] for n in objs]

        res = HTMLStrippingEventNoteSchema(many=True).dump(notes)
        return pagenav, EventNoteResultSchema(many=True).load(res)
