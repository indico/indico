from argparse import ArgumentParser
from pprint import pprint

from flask import Flask
from ZODB import DB, FileStorage

from indico.core.db import db
from indico.modules.rb.models import *


def setup(zodb_path, sqlalchemy_uri):
    app = Flask('migration')
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_uri
    db.init_app(app)

    zodb = DB(FileStorage.FileStorage(zodb_path))
    root = zodb.open().root()

    return root, app


def teardown():
    pass


def convert_repeatibility(old):
    return [(RepeatUnit.DAY, 1),
            (RepeatUnit.WEEK, 1),
            (RepeatUnit.WEEK, 2),
            (RepeatUnit.WEEK, 3),
            (RepeatUnit.MONTH, 1),
            (RepeatUnit.NEVER, 0)][
            [0, 1, 2, 3, 4, None].index(old)]


def migrate(root):
    pprint(root.keys())

    for old_location in root['RoomBookingLocationList']:
        print old_location.friendlyName
        l = Location(
            name=old_location.friendlyName,
            support_emails=old_location._avcSupportEmails,
        )

        for old_aspect_id, old_aspect in old_location._aspects.iteritems():
            pass

        db.session.add(l)
    db.session.commit()  # commit locations + aspects

    for old_room_id, old_room in root['Rooms'].iteritems():
        pass

    for k, v in root['Reservations'].iteritems():
        repeat_unit, repeat_step = convert_repeatibility(v.repeatability)

        r = Reservation(
            id=v.id,
            booked_for_id=v.bookedForId,
            booked_for_name=v.bookedForName,
            contact_email=v.contactEmail,
            contact_phone=v.contactPhone,
            created_by=v.createdBy,
            is_cancelled=v.isCancelled,
            is_confirmed=v.isConfirmed,
            is_rejected=v.isRejected,
            reason=v.reason,
            repeat_unit=repeat_unit,
            repeat_step=repeat_step
        )

        db.session.add(r)
    db.session.commit()

def main():
    root, app = setup('data.fs', 'sqlite:///data.db')
    with app.app_context():
        db.create_all()
        migrate(root)

if __name__ == '__main__':
    main()
