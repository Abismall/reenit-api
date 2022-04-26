from pydantic import BaseModel
from typing import Optional


class RegisterUser(BaseModel):
    steam64: int
    username: str
    password: str


class UpdateUser(BaseModel):
    username: Optional[str]
    password: Optional[str]
    public: Optional[bool]
    steam64: Optional[int]


class UserQuery(BaseModel):
    username: Optional[str]


class UserOut(BaseModel):
    id: Optional[int]
    username: Optional[str]
    #steam64: Optional[int]
    public: Optional[bool]

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    token: str
    token_type: str


class TokenData(BaseModel):
    id: str


class Scrim(BaseModel):
    id: Optional[int]
    action: Optional[int]
    title: Optional[str]
    public: Optional[bool]
    team_one: Optional[list]
    team_two: Optional[list]
    lobby: Optional[list]
    captain_one: Optional[str]
    captain_two: Optional[str]
    current_map: Optional[str]
    overtime: Optional[bool]
    team_damage: Optional[bool]
    server_id: Optional[str]


class PostScrim(BaseModel):
    title: str


class Server(BaseModel):
    active: Optional[bool]
    location: Optional[str]
    id: Optional[str]
    server_id: Optional[str]
    players: Optional[list]
