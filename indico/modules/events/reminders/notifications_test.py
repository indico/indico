# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta
from pathlib import Path

from indico.web.flask.templating import get_template_module


pytest_plugins = 'indico.modules.events.timetable.testing.fixtures'


def test_event_reminder_email_plaintext(snapshot, create_contribution, create_entry, create_event):
    event = create_event(start_dt=datetime(2022, 11, 11, 13, 37),
                         end_dt=datetime(2022, 11, 11, 23, 37), title='Baking with Cats')
    c1 = create_contribution(event, 'Kneading Dough', timedelta(minutes=23))
    c2 = create_contribution(event, 'Pure Bread Cats', timedelta(minutes=40))
    create_entry(c1, datetime(2022, 11, 11, 13, 37))
    create_entry(c2, datetime(2022, 11, 11, 15, 50))
    agenda = event.timetable_entries.filter_by(parent_id=None).all()
    template = get_template_module('events/reminders/emails/event_reminder.txt',
                                   event=event, url='http://localhost/', with_description=True,
                                   note='Meow.\nNyah!', with_agenda=True, agenda=agenda)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), 'event_reminder.txt')
