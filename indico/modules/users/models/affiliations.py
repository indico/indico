# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import ARRAY, JSONB, array
from sqlalchemy.event import listens_for
from sqlalchemy.orm import column_property, mapper

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import define_unaccented_lowercase_index
from indico.core.db.sqlalchemy.searchable import make_fts_index
from indico.util.string import format_repr


class Affiliation(db.Model):
    __tablename__ = 'affiliations'

    __table_args__ = (db.Index(None, 'meta', postgresql_using='gin'),
                      {'schema': 'indico'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        index=True
    )
    alt_names = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[],
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )
    street = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    postcode = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    city = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    country_code = db.Column(
        db.String,
        nullable=False,
        default='',
    )
    #: Opaque external data related to this affiliation
    meta = db.Column(
        JSONB,
        nullable=False,
        default={},
    )
    #: An indexed string containing all names for effective searching
    #: This string looks like ``|||name|||altname|||altname2|||...|||`` so a normal ``*foo*`` query
    #: against it lets you do a substring search, and searching for ``|||foo|||`` lets you do an
    #: exact match.
    searchable_names = column_property(
        db.func.indico.text_array_to_string(array(['']) +
                                            db.func.indico.text_array_append(alt_names, name) +
                                            array(['']), '|||'),
        deferred=True,
    )

    # relationship backrefs:
    # - abstract_links (AbstractPersonLink._affiliation_link)
    # - contribution_links (ContributionPersonLink._affiliation_link)
    # - event_links (EventPersonLink._affiliation_link)
    # - event_person_affiliations (EventPerson.affiliation_link)
    # - session_block_links (SessionBlockPersonLink._affiliation_link)
    # - subcontribution_links (SubContributionPersonLink._affiliation_link)
    # - user_affiliations (User.affiliation_link)

    def __repr__(self):
        return format_repr(self, 'id', _text=self.name)

    @classmethod
    def get_or_create_from_data(cls, affiliation_data):
        existing = (cls.query
                    .filter_by(name=affiliation_data['name'],
                               city=(affiliation_data['city'] or ''),
                               country_code=(affiliation_data['country_code'] or ''))
                    .order_by(Affiliation.id)
                    .first())
        if existing:
            return existing
        return cls(**affiliation_data)


define_unaccented_lowercase_index(Affiliation.searchable_names, Affiliation.__table__,
                                  'ix_affiliations_searchable_names_unaccent')
make_fts_index(Affiliation, 'searchable_names')


@listens_for(mapper, 'after_configured', once=True)
def _mappers_configured():
    from indico.modules.events.models.persons import EventPerson
    from indico.modules.users.models.users import User
    ref_classes = [User, EventPerson]
    subquery = db.union(
        *((db.select([cls.affiliation_id.label('id'),
                      db.func.count(cls.id).label('count'),
                      db.select([db.func.count(cls.id)]).scalar_subquery().label('total')])
           .select_from(cls)
           .group_by(cls.affiliation_id)) for cls in ref_classes)
    ).subquery()
    # The (rounded) popularity should be 0 if there's no references, >= 1 if there is at least one reference,
    # and at most 10. Since under normal circumstances an affiliation is referenced at most on 30% of objects,
    # a logarithmic-type scale is the most useful. In the end, the best results were obtained by the following
    # reciprocal function:
    #                                           P = 11 - 100/(x + 10)
    #      where x is the percentage of occurences of an affiliation
    # Since x = 100c / N, where c is the count and N is the total number of objects, the formula can be
    # rewritten as:
    #                                           P = 11 - 10N/(10c + N)
    # Because this formula might result in a division by 0 in cases where there are no instances of the reference
    # object, 1 is added to the divisor, which has little impact on the final result. Additionally, for cases in
    # which the reference count (c) is 0, these entries aren't present in the subquery and thus not calculated
    # through this formula, thus being coalesced to 0 as intended.
    query = (
        db.select([
            db.func.coalesce(
                db.func.sum(
                    11.0 - ((10.0 * db.column('total')) / ((10.0 * db.column('count')) + db.column('total') + 1))
                ) / len(ref_classes),
            0)
        ])
        .select_from(subquery)
        .where(db.column('id') == Affiliation.id)
        .scalar_subquery()
    )
    Affiliation.popularity = column_property(query, deferred=True)
