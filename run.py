import os
import uvicorn

log_level = "debug" if os.getenv("DEBUG", "0") == "1" else "info"

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=log_level,
        ws="websockets",
        ws_ping_interval=10,
        ws_ping_timeout=10,
    )