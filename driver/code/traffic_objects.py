import logging
import time


class TrafficObject(object):
    """Base class for all traffic objects"""
    
    def __init__(self):
        pass
    
    def set_car_state(self, car_state):
        """Set car state based on this traffic object"""
        pass
    
    @staticmethod
    def is_close_by(detected_obj, frame_height, min_height_pct=0.05):
        """
        Check if detected object is close enough to take action
        Args:
            detected_obj: Object with bounding_box attribute [(x1,y1), (x2,y2)]
            frame_height: Height of the frame in pixels
            min_height_pct: Minimum height percentage to consider "close"
        """
        if not hasattr(detected_obj, 'bounding_box'):
            return False
            
        obj_height = detected_obj.bounding_box[1][1] - detected_obj.bounding_box[0][1]
        height_percentage = obj_height / float(frame_height)
        
        is_close = height_percentage >= min_height_pct
        logging.debug("Object height: %dpx (%.1f%%) - Close: %s" % 
                     (obj_height, height_percentage * 100, is_close))
        return is_close


class RedTrafficLight(TrafficObject):
    """Red traffic light - stops the car"""
    
    def __init__(self):
        super(RedTrafficLight, self).__init__()
        logging.debug("RedTrafficLight created")
    
    def set_car_state(self, car_state):
        logging.info("🔴 RED LIGHT: Stopping car")
        car_state['speed'] = 0


class GreenTrafficLight(TrafficObject):
    """Green traffic light - allows normal driving"""
    
    def __init__(self):
        super(GreenTrafficLight, self).__init__()
        logging.debug("GreenTrafficLight created")
    
    def set_car_state(self, car_state):
        logging.info("🟢 GREEN LIGHT: Continue driving")
        # Green light doesn't change speed - car continues as normal


class Person(TrafficObject):
    """Person detected - stops the car for safety"""
    
    def __init__(self):
        super(Person, self).__init__()
        logging.debug("Person detector created")
    
    def set_car_state(self, car_state):
        logging.info("👤 PERSON DETECTED: Emergency stop!")
        car_state['speed'] = 0


class SpeedLimit(TrafficObject):
    """Speed limit sign - changes speed limit"""
    
    def __init__(self, speed_limit):
        super(SpeedLimit, self).__init__()
        self.speed_limit = speed_limit
        logging.debug("SpeedLimit(%d) created" % speed_limit)
    
    def set_car_state(self, car_state):
        logging.info("🚦 SPEED LIMIT %d: Adjusting speed" % self.speed_limit)
        car_state['speed_limit'] = self.speed_limit
        
        # If current speed is higher than new limit, reduce it
        if car_state['speed'] > self.speed_limit:
            car_state['speed'] = self.speed_limit


class StopSign(TrafficObject):
    """Stop sign - stops car and waits for specified time"""
    
    def __init__(self, wait_time_in_sec=2):
        super(StopSign, self).__init__()
        self.wait_time_in_sec = wait_time_in_sec
        self.start_wait_time = None
        self.in_wait_mode = False
        logging.debug("StopSign created (wait time: %ds)" % wait_time_in_sec)
    
    def set_car_state(self, car_state):
        current_time = time.time()
        
        if not self.in_wait_mode:
            # First time seeing stop sign
            logging.info("🛑 STOP SIGN: Starting %d second wait" % self.wait_time_in_sec)
            self.start_wait_time = current_time
            self.in_wait_mode = True
            car_state['speed'] = 0
            
        elif self.in_wait_mode:
            # Check if wait time is over
            elapsed_time = current_time - self.start_wait_time
            
            if elapsed_time < self.wait_time_in_sec:
                # Still waiting
                remaining = self.wait_time_in_sec - elapsed_time
                logging.debug("🛑 STOP SIGN: Still waiting (%.1fs remaining)" % remaining)
                car_state['speed'] = 0
            else:
                # Wait time is over
                logging.info("🛑 STOP SIGN: Wait complete, can proceed")
                self.in_wait_mode = False
                self.start_wait_time = None
                # Don't change speed here - let other systems handle acceleration
    
    def clear(self):
        """Clear stop sign state when no longer detected"""
        if self.in_wait_mode:
            logging.debug("🛑 STOP SIGN: Cleared from view")
        self.in_wait_mode = False
        self.start_wait_time = None 