# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.events.logs import EventLogKind, EventLogRealm
from indico.modules.events.persons import logger


def update_person(person, data):
    person.populate_from_dict(data)
    db.session.flush()
    signals.event.person_updated.send(person)
    logger.info('Person %s updated by %s', person, session.user)
    person.event.log(EventLogRealm.management, EventLogKind.change, 'Persons',
                     "Person with email '{}' has been updated".format(person.email), session.user)
