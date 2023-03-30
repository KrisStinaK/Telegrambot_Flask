import sqlalchemy
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import datetime


from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    position = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    cost = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.String, nullable=True, default=datetime.datetime.now())
