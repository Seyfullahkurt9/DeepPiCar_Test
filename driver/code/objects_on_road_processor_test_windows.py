import cv2
import logging
import datetime
import time
import numpy as np
from PIL import Image
from traffic_objects import *

_SHOW_IMAGE = False


class MockDetectedObject:
    """Mock object to simulate EdgeTPU detection results"""
    def __init__(self, label_id, score, bounding_box):
        self.label_id = label_id
        self.score = score
        self.bounding_box = bounding_box  # [(x1,y1), (x2,y2)]


class ObjectsOnRoadProcessorWindows(object):
    """
    Windows-compatible version of ObjectsOnRoadProcessor for testing
    Uses mock object detection instead of EdgeTPU
    """

    def __init__(self,
                 car=None,
                 speed_limit=40,
                 width=640,
                 height=480):
        logging.info('Creating a ObjectsOnRoadProcessorWindows (Mock Version)...')
        self.width = width
        self.height = height

        # initialize car
        self.car = car
        self.speed_limit = speed_limit
        self.speed = speed_limit

        # Mock labels (simplified version)
        self.labels = {
            0: 'Green Traffic Light',
            1: 'Person', 
            2: 'Red Traffic Light',
            3: 'Speed Limit 25',
            4: 'Speed Limit 40', 
            5: 'Stop Sign'
        }

        self.min_confidence = 0.30
        self.num_of_objects = 3
        logging.info('Mock Edge TPU initialized.')

        # initialize open cv for drawing boxes
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.bottomLeftCornerOfText = (10, height - 10)
        self.fontScale = 1
        self.fontColor = (255, 255, 255)  # white
        self.boxColor = (0, 0, 255)  # RED
        self.boxLineWidth = 1
        self.lineType = 2
        self.annotate_text = ""
        self.annotate_text_time = time.time()
        self.time_to_show_prediction = 1.0  # ms

        # Traffic objects
        self.traffic_objects = {0: GreenTrafficLight(),
                                1: Person(),
                                2: RedTrafficLight(),
                                3: SpeedLimit(25),
                                4: SpeedLimit(40),
                                5: StopSign()}

    def process_objects_on_road(self, frame):
        # Main entry point of the Road Object Handler
        logging.debug('Processing objects.................................')
        objects, final_frame = self.detect_objects(frame)
        self.control_car(objects)
        logging.debug('Processing objects END..............................')

        return final_frame

    def control_car(self, objects):
        logging.debug('Control car...')
        car_state = {"speed": self.speed_limit, "speed_limit": self.speed_limit}

        if len(objects) == 0:
            logging.debug('No objects detected, drive at speed limit of %s.' % self.speed_limit)

        contain_stop_sign = False
        for obj in objects:
            obj_label = self.labels[obj.label_id]
            processor = self.traffic_objects[obj.label_id]
            if processor.is_close_by(obj, self.height):
                processor.set_car_state(car_state)
                logging.info('[%s] object detected and is close by, taking action.' % obj_label)
            else:
                logging.debug("[%s] object detected, but it is too far, ignoring." % obj_label)
            if obj_label == 'Stop Sign':
                contain_stop_sign = True

        if not contain_stop_sign:
            self.traffic_objects[5].clear()

        self.resume_driving(car_state)

    def resume_driving(self, car_state):
        old_speed = self.speed
        self.speed_limit = car_state['speed_limit']
        self.speed = car_state['speed']

        if self.speed == 0:
            self.set_speed(0)
        else:
            self.set_speed(self.speed_limit)
        logging.info('Speed change: %d → %d' % (old_speed, self.speed))

        if self.speed == 0:
            logging.info('FULL STOP for 1 second')
            time.sleep(1)

    def set_speed(self, speed):
        # Use this setter, so we can test this class without a car attached
        self.speed = speed
        if self.car is not None:
            logging.debug("Actually setting car speed to %d" % speed)
            self.car.back_wheels.speed = speed

    def mock_detect_objects_from_filename(self, filename):
        """Mock object detection based on filename"""
        objects = []
        
        if 'red_light' in filename.lower():
            obj = MockDetectedObject(2, 0.95, [(200, 100), (300, 200)])  # Red light
            objects.append(obj)
        elif 'green_light' in filename.lower():
            obj = MockDetectedObject(0, 0.92, [(200, 100), (300, 200)])  # Green light
            objects.append(obj)
        elif 'person' in filename.lower():
            obj = MockDetectedObject(1, 0.88, [(150, 150), (250, 350)])  # Person
            objects.append(obj)
        elif 'stop' in filename.lower():
            obj = MockDetectedObject(5, 0.94, [(180, 120), (280, 220)])  # Stop sign
            objects.append(obj)
        elif 'limit_25' in filename.lower():
            obj = MockDetectedObject(3, 0.89, [(190, 110), (290, 210)])  # Speed limit 25
            objects.append(obj)
        elif 'limit_40' in filename.lower():
            obj = MockDetectedObject(4, 0.91, [(190, 110), (290, 210)])  # Speed limit 40
            objects.append(obj)
        # 'no_obj' will return empty list
        
        return objects

    def detect_objects(self, frame, filename="unknown"):
        logging.debug('Detecting objects (MOCK MODE)...')

        # Mock detection timing
        start_ms = time.time()
        
        # Get mock objects
        objects = self.mock_detect_objects_from_filename(filename)
        
        # Draw detection boxes and labels
        if objects:
            for obj in objects:
                height = obj.bounding_box[1][1] - obj.bounding_box[0][1]
                width = obj.bounding_box[1][0] - obj.bounding_box[0][0]
                logging.debug("%s, %.0f%% w=%.0f h=%.0f" % (self.labels[obj.label_id], obj.score * 100, width, height))
                
                box = obj.bounding_box
                coord_top_left = (int(box[0][0]), int(box[0][1]))
                coord_bottom_right = (int(box[1][0]), int(box[1][1]))
                cv2.rectangle(frame, coord_top_left, coord_bottom_right, self.boxColor, self.boxLineWidth)
                annotate_text = "%s %.0f%%" % (self.labels[obj.label_id], obj.score * 100)
                coord_top_left = (coord_top_left[0], coord_top_left[1] + 15)
                cv2.putText(frame, annotate_text, coord_top_left, self.font, self.fontScale, self.boxColor, self.lineType)
        else:
            logging.debug('No object detected')

        elapsed_ms = time.time() - start_ms
        if elapsed_ms > 0:
            annotate_summary = "%.1f FPS (MOCK)" % (1.0/elapsed_ms)
        else:
            annotate_summary = "High FPS (MOCK)"
        logging.debug(annotate_summary)
        cv2.putText(frame, annotate_summary, self.bottomLeftCornerOfText, self.font, self.fontScale, self.fontColor, self.lineType)

        return objects, frame


