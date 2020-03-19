"""
Mock PiCar module for Windows development
Bu modul Windows'ta gelistirme yapmak icin sahte picar kütüphanesi saglar
"""
import logging

def setup():
    """PiCar setup function mock"""
    logging.info("Mock PiCar setup() called - Windows development mode")

class Servo:
    class Servo:
        def __init__(self, pin):
            self.pin = pin
            self.offset = 0
            logging.debug("Mock Servo {} initialized".format(pin))
            
        def write(self, angle):
            logging.debug("Mock Servo {}: Setting angle to {}".format(self.pin, angle))

class back_wheels:
    class Back_Wheels:
        def __init__(self):
            self._speed = 0
            logging.debug("Mock Back_Wheels initialized")
            
        @property
        def speed(self):
            return self._speed
            
        @speed.setter
        def speed(self, value):
            self._speed = value
            logging.debug("Mock Back_Wheels: Setting speed to {}".format(value))

class front_wheels:
    class Front_Wheels:
        def __init__(self):
            self.turning_offset = 0
            logging.debug("Mock Front_Wheels initialized")
            
        def turn(self, angle):
            logging.debug("Mock Front_Wheels: Turning to angle {}".format(angle)) 