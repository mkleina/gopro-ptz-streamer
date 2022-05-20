from motor import Motor, MOTOR_X_PINS, MOTOR_Y_PINS
import json
import asyncio
import os
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.logger import logger
from camera import CameraStream
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BUZZER_PIN = 23

api = FastAPI(debug=True)
        
# Sound on API startup
@api.on_event("startup")
async def startup_event():
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    buzz(5, 0.02)

class Controller:
    motor_x = Motor(MOTOR_X_PINS)
    motor_y = Motor(MOTOR_Y_PINS)
    camera_stream = CameraStream(-1)
    
    def get_motor(self, axis) -> Motor:
       return (self.motor_x if axis.lower() == 'x' else self.motor_y) 

    def stop_motors(self):
        self.motor_x.stop()
        self.motor_y.stop()
        
    async def stream(self):
        buzz(1, 0.05)
        try:
            async for frame in self.camera_stream:
                yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        except asyncio.CancelledError:
            logger.info("client stopped video stream")
        finally:
            buzz(2, 0.05)

# Initialize global controller
controller = Controller()
        
# Handle websock messages
@api.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data_str = await websocket.receive_text()
            logger.debug("got data:", data_str)
            data = json.loads(data_str)
            
            resp = {
                'command': data['command'],
                'ok': True
            }

            if data['command'] == 'start':
                controller.get_motor(data['axis']).start(data['direction'])
            elif data['command'] == 'stop':
                controller.get_motor(data['axis']).stop()
            elif data['command'] == 'set_quality':
                controller.camera_stream.set_quality(data['value'])
            elif data['command'] == 'get_quality':
                resp['value'] = controller.camera_stream.get_quality()
            else:
                resp['ok'] = False

            await websocket.send_json(resp)
    except WebSocketDisconnect:
        controller.stop_motors()
        logger.info("client disconnected from websock server")

# Handle video feed endpoint
@api.get("/video")
async def video_endpoint():
    return StreamingResponse(controller.stream(), media_type="multipart/x-mixed-replace;boundary=frame")

api.mount("/", StaticFiles(directory=ROOT_DIR+"/static", html=True), name="static")

# Emit sound from the buzzer
def buzz(count, delay):
    for i in range(count):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(delay)