# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.cache import make_scoped_cache
from indico.core.db.sqlalchemy.principals import EmailPrincipal


def iter_acl(acl):
    """Iterate over an ACL in the most efficient order.

    This first yields users/emails, then ip networks, then local
    groups, and eventually multipass groups as a remote group check
    is much more expensive than checking if two users are the same
    (``==``), if an ip is in a network (just some math) or if a user
    is in a local group (SQL query).

    :param acl: any iterable containing users/groups or objects which
                contain users/groups in a `principal` attribute
    """
    return sorted(acl, key=lambda x: (getattr(x, 'principal', x).principal_order,
                                      not getattr(getattr(x, 'principal', x), 'is_local', None)))


def principal_from_identifier(identifier, allow_groups=False, allow_external_users=False, allow_event_roles=False,
                              allow_event_persons=False, allow_category_roles=False, allow_registration_forms=False,
                              allow_emails=False, allow_networks=False, event_id=None, category_id=None,
                              soft_fail=False):
    from indico.modules.categories.models.categories import Category
    from indico.modules.categories.models.roles import CategoryRole
    from indico.modules.events.models.events import Event
    from indico.modules.events.models.persons import EventPerson
    from indico.modules.events.models.roles import EventRole
    from indico.modules.events.registration.models.forms import RegistrationForm
    from indico.modules.groups import GroupProxy
    from indico.modules.networks.models.networks import IPNetworkGroup
    from indico.modules.users import User
    from indico.modules.users.models.affiliations import Affiliation
    from indico.modules.users.models.users import UserTitle

    if allow_category_roles and category_id is None and event_id is None:
        raise ValueError('Cannot use category roles without a category/event context')
    if allow_event_roles and event_id is None:
        raise ValueError('Cannot use event roles without an event context')
    if allow_event_persons and event_id is None:
        raise ValueError('Cannot use event persons without an event context')
    if allow_registration_forms and event_id is None:
        raise ValueError('Cannot use registration forms without an event context')

    try:
        type_, data = identifier.split(':', 1)
    except ValueError:
        raise ValueError('Invalid data')

    if type_ == 'User':
        try:
            user_id = int(data)
        except ValueError:
            raise ValueError('Invalid data')
        user = User.get(user_id, is_deleted=(None if soft_fail else False))
        if user is None:
            raise ValueError(f'Invalid user: {user_id}')
        return user
    elif type_ == 'ExternalUser':
        if not allow_external_users:
            raise ValueError('External users are not allowed')
        cache = make_scoped_cache('external-user')
        external_user_data = cache.get(data)
        if not external_user_data:
            raise ValueError('Invalid data')
        user = User.query.filter(User.all_emails == external_user_data['email'], ~User.is_deleted).first()
        if user:
            return user
        # create a pending user. this user isn't sent to the DB unless it gets added
        # to the sqlalchemy session somehow (e.g. by adding it to an ACL).
        # like this processing form data does not result in something being stored in
        # the database, which is good!
        user = User(first_name=external_user_data['first_name'], last_name=external_user_data['last_name'],
                    email=external_user_data['email'], affiliation=external_user_data['affiliation'],
                    address=external_user_data['address'], phone=external_user_data['phone'], _title=UserTitle.none,
                    is_pending=True)
        if affiliation_data := external_user_data.get('affiliation_data'):
            user.affiliation_link = Affiliation.get_or_create_from_data(affiliation_data)
            user.affiliation = user.affiliation_link.name
        return user
    elif type_ == 'Group':
        if not allow_groups:
            raise ValueError('Groups are not allowed')
        try:
            provider, name = data.split(':', 1)
        except ValueError:
            raise ValueError('Invalid data')
        if not provider:
            # local group
            try:
                group_id = int(name)
            except ValueError:
                raise ValueError('Invalid data')
            group = GroupProxy(group_id)
        else:
            # multipass group
            group = GroupProxy(name, provider)
        if not soft_fail and group.group is None:
            raise ValueError(f'Invalid group: {data}')
        return group
    elif type_ == 'EventRole':
        if not allow_event_roles:
            raise ValueError('Event roles are not allowed')
        try:
            event_role_id = int(data)
        except ValueError:
            raise ValueError('Invalid data')
        event_role = EventRole.get(event_role_id)
        if event_role is None or event_role.event_id != event_id:
            raise ValueError(f'Invalid event role: {event_role_id}')
        return event_role
    elif type_ == 'EventPerson':
        if not allow_event_persons:
            raise ValueError('Event persons are not allowed')
        try:
            event_person_id = int(data)
        except ValueError:
            raise ValueError('Invalid data')
        event_person = EventPerson.get(event_person_id)
        if event_person is None or event_person.event_id != event_id:
            raise ValueError(f'Invalid event person: {event_person_id}')
        return event_person
    elif type_ == 'CategoryRole':
        if not allow_category_roles:
            raise ValueError('Category roles are not allowed')
        category = None
        if category_id is not None:
            category = Category.get(category_id)
            if category is None:
                raise ValueError(f'Invalid category id: {category_id}')
        elif event_id is not None:
            event = Event.get(event_id)
            if event is None:
                raise ValueError(f'Invalid event id: {event_id}')
            category = event.category
        try:
            category_role_id = int(data)
        except ValueError:
            raise ValueError('Invalid data')
        if soft_fail:
            category_role = CategoryRole.get(category_role_id)
        else:
            category_role = CategoryRole.get_category_role_by_id(category, category_role_id)
        if category_role is None:
            raise ValueError(f'Invalid category role: {category_role_id}')
        return category_role
    elif type_ == 'RegistrationForm':
        if not allow_registration_forms:
            raise ValueError('Registration forms are not allowed')

        try:
            reg_form_id = int(data)
        except ValueError:
            raise ValueError('Invalid data')

        registration_form = RegistrationForm.get(reg_form_id, is_deleted=(None if soft_fail else False))
        if registration_form is None or registration_form.event_id != event_id:
            raise ValueError(f'Invalid registration form: {reg_form_id}')
        return registration_form
    elif type_ == 'Email':
        if not allow_emails:
            raise ValueError('Emails are not allowed')
        return EmailPrincipal(data)
    elif type_ == 'IPNetworkGroup':
        if not allow_networks:
            raise ValueError('Network groups are not allowed')
        try:
            netgroup_id = int(data)
        except ValueError:
            raise ValueError('Invalid data')
        netgroup = IPNetworkGroup.get(netgroup_id)
        if netgroup is None or (netgroup.hidden and not soft_fail):
            raise ValueError(f'Invalid network group: {netgroup_id}')
        return netgroup
    else:
        raise ValueError('Invalid data')
