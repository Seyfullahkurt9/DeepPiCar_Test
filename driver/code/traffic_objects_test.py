from traffic_objects import *
import logging
import time

def test_traffic_objects():
    """Traffic objects sınıflarını test et"""
    logging.basicConfig(level=logging.DEBUG)
    
    print("Traffic Objects Test Starting...")
    
    # Car state dictionary
    car_state = {
        'speed': 40,
        'speed_limit': 50,
        'steering_angle': 90
    }
    
    print("Initial car state: %s" % car_state)
    
    # Red Traffic Light Test
    print("\n1. Testing Red Traffic Light:")
    red_light = RedTrafficLight()
    red_light.set_car_state(car_state)
    print("After red light: %s" % car_state)
    
    # Reset speed
    car_state['speed'] = 40
    
    # Green Traffic Light Test
    print("\n2. Testing Green Traffic Light:")
    green_light = GreenTrafficLight()
    green_light.set_car_state(car_state)
    print("After green light: %s" % car_state)
    
    # Person Test
    print("\n3. Testing Person Detection:")
    person = Person()
    person.set_car_state(car_state)
    print("After person detection: %s" % car_state)
    
    # Reset speed
    car_state['speed'] = 40
    
    # Speed Limit Test
    print("\n4. Testing Speed Limit 25:")
    speed_limit_25 = SpeedLimit(25)
    speed_limit_25.set_car_state(car_state)
    print("After speed limit 25: %s" % car_state)
    
    # Stop Sign Test
    print("\n5. Testing Stop Sign:")
    stop_sign = StopSign(wait_time_in_sec=2)
    
    # First detection
    print("First stop sign detection:")
    stop_sign.set_car_state(car_state)
    print("After stop sign: %s" % car_state)
    
    # During wait
    print("During wait period:")
    stop_sign.set_car_state(car_state)
    print("Still waiting: %s" % car_state)
    
    # Wait for timer
    print("Waiting 2 seconds...")
    time.sleep(2.5)
    
    # After wait
    print("After wait period:")
    stop_sign.set_car_state(car_state)
    print("After wait completed: %s" % car_state)
    
    # Test object proximity
    print("\n6. Testing Object Proximity:")
    
    # Mock object with bounding box
    class MockObject:
        def __init__(self, height):
            # bounding_box format: [(x1,y1), (x2,y2)]
            self.bounding_box = [(100, 100), (200, 100 + height)]
    
    frame_height = 480
    
    # Small object (2% of frame height)
    small_obj = MockObject(10)  # 10 pixels height
    is_close_small = TrafficObject.is_close_by(small_obj, frame_height, min_height_pct=0.05)
    print("Small object (10px) is close: %s" % is_close_small)
    
    # Large object (10% of frame height)  
    large_obj = MockObject(48)  # 48 pixels height (10% of 480)
    is_close_large = TrafficObject.is_close_by(large_obj, frame_height, min_height_pct=0.05)
    print("Large object (48px) is close: %s" % is_close_large)
    
    print("\nTraffic Objects Test Completed!")

if __name__ == '__main__':
    test_traffic_objects() 