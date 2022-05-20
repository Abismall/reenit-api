from fastapi import HTTPException, status, APIRouter
from .. utils import get_servers, start_server, server_details, remove_keys, create_config_file, send_config_file, gather_steam64
router = APIRouter(
    prefix="/dathost",
    tags=['Dathost']
)


@router.post("/start/{server_id}", status_code=status.HTTP_201_CREATED)
async def start_dathost_server(server_id: str, data: dict):
    details = server_details(server_id).json()
    team1_steamIDs, team2_steamIDs = gather_steam64(data["Players"])
    config = create_config_file([data["lobby"]["current_map"]], data["lobby"]["id"], team1_steamIDs,
                                team2_steamIDs, data["lobby"]["captain_one"], data["lobby"]["captain_two"])
    print(team2_steamIDs, team1_steamIDs)
    send_config_file(config, details["ip"], server_id, details["ftp_password"])
    server_call = start_server(server_id)
    if server_call.status_code == status.HTTP_200_OK:
        return
    if server_call.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if server_call.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/available/", status_code=status.HTTP_200_OK)
async def dathost_servers():
    available_servers = get_servers()
    if available_servers.status_code == status.HTTP_200_OK:
        output = remove_keys(available_servers.json())
        return output
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/details/{server_id}", status_code=status.HTTP_200_OK)
async def dathost_server_details(server_id: str):
    details = server_details(server_id)
    if details.status_code == status.HTTP_200_OK:
        return details.json()
    if details.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
