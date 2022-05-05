from sqlalchemy import Column, Integer, String, Boolean, BigInteger, ForeignKey, PickleType
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from app.database import Base


class Scrim(Base):
    __tablename__ = "open_scrims"

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
    captain_one = Column(String, nullable=True, default=None)
    captain_two = Column(String, nullable=True, default=None)
    current_map = Column(String, nullable=True, default=None)
    overtime = Column(Boolean, nullable=True, default=False)
    team_damage = Column(Boolean, nullable=True, default=True)
    server_id = Column(String, nullable=True)


class Active(Base):
    __tablename__ = "active_users"
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    scrim_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    steam64 = Column(BigInteger, nullable=False)
    title = Column(String, ForeignKey(
        "open_scrims.title", ondelete="CASCADE"), nullable=False, primary_key=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    steam64 = Column(BigInteger, unique=True, nullable=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(200))
    public = Column(Boolean, server_default='True')
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=text('now()'))


class Server(Base):
    __tablename__ = "active_servers"
    id = Column(Integer, primary_key=True, nullable=False)
    server_id = Column(String, unique=True)
    location = Column(String(100), nullable=False)
    active = Column(Boolean, server_default='False', nullable=False)
    players = Column(MutableList.as_mutable(PickleType),
                     default=[])


# class Location(Base):
#     __tablename__ = "locations"
#     id = Column(String, primary_key=True, nullable=False)
#     location = Column(String(100), nullable=False)
#     active = Column(Boolean, server_default='False', nullable=False)
