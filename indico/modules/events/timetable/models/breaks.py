# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy import DDL
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorMixin, ColorTuple
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


class Break(DescriptionMixin, ColorMixin, LocationMixin, db.Model):
    __tablename__ = 'breaks'
    __auto_table_args = {'schema': 'events'}
    location_backref_name = 'breaks'
    default_colors = ColorTuple('#202020', '#90c0f0')
    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    duration = db.Column(
        db.Interval,
        nullable=False
    )

    # relationship backrefs:
    # - timetable_entry (TimetableEntry.break_)

    def can_access(self, user):
        parent = self.timetable_entry.parent
        if parent:
            return parent.object.can_access(user)
        else:
            return self.event.can_access(user)

    @property
    def event(self):
        return self.timetable_entry.event if self.timetable_entry else None

    @property
    def location_parent(self):
        return (self.event
                if self.timetable_entry.parent_id is None
                else self.timetable_entry.parent.session_block)

    @property
    def start_dt(self):
        return self.timetable_entry.start_dt if self.timetable_entry else None

    @property
    def end_dt(self):
        return self.timetable_entry.start_dt + self.duration if self.timetable_entry else None

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title)

    @locator_property
    def locator(self):
        return dict(self.event.locator, break_id=self.id)


Break.register_location_events()


@listens_for(Break.duration, 'set')
def _set_duration(target, value, oldvalue, *unused):
    from indico.modules.events.util import register_time_change
    if oldvalue in (NEVER_SET, NO_VALUE):
        return
    if value != oldvalue and target.timetable_entry is not None:
        register_time_change(target.timetable_entry)


@listens_for(Break.__table__, 'after_create')
def _add_timetable_consistency_trigger(target, conn, **kw):
    sql = """
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE OF duration
        ON {}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('break');
    """.format(target.fullname)
    DDL(sql).execute(conn)
