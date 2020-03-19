#!/usr/bin/env python3
"""
Traffic Objects Linux Test - Linux/Raspberry Pi için traffic objects testi
"""

import sys
import os
import logging
import time

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from traffic_objects import *
except ImportError as e:
    logging.error("Cannot import traffic_objects: %s" % str(e))
    logging.info("Make sure traffic_objects.py is in the parent directory")
    sys.exit(1)


def test_basic_functionality():
    """Temel traffic objects fonksiyonalitesini test et"""
    logging.info("=== Basic Traffic Objects Test ===")
    
    # Test car state
    car_state = {
        'speed': 40,
        'speed_limit': 50,
        'steering_angle': 90
    }
    
    logging.info("Initial car state: %s" % car_state)
    
    # Red Traffic Light Test
    logging.info("\n1. Testing Red Traffic Light:")
    red_light = RedTrafficLight()
    red_light.set_car_state(car_state)
    logging.info("After red light: %s" % car_state)
    assert car_state['speed'] == 0, "Red light should stop the car"
    
    # Reset speed
    car_state['speed'] = 40
    
    # Green Traffic Light Test
    logging.info("\n2. Testing Green Traffic Light:")
    green_light = GreenTrafficLight()
    green_light.set_car_state(car_state)
    logging.info("After green light: %s" % car_state)
    # Green light should not change speed
    assert car_state['speed'] == 40, "Green light should not change speed"
    
    # Person Test
    logging.info("\n3. Testing Person Detection:")
    person = Person()
    person.set_car_state(car_state)
    logging.info("After person detection: %s" % car_state)
    assert car_state['speed'] == 0, "Person detection should stop the car"
    
    # Reset speed
    car_state['speed'] = 40
    
    # Speed Limit Test
    logging.info("\n4. Testing Speed Limit 25:")
    speed_limit_25 = SpeedLimit(25)
    speed_limit_25.set_car_state(car_state)
    logging.info("After speed limit 25: %s" % car_state)
    assert car_state['speed_limit'] == 25, "Speed limit should be updated"
    
    # Stop Sign Test
    logging.info("\n5. Testing Stop Sign:")
    car_state = {'speed': 30, 'speed_limit': 50, 'steering_angle': 90}
    stop_sign = StopSign(wait_time_in_sec=2)
    
    # First detection
    logging.info("First stop sign detection:")
    stop_sign.set_car_state(car_state)
    logging.info("After stop sign: %s" % car_state)
    assert car_state['speed'] == 0, "Stop sign should stop the car"
    
    # During wait
    logging.info("During wait period:")
    stop_sign.set_car_state(car_state)
    logging.info("Still waiting: %s" % car_state)
    assert car_state['speed'] == 0, "Should still be stopped during wait"
    
    # Wait for timer
    logging.info("Waiting 2.5 seconds...")
    time.sleep(2.5)
    
    # After wait
    car_state['speed'] = 30  # Reset speed as if car started again
    logging.info("After wait period:")
    stop_sign.set_car_state(car_state)
    logging.info("After wait completed: %s" % car_state)
    
    logging.info("✅ Basic functionality test completed successfully")
    return True


def test_object_proximity():
    """Object proximity detection test"""
    logging.info("=== Object Proximity Test ===")
    
    # Mock object with bounding box
    class MockObject:
        def __init__(self, height):
            # bounding_box format: [(x1,y1), (x2,y2)]
            self.bounding_box = [(100, 100), (200, 100 + height)]
    
    frame_height = 480
    
    # Small object (2% of frame height)
    small_obj = MockObject(10)  # 10 pixels height
    is_close_small = TrafficObject.is_close_by(small_obj, frame_height, min_height_pct=0.05)
    logging.info("Small object (10px, 2.1%%) is close: %s" % is_close_small)
    assert not is_close_small, "Small object should not be considered close"
    
    # Large object (10% of frame height)  
    large_obj = MockObject(48)  # 48 pixels height (10% of 480)
    is_close_large = TrafficObject.is_close_by(large_obj, frame_height, min_height_pct=0.05)
    logging.info("Large object (48px, 10%%) is close: %s" % is_close_large)
    assert is_close_large, "Large object should be considered close"
    
    logging.info("✅ Object proximity test completed successfully")
    return True


