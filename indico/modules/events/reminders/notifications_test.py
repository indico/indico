# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import textwrap
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.modules.events.reminders.models.reminders import ReminderType
from indico.modules.events.reminders.util import get_reminder_email_tpl
from indico.testing.util import assert_email_snapshot
from indico.util.string import RichMarkup
from indico.web.flask.templating import get_template_module


@pytest.mark.parametrize(('with_label', 'venue', 'room', 'address', 'snapshot_filename'), (
    (True, '', '', '', 'event_reminder_label.txt'),
    (False, '', '', '', 'event_reminder.txt'),
    (False, 'Home', '', '', 'event_reminder_v.txt'),
    (False, '', 'Bed', '', 'event_reminder_r.txt'),
    (False, '', '', 'Some\nWhere', 'event_reminder_a.txt'),
    (False, 'Home', 'Bed', '', 'event_reminder_vr.txt'),
    (False, '', 'Bed', 'Some\nWhere', 'event_reminder_ra.txt'),
    (False, 'Home', '', 'Some\nWhere', 'event_reminder_va.txt'),
    (False, 'Home', 'Bed', 'Some\nWhere', 'event_reminder_vra.txt'),
))
def test_event_reminder_email_plaintext(snapshot, create_contribution, create_timetable_entry, create_event,
                                        create_label, with_label, venue, room, address, snapshot_filename):
    event = create_event(start_dt=datetime(2022, 11, 11, 13, 37),
                         end_dt=datetime(2022, 11, 11, 23, 37), title='Baking with Cats')
    event.venue_name = venue
    event.room_name = room
    event.address = address
    c1 = create_contribution(event, 'Kneading Dough', timedelta(minutes=23))
    c2 = create_contribution(event, 'Pure Bread Cats', timedelta(minutes=40))
    create_timetable_entry(event, c1, datetime(2022, 11, 11, 13, 37))
    create_timetable_entry(event, c2, datetime(2022, 11, 11, 15, 50))
    if with_label:
        label = create_label('POSTPONED')
        event.label = label
    agenda = event.timetable_entries.filter_by(parent_id=None).all()
    template = get_template_module('events/reminders/emails/event_reminder.txt',
                                   event=event, url='http://localhost/', with_description=True,
                                   note='Meow.\nNyah!', with_agenda=True, agenda=agenda)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    assert_email_snapshot(snapshot, template, snapshot_filename)


@pytest.mark.parametrize(('with_label', 'venue', 'room', 'address', 'snapshot_filename'), (
    (True, '', '', '', 'event_reminder_label.html'),
    (False, '', '', '', 'event_reminder.html'),
    (False, 'Home', '', '', 'event_reminder_v.html'),
    (False, '', 'Bed', '', 'event_reminder_r.html'),
    (False, '', '', 'Some\nWhere', 'event_reminder_a.html'),
    (False, 'Home', 'Bed', '', 'event_reminder_vr.html'),
    (False, '', 'Bed', 'Some\nWhere', 'event_reminder_ra.html'),
    (False, 'Home', '', 'Some\nWhere', 'event_reminder_va.html'),
    (False, 'Home', 'Bed', 'Some\nWhere', 'event_reminder_vra.html'),
))
def test_event_reminder_email_html(snapshot, create_contribution, create_timetable_entry, create_event,
                                   create_label, with_label, venue, room, address, snapshot_filename):
    event = create_event(start_dt=datetime(2022, 11, 11, 13, 37),
                         end_dt=datetime(2022, 11, 11, 23, 37), title='Baking with Cats')
    event.venue_name = venue
    event.room_name = room
    event.address = address
    c1 = create_contribution(event, 'Kneading Dough', timedelta(minutes=23))
    c2 = create_contribution(event, 'Pure Bread Cats', timedelta(minutes=40))
    create_timetable_entry(event, c1, datetime(2022, 11, 11, 13, 37))
    create_timetable_entry(event, c2, datetime(2022, 11, 11, 15, 50))
    if with_label:
        label = create_label('POSTPONED')
        event.label = label
    agenda = event.timetable_entries.filter_by(parent_id=None).all()
    template = get_template_module('events/reminders/emails/event_reminder.html',
                                   event=event, url='http://localhost/', with_description=True,
                                   note=RichMarkup('<p>Meow.</p><p>Nyah!</p>'), with_agenda=True, agenda=agenda)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    assert_email_snapshot(snapshot, template, snapshot_filename, html=True)


def test_event_reminder_email_plaintext_from_html(snapshot, create_event):
    event = create_event(start_dt=datetime(2025, 8, 8, 18, 18),
                         end_dt=datetime(2025, 8, 8, 19, 19),
                         title='Baking Cats',
                         url_shortcut='nyan')
    note = RichMarkup(textwrap.dedent('''
        <p><a href="https://www.nyan.cat/">Nyan Nyan <strong>Nyan!</strong></a></p>

        <table>
            <tr><th>Animal</th><th>Cuteness</th></tr>
            <tr><td>Kitten</td><td>OVER 9000</td></tr>
            <tr><td>Molerat</td><td>WTF</td></tr>
        </table>
    ''').strip())
    html_tpl, text_tpl = get_reminder_email_tpl(event, ReminderType.standard, RenderMode.html, False, False, None, note)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    assert_email_snapshot(snapshot, text_tpl, 'event_reminder_htmlconv.txt')
    assert_email_snapshot(snapshot, html_tpl, 'event_reminder_htmlconv.html', html=True)
