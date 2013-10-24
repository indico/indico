from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

from indico.core.db.schema import Base


def main():
    engine = create_engine('sqlite:///test.db')
    Base.metadata.create_all(engine)
    # Session = sessionmaker(bind=engine)
    # session = Session()
    print 'everything is fine for now!'

if __name__ == '__main__':
    main()