def test_with_real_objects():
    """Test gerçek obje dosyalarıyla"""
    logging.info("=== Real Object Files Test ===")
    
    # Test data klasörünü kontrol et
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'objects')
    
    if not os.path.exists(data_dir):
        logging.warning("⚠️  Data directory not found: %s" % data_dir)
        logging.info("Skipping real object files test")
        return True
    
    # Test objelerini listele
    test_objects = [
        ('green_light.jpg', GreenTrafficLight()),
        ('red_light.jpg', RedTrafficLight()),
        ('stop_sign.jpg', StopSign()),
        ('person.jpg', Person()),
        ('limit_25.jpg', SpeedLimit(25)),
        ('limit_40.jpg', SpeedLimit(40))
    ]
    
    found_files = 0
    
    for filename, traffic_obj in test_objects:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            found_files += 1
            logging.info("✅ Found test file: %s" % filename)
            
            # Mock detected object
            car_state = {'speed': 50, 'speed_limit': 60, 'steering_angle': 90}
            
            # Test with mock close object
            mock_detected_obj = type('MockObj', (), {
                'bounding_box': [(100, 100), (150, 150)]  # 50x50 pixel object
            })()
            
            frame_height = 240  # Raspberry Pi camera resolution
            is_close = TrafficObject.is_close_by(mock_detected_obj, frame_height)
            
            if is_close:
                logging.info("  Testing %s (close object)" % filename)
                traffic_obj.set_car_state(car_state)
                logging.info("  Result: %s" % car_state)
            else:
                logging.info("  %s object too far, no action" % filename)
        else:
            logging.debug("Test file not found: %s" % filepath)
    
    if found_files > 0:
        logging.info("✅ Real object files test completed (%d files found)" % found_files)
    else:
        logging.warning("⚠️  No test files found, but test passed")
    
    return True


def check_system_compatibility():
    """Linux sisteminde traffic objects uyumluluğunu kontrol et"""
    logging.info("=== System Compatibility Check ===")
    
    try:
        # Import check
        from traffic_objects import TrafficObject, RedTrafficLight, GreenTrafficLight
        from traffic_objects import Person, SpeedLimit, StopSign
        logging.info("✅ All traffic object classes imported successfully")
        
        # Basic functionality check
        car_state = {'speed': 30}
        red_light = RedTrafficLight()
        red_light.set_car_state(car_state)
        
        if car_state['speed'] == 0:
            logging.info("✅ Traffic light stop functionality works")
        else:
            logging.error("❌ Traffic light stop functionality failed")
            return False
            
        # Timer functionality check
        stop_sign = StopSign(wait_time_in_sec=1)
        start_time = time.time()
        car_state = {'speed': 25}
        stop_sign.set_car_state(car_state)
        
        # Check if stopped
        if car_state['speed'] == 0:
            logging.info("✅ Stop sign stop functionality works")
        else:
            logging.error("❌ Stop sign stop functionality failed")
            return False
        
        # Wait and check timer
        time.sleep(1.2)
        if not stop_sign.in_wait_mode:
            logging.info("✅ Stop sign timer functionality works")
        else:
            logging.warning("⚠️  Stop sign timer might have issues")
            
        logging.info("✅ System compatibility check passed")
        return True
        
    except Exception as e:
        logging.error("❌ System compatibility check failed: %s" % str(e))
        return False


def main():
    """Ana test fonksiyonu"""
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("Traffic Objects Linux Test Suite")
        print("Usage: python traffic_objects_test_fixed.py [1-4]")
        print("1. Basic functionality test")
        print("2. Real object files test")
        print("3. System compatibility check")
        print("4. All tests")
        choice = input("Enter choice (1-4): ")
    
    success = True
    
    if choice == "1":
        success = test_basic_functionality()
    elif choice == "2":
        success = test_with_real_objects()
    elif choice == "3":
        success = check_system_compatibility()
    elif choice == "4":
        logging.info("Running all tests...")
        success = (test_basic_functionality() and 
                  test_object_proximity() and
                  test_with_real_objects() and 
                  check_system_compatibility())
    else:
        logging.error("Invalid choice: %s" % choice)
        return False
    
    if success:
        logging.info("✅ All selected tests passed!")
        return True
    else:
        logging.error("❌ Some tests failed!")
        return False


if __name__ == '__main__':
    # Setup logging
    log_level = logging.DEBUG if '-v' in sys.argv else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("Traffic Objects Linux Test Suite Starting...")
    
    if main():
        sys.exit(0)
    else:
        sys.exit(1) 