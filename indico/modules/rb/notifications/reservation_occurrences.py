from datetime import date

from flask import render_template

from indico.core.config import Config
from indico.modules.rb.models.reservations import RepeatUnit


def upcoming_occurrence(occurrence):
    if occurrence.start.date() < date.today():
        raise ValueError('This reservation occurrence started in the past')

    owner = occurrence.reservation.booked_for_user
    if owner is None:
        return

    from_addr = Config.getInstance().getNoReplyEmail()
    to = owner.getEmail()
    subject = 'Reservation reminder'
    text = render_template('rb/upcoming_occurrence.txt',
                           occurrence=occurrence,
                           owner=owner,
                           RepeatUnit=RepeatUnit)

    return {
        'fromAddr': from_addr,
        'toList': [to],
        'subject': subject,
        'body': text
    }
