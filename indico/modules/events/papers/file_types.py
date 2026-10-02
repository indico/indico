# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.modules.events.editing.models.file_types import BaseFileType


class PaperFileType(BaseFileType):
    event_backref_name = 'paper_file_types'

    source_editing_file_type_id = db.Column(
        db.ForeignKey('event_editing.file_types.id'),
        index=True,
        nullable=True
    )
    source_editing_file_type = db.relationship(
        'EditingFileType',
        backref=db.backref(
            'paper_file_type',
            cascade='all, delete-orphan',
            lazy=True,
            uselist=False,
            single_parent=True,
        ),
    )

    @declared_attr
    def __table_args__(cls):
        return (
            db.Index(
                'ix_uq_file_types_event_id_name_lower',
                cls.event_id,
                db.func.lower(cls.name),
                unique=True,
                postgresql_where=cls.source_editing_file_type_id.is_(None)
            ),
            db.Index(
                'ix_uq_file_types_event_id_source_editing_file_type_id',
                cls.event_id,
                cls.source_editing_file_type_id,
                unique=True,
                postgresql_where=cls.source_editing_file_type_id.isnot(None)
            ),
            {'schema': 'event_paper_reviewing'},
        )

    # relationship backrefs:
    # - files (PaperFile.file_type)

    def log(self, *args, **kwargs):
        """Log with prefilled metadata for the file type."""
        return self.event.log(*args, meta={'paper_file_type_id': self.id}, **kwargs)