############################
# Test Functions
############################
def test_photo(file):
    """Test with a single photo"""
    print("\n=== Testing photo: %s ===" % file)
    object_processor = ObjectsOnRoadProcessorWindows()
    frame = cv2.imread(file)
    if frame is None:
        print("Error: Could not load image %s" % file)
        return
    
    # Extract filename for mock detection
    import os
    filename = os.path.basename(file)
    combo_image = object_processor.detect_objects(frame, filename)[1]
    object_processor.control_car(object_processor.mock_detect_objects_from_filename(filename))
    
    print("Final speed: %d" % object_processor.speed)
    return combo_image

def test_stop_sign_sequence():
    """Test stop sign behavior with sequence"""
    print("\n=== Testing Stop Sign Sequence ===")
    object_processor = ObjectsOnRoadProcessorWindows()
    
    # Load stop sign image
    frame = cv2.imread('../data/objects/stop_sign.jpg')
    if frame is None:
        print("Warning: stop_sign.jpg not found, using mock")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    print("1. First stop sign detection:")
    objects = object_processor.mock_detect_objects_from_filename('stop_sign.jpg')
    object_processor.control_car(objects)
    
    print("2. Second detection (still waiting):")
    objects = object_processor.mock_detect_objects_from_filename('stop_sign.jpg')
    object_processor.control_car(objects)
    
    print("3. Wait 2 seconds...")
    time.sleep(2.1)
    
    print("4. After wait period - should resume:")
    objects = object_processor.mock_detect_objects_from_filename('green_light.jpg')
    object_processor.control_car(objects)

def test_all_objects():
    """Test all object types"""
    print("\n=== Testing All Object Types ===")
    
    test_cases = [
        ('red_light.jpg', 'Red Traffic Light'),
        ('green_light.jpg', 'Green Traffic Light'), 
        ('person.jpg', 'Person'),
        ('stop_sign.jpg', 'Stop Sign'),
        ('limit_25.jpg', 'Speed Limit 25'),
        ('limit_40.jpg', 'Speed Limit 40'),
        ('no_obj.jpg', 'No Object')
    ]
    
    for filename, description in test_cases:
        print("\n--- Testing %s (%s) ---" % (description, filename))
        object_processor = ObjectsOnRoadProcessorWindows()
        
        # Try to load actual image, fallback to mock
        filepath = '../data/objects/%s' % filename
        frame = cv2.imread(filepath)
        if frame is None:
            print("Image %s not found, using mock frame" % filepath)
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Process
        objects = object_processor.mock_detect_objects_from_filename(filename)
        object_processor.control_car(objects)
        print("Result: Speed = %d, Speed Limit = %d" % (object_processor.speed, object_processor.speed_limit))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)-5s: %(message)s')
    
    print("Objects On Road Processor - Windows Test")
    print("========================================")
    
    # Test individual objects
    test_all_objects()
    
    # Test stop sign sequence
    test_stop_sign_sequence()
    
    # Test with actual images if available
    test_images = [
        '../data/objects/red_light.jpg',
        '../data/objects/green_light.jpg', 
        '../data/objects/person.jpg',
        '../data/objects/stop_sign.jpg',
        '../data/objects/limit_25.jpg',
        '../data/objects/limit_40.jpg',
        '../data/objects/no_obj.jpg'
    ]
    
    for img_path in test_images:
        test_photo(img_path)
    
    print("\n=== Test Completed ===") 