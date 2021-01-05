# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from uuid import UUID

from flask import request, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.management.controllers.base import ManageEventMixin
from indico.modules.events.util import check_event_locked
from indico.util.decorators import classproperty


class SpecificAbstractMixin:
    """Mixin for RHs that deal with a specific abstract."""

    # whether the RH should use Abstract's UUID when querying
    USE_ABSTRACT_UUID = False

    @classproperty
    @classmethod
    def normalize_url_spec(cls):
        return {
            'locators': {
                lambda self: self.abstract.locator.token if cls.USE_ABSTRACT_UUID else self.abstract
            }
        }

    _abstract_query_options = ()

    @property
    def _abstract_query(self):
        query = Abstract.query
        if self._abstract_query_options:
            query = query.options(*self._abstract_query_options)
        return query

    def _process_args(self):
        filters = {'is_deleted': False}
        if self.USE_ABSTRACT_UUID:
            try:
                UUID(request.view_args['uuid'])
            except ValueError:
                raise NotFound
            filters['uuid'] = request.view_args['uuid']
        else:
            filters['id'] = request.view_args['abstract_id']
        self.abstract = self._abstract_query.filter_by(**filters).one()

    def _check_access(self):
        if not self._check_abstract_protection():
            raise Forbidden

    def _check_abstract_protection(self):
        raise NotImplementedError


class RHAbstractsBase(RHDisplayEventBase):
    """Base class for all abstract-related RHs."""

    EVENT_FEATURE = 'abstracts'

    def _check_access(self):
        RHDisplayEventBase._check_access(self)
        # Only let event managers access the management versions.
        if self.management and not self.event.can_manage(session.user):
            raise Forbidden
        check_event_locked(self, self.event)

    @property
    def management(self):
        """Whether the RH is currently used in the management area."""
        return request.view_args.get('management', False)


class RHManageAbstractsBase(ManageEventMixin, RHAbstractsBase):
    """
    Base class for all abstract-related RHs that require full event
    management permissions.
    """

    DENY_FRAMES = True

    @property
    def management(self):
        """Whether the RH is currently used in the management area."""
        return request.view_args.get('management', True)


class RHAbstractBase(SpecificAbstractMixin, RHAbstractsBase):
    """
    Base class for all abstract-related RHs that require read access
    to the associated abstract.
    """

    def _process_args(self):
        RHAbstractsBase._process_args(self)
        SpecificAbstractMixin._process_args(self)

    def _check_access(self):
        RHAbstractsBase._check_access(self)
        SpecificAbstractMixin._check_access(self)

    def _check_abstract_protection(self):
        """Perform a permission check on the current abstract.

        Override this in case you want to check for more specific
        privileges than the generic "can access".
        """
        return self.abstract.can_access(session.user)
