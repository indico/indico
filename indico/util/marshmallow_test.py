# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

import pytest
import pytz
from marshmallow import ValidationError

from indico.core.marshmallow import mm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.users.models.users import User
from indico.util.marshmallow import ModelField, ModelList, NaiveDateTime


def test_NaiveDateTime_serialize():
    utc_now = datetime.now(pytz.UTC)
    now = utc_now.replace(tzinfo=None)
    obj = type('Test', (), {
        'naive': now,
        'aware': utc_now,
    })
    field = NaiveDateTime()
    assert field.serialize('naive', obj) == now.isoformat()
    with pytest.raises(AssertionError):
        field.serialize('aware', obj)


def test_NaiveDateTime_deserialize():
    utc_now = datetime.now(pytz.UTC)
    now = utc_now.replace(tzinfo=None)
    field = NaiveDateTime()
    assert field.deserialize(now.isoformat()) == now
    with pytest.raises(ValidationError):
        field.deserialize(utc_now.isoformat())


def test_ModelField_deserialize(dummy_user, dummy_contribution, create_event):
    field = ModelField(User)
    assert field.deserialize(dummy_user.id).id == dummy_user.id

    field = ModelField(User, column='first_name')
    assert field.deserialize(dummy_user.first_name).id == dummy_user.id

    dummy_user.is_deleted = True
    field = ModelField(User, filter_deleted=True)
    with pytest.raises(ValidationError):
        field.deserialize(dummy_user.id)

    field = ModelField(User, get_query=lambda m, _: m.query.filter_by(first_name=dummy_user.first_name))
    assert field.deserialize(dummy_user.id).id == dummy_user.id

    field = ModelField(User, get_query=lambda m, _: m.query.filter_by(first_name='Fake'))
    with pytest.raises(ValidationError):
        field.deserialize(dummy_user.id)

    field = ModelField(User, none_if_missing=True, filter_deleted=True)
    assert field.deserialize(dummy_user.id) is None

    event1 = create_event(title='event1')
    event2 = create_event(title='event2')
    event1.contributions.append(dummy_contribution)

    class Schema(mm.SQLAlchemyAutoSchema):
        contrib = ModelField(Contribution, with_parent='event')

    ctx = {'event': event1}
    assert Schema(context=ctx).load({'contrib': dummy_contribution.id})['contrib'].id == dummy_contribution.id

    ctx['event'] = event2
    with pytest.raises(ValidationError):
        Schema(context=ctx).load({'contrib': dummy_contribution.id})['contrib']


def test_ModelField_serialize(dummy_user):
    obj = type('Test', (), {
        'user': dummy_user
    })

    field = ModelField(User)
    assert field.serialize('user', obj) == dummy_user.id

    field = ModelField(User, column='first_name')
    assert field.serialize('user', obj) == dummy_user.first_name


def test_ModelList_deserialize(dummy_user, dummy_contribution, create_event):
    field = ModelList(User)
    assert field.deserialize([dummy_user.id])[0].id == dummy_user.id

    field = ModelList(User, collection_class=set)
    assert isinstance(field.deserialize([dummy_user.id]), set)

    field = ModelList(User, column='first_name')
    assert field.deserialize([dummy_user.first_name])[0].id == dummy_user.id

    dummy_user.is_deleted = True
    field = ModelList(User, filter_deleted=True)
    with pytest.raises(ValidationError):
        field.deserialize([dummy_user.id])

    field = ModelList(User, get_query=lambda m, _: m.query.filter_by(first_name=dummy_user.first_name))
    assert field.deserialize([dummy_user.id])[0].id == dummy_user.id

    field = ModelList(User, get_query=lambda m, _: m.query.filter_by(first_name='Fake'))
    with pytest.raises(ValidationError):
        field.deserialize([dummy_user.id])

    event1 = create_event(title='event1')
    event2 = create_event(title='event2')
    event1.contributions.append(dummy_contribution)

    class Schema(mm.SQLAlchemyAutoSchema):
        contribs = ModelList(Contribution, with_parent='event')

    ctx = {'event': event1}
    assert Schema(context=ctx).load({'contribs': [dummy_contribution.id]})['contribs'][0].id == dummy_contribution.id

    ctx['event'] = event2
    with pytest.raises(ValidationError):
        Schema(context=ctx).load({'contribs': [dummy_contribution.id]})['contribs']


def test_ModelList_serialize(dummy_user):
    obj = type('Test', (), {
        'users': [dummy_user, dummy_user]
    })

    field = ModelList(User)
    serialized = field.serialize('users', obj)
    assert len(serialized) == 2
    assert serialized[0] == dummy_user.id

    field = ModelList(User, column='first_name')
    assert field.serialize('users', obj)[0] == dummy_user.first_name
