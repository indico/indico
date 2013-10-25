from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

from indico.core.db.schema import Base
from indico.core.db.schema.rb import (aspect, blocked_room, blocking,
                                      blocking_principal, edit, interval,
                                      location, photo, reservation, room, trait)


def main():
    engine = create_engine('sqlite:///test.db', echo=True)
    Base.metadata.create_all(engine, checkfirst=True)
    # Session = sessionmaker(bind=engine)
    # session = Session()
    print 'everything is fine for now!'

if __name__ == '__main__':
    main()
