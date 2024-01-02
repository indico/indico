# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.events.persons import logger
from indico.modules.logs import EventLogRealm, LogKind


def update_person(person, data):
    person.populate_from_dict(data)
    db.session.flush()
    signals.event.person_updated.send(person)
    logger.info('Person %s updated by %s', person, session.user)
    person.event.log(EventLogRealm.management, LogKind.change, 'Persons',
                     f"Person with email '{person.email}' has been updated", session.user)
