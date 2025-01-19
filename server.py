# Simple Websocket server for use wih Wavelog hardware interface
import os
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, status
from websockets.exceptions import ConnectionClosed
from fastapi.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
]

app = FastAPI(middleware=middleware)

@app.get("/cmd/{device_id}/qsy/{qrg}")
async def trigger_qsy(device_id: str, qrg: int):
    """GET endpoint, that will send QSY frequency to the connected websocket client"""
    client_socket = app.wss.get(device_id)
    if not client_socket:
        raise HTTPException(
            status_code=404,
            detail=f"no device with id {device_id} is connected",
        )
    
    response = {
        "command": "qsy",
        "params": {
            "frequency": qrg,
        }
    }
    try:
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