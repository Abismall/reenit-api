from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, PickleType
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from app.database import Base


class Scrim(Base):
    __tablename__ = "scrims"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False, unique=True)
    public = Column(Boolean, server_default='TRUE', nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    owner_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, unique=True)

    owner = relationship("User")
    team_one = Column(MutableList.as_mutable(PickleType),
                      default=[])
    team_two = Column(MutableList.as_mutable(PickleType),
                      default=[])


class Active(Base):
    __tablename__ = "active users"
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    username = Column(String, nullable=False)
    steam64 = Column(Integer, nullable=False)
    title = Column(String, ForeignKey(
        "scrims.title", ondelete="CASCADE"), nullable=False, primary_key=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    steam64 = Column(Integer, unique=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(200))
    public = Column(Boolean, server_default='True')
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text('now()'))


class Server(Base):
    __tablename__ = "servers"
    id = Column(String, primary_key=True, nullable=False)
    match_id = Column(Integer, unique=True)
    location = Column(String(100), nullable=False)
    active = Column(Boolean, server_default='False', nullable=False)
    players = Column(MutableList.as_mutable(PickleType),
                     default=[])


class Location(Base):
    __tablename__ = "locations"
    id = Column(String, primary_key=True, nullable=False)
    location = Column(String(100), nullable=False)
    active = Column(Boolean, server_default='False', nullable=False)
