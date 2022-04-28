from passlib.context import CryptContext
import requests
from app.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_servers():
    try:
        with requests.get("https://dathost.net/api/0.1/game-servers", auth=(settings.dathost_username,  settings.dathost_password)) as api_call:
            return api_call
    except requests.exceptions.RequestException as err:
        print(f"Requests error: {err}")
    except requests.exceptions.HTTPError as err:
        print(f"Requests error: {err}")


def start_server(server_id):
    try:
        with requests.post(f"https://dathost.net/api/0.1/game-servers/{server_id}/start", auth=(settings.dathost_username, settings.dathost_password)) as api_call:
            return api_call
    except requests.exceptions.RequestException as err:
        print(f"Requests error: {err}")
        return None
    except requests.exceptions.HTTPError as err:
        print(f"Requests error: {err}")
        return None


def server_details(server_id):
    try:
        with requests.get(f"https://dathost.net/api/0.1/game-servers/{server_id}", auth=(settings.dathost_username, settings.dathost_password)) as api_call:
            return api_call
    except requests.exceptions.RequestException as err:
        print(f"Requests error: {err}")
        return None
    except requests.exceptions.HTTPError as err:
        print(f"Requests error: {err}")
        return None
