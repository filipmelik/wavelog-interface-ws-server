# Simple Websocket server for use with Wavelog hardware interface
# (see https://github.com/filipmelik/wavelog-trx-interface)
import os
import logging
from typing import Annotated

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, status
from websockets.exceptions import ConnectionClosed
from fastapi.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from mode_from_qrg_resolver import get_mode_from_qrg, QRGLookupTableDoesNotExist, QRGLookupTableInvalid, \
    QRGLookupTableFetchFailed

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
]

qrg_table_cache = {}  # intentionally defined in global scope to preserve it in memory forever

async def qrg_table_cache_dependency():
    return qrg_table_cache

app = FastAPI(middleware=middleware)

@app.get("/cmd/{device_id}/qsy/{qrg}")
async def trigger_qsy(device_id: str, qrg: int):
    """
    GET endpoint, that will send QSY frequency request to the connected
    websocket client running in Wavelog hardware interface.
    """
    client_socket = app.wss.get(device_id)
    if not client_socket:
        raise HTTPException(
            status_code=404,
            detail=f"no device with id {device_id} is connected",
        )
    
    try:
        response = {
            "command": "qsy",
            "params": {
                "frequency": qrg,
            }
        }
        await client_socket.send_json(response)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=f"something bad happened while sending data to client :(",
        )
    
    app.logger.info(f"Sending QSY to {qrg} on device {device_id}")
    return {
        "device_id": device_id,
        "qrg": qrg,
        "result": "success"
    }


@app.get("/cmd/{device_id}/qsy-with-mode/{qrg_lookup_table_name}/{qrg}")
async def trigger_qsy_with_mode(
        qrg_table_cache: Annotated[dict, Depends(qrg_table_cache_dependency)],
        device_id: str,
        qrg_lookup_table_name: str,
        qrg: int,
):
    """
    GET endpoint, that will send QSY frequency request along with the mode
    change request to the connected websocket client running in Wavelog hardware
    interface. The mode is derived from frequency-to-mode lookup table
    referenced in API request parameter qrg_lookup_table_name.
    """
    try:
        resolved_mode = get_mode_from_qrg(
            logger=app.logger,
            qrg_table_cache=qrg_table_cache,
            qrg_lookup_table_name=qrg_lookup_table_name,
            qrg=qrg,
        )
    
    except (QRGLookupTableDoesNotExist, QRGLookupTableInvalid, QRGLookupTableFetchFailed) as e:
        raise HTTPException(
            status_code=404,
            detail=f"error: {str(e)}",
        )
    except Exception as e:
        app.logger.exception(f"unexpected error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail="unexpected error. check logs",
        )
    
    client_socket = app.wss.get(device_id)
    if not client_socket:
        raise HTTPException(
            status_code=404,
            detail=f"no device with id {device_id} is connected",
        )
    
    try:
        response = {
            "command": "qsy_with_mode",
            "params": {
                "frequency": qrg,
                "mode": resolved_mode,
            }
        }
        await client_socket.send_json(response)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=f"something bad happened while sending data to client :(",
        )
    
    app.logger.info(f"Sending QSY+MODE to {qrg} {resolved_mode} on device {device_id}")
    return {
        "device_id": device_id,
        "qrg": qrg,
        "mode": resolved_mode,
        "result": "success"
    }

@app.get("/cmd/flush_qrg_tables_cache")
async def flush_qrg_table_cache(admin_password: str):
    """
    GET endpoint, that flushes cache with QRG mapping tables
    """
    if admin_password !=  os.getenv("ADMIN_PASS"):
        raise HTTPException(
            status_code=403,
            detail=f"bad password",
        )
    
    global qrg_table_cache
    qrg_table_cache = {}
    
    app.logger.info("QRG table cache was flushed")
    return {
        "message": "qrg table cache was flushed",
        "result": "success"
    }
    
@app.websocket('/ws/connect-device/{device_id}')
async def device_connect_endpoint(
    *,
    websocket: WebSocket,
    device_id: str,
):
    try:
        await websocket.accept()
        
        if device_id in app.wss.keys():
            await websocket.close(code=status.WS_1001_GOING_AWAY)
            app.logger.info("Client {} already exists.".format(device_id))
            return
        
        app.logger.info("New websocket client connected: {}".format(device_id))
        app.wss[device_id] = websocket # store the websocket in the app's state
        
        while True:
            # echo what is received (for debug purposes since the wavelog
            # hardware interface normally just listen for data sent from server)
            received_text = await websocket.receive_text()
            echo_response = {"received": received_text, "device_id": device_id}
            await websocket.send_json(echo_response)
            
    except (WebSocketDisconnect, ConnectionClosed):
        app.logger.info("Device with ID {} disconnected".format(device_id))
        app.wss.pop(device_id, None)


@app.on_event("startup")
async def startup():
    app.wss = {}

    app.logger = logging.getLogger('wavelog_hw_iface_server')
    log_level = logging.DEBUG if os.getenv("DEBUG", "0") == "1" else logging.INFO
    app.logger.setLevel(log_level)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter('%(levelname)s - [%(asctime)s]: %(message)s')
    ch.setFormatter(formatter)
    app.logger.addHandler(ch)

    app.logger.info("Wavelog hardware interface websocket server has started.")

@app.on_event("shutdown")
async def shutdown():
    for _, ws in app.wss.items():
       await ws.close()

    app.logger.info("Server stopped.")