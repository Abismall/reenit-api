from fastapi import HTTPException, status, APIRouter
from .. utils import get_servers, start_server, server_details, remove_keys
router = APIRouter(
    prefix="/dathost",
    tags=['Dathost']
)


@router.post("/start/", status_code=status.HTTP_201_CREATED)
async def start_dathost_server(server_id: str):
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


@router.get("/details/", status_code=status.HTTP_200_OK)
async def dathost_server_details(server_id: str):
    details = server_details(server_id)
    if details.status_code == status.HTTP_200_OK:
        return details.json()
    if details.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
