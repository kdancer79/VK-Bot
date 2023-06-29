import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from config import db_url_object

metadata = MetaData()
Base = declarative_base()

engine = create_engine(db_url_object)


class Viewed(Base):
    __tablename__ = 'views'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)


def add_user(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        viewed = Viewed(profile_id=profile_id, worksheet_id=worksheet_id)
        session.add(viewed)
        session.commit()


def check_user(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        user = session.query(Viewed).filter_by(profile_id=profile_id, worksheet_id=worksheet_id).first()
        if user:
            return True
        else:
            return False


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    res = check_user(engine, 2113, 654623)
    print(res)
