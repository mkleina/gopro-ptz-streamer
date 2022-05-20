from distutils.log import debug
import RPi.GPIO as GPIO
from server import api

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, ws_ping_interval=1, ws_ping_timeout=3, host="0.0.0.0", port=8080)    
