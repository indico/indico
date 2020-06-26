# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


class CategoryRole(db.Model):
    __tablename__ = 'roles'
    __table_args__ = (db.CheckConstraint('code = upper(code)', 'uppercase_code'),
                      db.Index(None, 'category_id', 'code', unique=True),
                      {'schema': 'categories'})

    is_group = False
    is_event_role = False
    is_registration_form = False
    is_category_role = True
    is_single_person = True
    is_network = False
    principal_order = 2
    principal_type = PrincipalType.category_role

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        nullable=False,
        index=True
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    code = db.Column(
        db.String,
        nullable=False
    )
    color = db.Column(
        db.String,
        nullable=False
    )

    category = db.relationship(
        'Category',
        lazy=True,
        backref=db.backref(
            'roles',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    members = db.relationship(
        'User',
        secondary='categories.role_members',
        lazy=True,
        collection_class=set,
        backref=db.backref('category_roles', lazy=True, collection_class=set),
    )

    # relationship backrefs:
    # - in_attachment_acls (AttachmentPrincipal.category_role)
    # - in_attachment_folder_acls (AttachmentFolderPrincipal.category_role)
    # - in_category_acls (CategoryPrincipal.category_role)
    # - in_contribution_acls (ContributionPrincipal.category_role)
    # - in_event_acls (EventPrincipal.category_role)
    # - in_event_settings_acls (EventSettingPrincipal.category_role)
    # - in_session_acls (SessionPrincipal.category_role)
    # - in_track_acls (TrackPrincipal.category_role)

    def __contains__(self, user):
        return user is not None and self in user.category_roles

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'code', _text=self.name)

    @locator_property
    def locator(self):
        return dict(self.category.locator, role_id=self.id)

    @property
    def identifier(self):
        return 'CategoryRole:{}'.format(self.id)

    @property
    def css(self):
        return 'color: #{0} !important; border-color: #{0} !important'.format(self.color)

    @property
    def style(self):
        return {'color': '#' + self.color, 'borderColor': '#' + self.color}

    @staticmethod
    def get_category_roles(cat):
        """Get the category roles available for the specified category."""
        return CategoryRole.query.join(cat.chain_query.subquery()).order_by(CategoryRole.code).all()

    @staticmethod
    def get_category_role_by_id(cat, id):
        """
        Get a category role in the context of the specified category.
        If the role is not defined in the category or one of its parents,
        it is considered non-existing.
        """
        return CategoryRole.query.filter_by(id=id).join(cat.chain_query.subquery()).first()


role_members_table = db.Table(
    'role_members',
    db.metadata,
    db.Column(
        'role_id',
        db.Integer,
        db.ForeignKey('categories.roles.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    schema='categories'
)
