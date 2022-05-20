import json
from io import BytesIO
import ftplib
from passlib.context import CryptContext
import requests
from app.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def remove_keys(dathost_dict):
    output_keys = ["id", "name", "user_data", "location", "players_online",
                   "status", "booting", "server_error", "ip", "raw_ip", "match_id", "on", "ports"]
    output = []
    for server in dathost_dict:
        sanitized_dict = {k: v for k, v in server.items() if k in output_keys}
        output.append(sanitized_dict)
    return output


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


def gather_steam64(current):
    team_one = []
    team_two = []
    for user in current:
        if user["team"] == 1:
            team_one.append(str(user["steam64"]))
        elif user["team"] == 2:

            team_two.append(str(user["steam64"]))
    return team_one, team_two


def create_config_file(map_list, match_id, team1_steamIDs, team2_steamIDs, captain1, captain2):
    match_config = {
        'matchid': str(match_id),
        'num_maps': 1,
        'maplist': map_list,
        'skip_veto': True,
        'veto_first': 'team1',
        'side_type': 'always_knife',
        'players_per_team': 5,
        'min_players_to_ready': 1,
        'team1': {
            'name': f"{captain1} & kopla",
            'flag': "Fi",
            'players': team1_steamIDs
        },
        'team2': {
            'name': f"{captain2} & kopla",
            'flag': "Fi",
            'players': team2_steamIDs
        },
        'cvars': {
            'get5_event_api_url': f"http://13.53.34.176:8000/servers/status/",


        },
    }
    config_encode_data = json.dumps(match_config, indent=2).encode('utf-8')
    configs_bytes = BytesIO(config_encode_data)
    return configs_bytes


def send_config_file(configs, host, ftp_user, ftp_password):
    try:
        with ftplib.FTP(host, ftp_user, ftp_password, timeout=30) as ftp:
            ftp.login
            print(ftp)
            ftp.storbinary('STOR reenit_match_configs.json', configs)
            return True
    except ftplib.all_errors as err:
        print(f"ftp error: {err}")
        return False
