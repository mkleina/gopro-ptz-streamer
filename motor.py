import RPi.GPIO as GPIO
from threading import Thread, Condition
import time

MOTOR_X_PINS = [11, 13, 15, 19]
MOTOR_Y_PINS = [35, 33, 31, 29]

class Motor:
    FORWARD = 1
    BACKWARD = -1
    SPEED = 0.0015
    state = Condition()

    def __init__(self, pins):
        self.pin_order = self.pins = pins

        # Setup motor
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)

        # Setup thread
        self.state = Condition()
        self.paused = True
        self.thread = Thread(target=self.__spin)
        self.thread.start()
    
    def __del__(self):
        GPIO.cleanup()

    def __spin(self):
        while True:
            with self.state:
                if self.paused:
                    self.state.wait()

            for i, pin in enumerate(self.pin_order):
                # Enable next pin
                GPIO.output(pin, GPIO.HIGH)

                time.sleep(Motor.SPEED)

                # Disable previous pin
                if i == 0:
                    GPIO.output(
                        self.pin_order[len(self.pin_order)-1], GPIO.LOW)
                else:
                    GPIO.output(self.pin_order[i-1], GPIO.LOW)

                time.sleep(Motor.SPEED)

    def start(self, direction):
        self.stop()

        self.pin_order = self.pins
        if direction == Motor.BACKWARD:
            self.pin_order = list(reversed(self.pins))

        with self.state:
            self.paused = False
            self.state.notify()

    def stop(self):
        with self.state:
            self.paused = True