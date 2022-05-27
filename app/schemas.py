from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class RegisterUser(BaseModel):
    username: str
    password: str


class UpdateUser(BaseModel):
    username: Optional[str]
    password: Optional[str]
    public_state: Optional[bool]
    steam64: Optional[str]
    profile_list: Optional[list]


class UserQuery(BaseModel):
    team: Optional[int]


class UserOut(BaseModel):
    id: Optional[int]
    username: Optional[str]
    steam64: Optional[str]
    public_state: Optional[bool]
    profile_list: Optional[list]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class Steam64(BaseModel):
    profileUrl: Any


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
    active: Optional[bool]
    title: Optional[str]
    public_state: Optional[bool]
    team_one: Optional[list]
    team_two: Optional[list]
    lobby: Optional[list]
    captain_one: Optional[str]
    captain_two: Optional[str]
    current_map: Optional[str]
    overtime: Optional[bool]
    team_damage: Optional[bool]
    history: Optional[list]
    server_address: Optional[Any]
    server_id: Optional[str]


class PostScrim(BaseModel):
    title: str


class Server(BaseModel):
    active: Optional[bool]
    location: Optional[str]
    id: Optional[str]
    server_id: Optional[str]
    players: Optional[list]
