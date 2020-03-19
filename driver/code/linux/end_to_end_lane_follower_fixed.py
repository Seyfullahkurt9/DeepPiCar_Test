import cv2
import numpy as np
import logging
import math
import os
import sys
from keras.models import load_model
from hand_coded_lane_follower_fixed import HandCodedLaneFollower

_SHOW_IMAGE = False


class EndToEndLaneFollower(object):

    def __init__(self, car=None, model_path=None):
        logging.info('Creating a EndToEndLaneFollower...')
        
        # Linux path için model dosyasını bul - multiple locations check
        if model_path is None:
            possible_paths = [
                '/home/pi/DeepPiCar/models/lane_navigation/data/model_result/lane_navigation.h5',
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lane_navigation', 'data', 'model_result', 'lane_navigation.h5'),
                './models/lane_navigation/data/model_result/lane_navigation.h5',
                '../models/lane_navigation/data/model_result/lane_navigation.h5'
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    logging.info('Found model at: %s' % path)
                    break
        
        if model_path and os.path.exists(model_path):
            try:
                self.model = load_model(model_path)
                logging.info('Successfully loaded model with %d parameters' % self.model.count_params())
            except Exception as e:
                logging.error('Failed to load model: %s' % str(e))
                self.model = None
        else:
            logging.warning('Model file not found. Available paths checked:')
            for path in possible_paths:
                logging.warning('  %s - %s' % (path, 'EXISTS' if os.path.exists(path) else 'NOT FOUND'))
            logging.info('Running in mock mode for testing...')
            self.model = None
            
        self.car = car
        self.curr_steering_angle = 90

    def follow_lane(self, frame):
        # Main entry point of the lane follower
        show_image("orig", frame)

        self.curr_steering_angle = self.compute_steering_angle(frame)
        logging.debug("curr_steering_angle = %d" % self.curr_steering_angle)

        if self.car is not None:
            self.car.front_wheels.turn(self.curr_steering_angle)
        final_frame = display_heading_line(frame, self.curr_steering_angle)

        return final_frame

    def compute_steering_angle(self, frame):
        """ Find the steering angle directly based on video frame
            We assume that camera is calibrated to point to dead center
        """
        if self.model is None:
            # Mock steering angle for testing without model
            logging.debug('Using mock steering angle (no model available)')
            return 90 + np.random.randint(-10, 10)
            
        try:
            preprocessed = img_preprocess(frame)
            X = np.asarray([preprocessed])
            steering_angle = self.model.predict(X)[0]

            # Ensure steering angle is within valid range
            steering_angle = max(0, min(180, float(steering_angle)))
            
            logging.debug('new steering angle: %s' % steering_angle)
            return int(steering_angle + 0.5) # round the nearest integer
        except Exception as e:
            logging.error('Error in model prediction: %s' % str(e))
            return 90  # fallback to center


def img_preprocess(image):
    """
    Preprocess image for Nvidia model
    Enhanced with error handling
    """
    try:
        height, width, channels = image.shape
        if channels != 3:
            logging.warning('Unexpected number of channels: %d' % channels)
            
        image = image[int(height/2):,:,:]  # remove top half of the image, as it is not relevant for lane following
        image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)  # Nvidia model said it is best to use YUV color space
        image = cv2.GaussianBlur(image, (3,3), 0)
        image = cv2.resize(image, (200,66)) # input image size (200,66) Nvidia model
        image = image / 255.0 # normalizing
        return image
    except Exception as e:
        logging.error('Error in image preprocessing: %s' % str(e))
        # Return a default processed image
        return np.zeros((66, 200, 3))

def display_heading_line(frame, steering_angle, line_color=(0, 0, 255), line_width=5):
    """
    Enhanced with mathematical error handling
    """
    heading_image = np.zeros_like(frame)
    height, width, _ = frame.shape

    # figure out the heading line from steering angle
    # heading line (x1,y1) is always center bottom of the screen
    # (x2, y2) requires a bit of trigonometry

    # Note: the steering angle of:
    # 0-89 degree: turn left
    # 90 degree: going straight
    # 91-180 degree: turn right 
    
    try:
        steering_angle_radian = steering_angle / 180.0 * math.pi
        x1 = int(width / 2)
        y1 = height
        
        # Add protection against tan(90°) = infinity
        if abs(steering_angle - 90) < 0.1:  # nearly straight
            x2 = x1
        else:
            x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
        y2 = int(height / 2)

        cv2.line(heading_image, (x1, y1), (x2, y2), line_color, line_width)
        heading_image = cv2.addWeighted(frame, 0.8, heading_image, 1, 1)
    except (ZeroDivisionError, OverflowError) as e:
        logging.warning('Mathematical error in heading line: %s' % str(e))
        heading_image = frame.copy()

    return heading_image


def show_image(title, frame, show=_SHOW_IMAGE):
    if show:
        cv2.imshow(title, frame)


############################
# Test Functions
############################
def test_photo_linux(image_path=None):
    """Linux test with camera capture or image file"""
    lane_follower = EndToEndLaneFollower()
    
    if image_path and os.path.exists(image_path):
        frame = cv2.imread(image_path)
        if frame is None:
            logging.error("Could not load image: %s" % image_path)
            return
    else:
        # Try to capture from camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logging.error("Could not open camera")
            return
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            logging.error("Could not capture frame from camera")
            return
    
    combo_image = lane_follower.follow_lane(frame)
    show_image('final', combo_image, True)
    logging.info("Linux test: model steering angle = %3d" % lane_follower.curr_steering_angle)
    cv2.waitKey(2000)  # 2 saniye göster
    cv2.destroyAllWindows()


def test_video_comparison_linux():
    """Linux'ta kamera ile hand-coded vs end-to-end karşılaştırması"""
    end_to_end_lane_follower = EndToEndLaneFollower()
    hand_coded_lane_follower = HandCodedLaneFollower()
    
    # Try different camera sources for Raspberry Pi
    camera_sources = [0, 1, '/dev/video0', '/dev/video1']
    cap = None
    
    for source in camera_sources:
        try:
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                logging.info('Successfully opened camera: %s' % source)
                break
            cap.release()
        except Exception as e:
            logging.debug('Failed to open camera %s: %s' % (source, e))
    
    if cap is None or not cap.isOpened():
        logging.error("Cannot open any camera source")
        return
        
    logging.info("Starting live comparison test. Press 'q' to quit.")
    
    try:
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                logging.error("Failed to read frame")
                break
                
            frame_copy = frame.copy()
            
            # Her 10 frame'de bir log
            if frame_count % 10 == 0:
                logging.info('Frame %s' % frame_count)
            
            try:
                combo_image1 = hand_coded_lane_follower.follow_lane(frame)
                combo_image2 = end_to_end_lane_follower.follow_lane(frame_copy)

                diff = end_to_end_lane_follower.curr_steering_angle - hand_coded_lane_follower.curr_steering_angle
                
                if frame_count % 10 == 0:
                    logging.info("hand_coded=%3d, end_to_end=%3d, diff=%3d" %
                                  (hand_coded_lane_follower.curr_steering_angle,
                                  end_to_end_lane_follower.curr_steering_angle,
                                  diff))

                cv2.imshow("Hand Coded Lane Following", combo_image1)
                cv2.imshow("End-to-End Deep Learning", combo_image2)
            except Exception as e:
                logging.error("Error processing frame: %s" % str(e))

            frame_count += 1
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()


def check_system_requirements():
    """Linux sisteminin gereksinimlerini kontrol et"""
    logging.info("=== Linux System Requirements Check ===")
    
    # OpenCV check
    logging.info("OpenCV version: %s" % cv2.__version__)
    
    # Camera check
    logging.info("Checking camera availability...")
    camera_found = False
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            logging.info("Camera found at index %d" % i)
            camera_found = True
            cap.release()
        else:
            logging.debug("No camera at index %d" % i)
    
    if not camera_found:
        logging.warning("No cameras detected!")
    
    # Check video devices
    video_devices = []
    for device in ['/dev/video0', '/dev/video1', '/dev/video2']:
        if os.path.exists(device):
            video_devices.append(device)
    
    if video_devices:
        logging.info("Video devices found: %s" % video_devices)
    else:
        logging.warning("No /dev/video* devices found")
    
    # Model path check
    logging.info("Model path check...")
    model_paths = [
        '/home/pi/DeepPiCar/models/lane_navigation/data/model_result/lane_navigation.h5',
        './models/lane_navigation/data/model_result/lane_navigation.h5'
    ]
    
    for path in model_paths:
        if os.path.exists(path):
            logging.info("Model found: %s" % path)
        else:
            logging.debug("Model not found: %s" % path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    check_system_requirements()
    
    print("End-to-End Lane Follower Linux Test")
    print("1. Single photo test")
    print("2. Live comparison test") 
    print("3. System check only")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Enter choice (1, 2, or 3): ")
    
    if choice == "1":
        image_path = sys.argv[2] if len(sys.argv) > 2 else None
        test_photo_linux(image_path)
    elif choice == "2":
        test_video_comparison_linux()
    elif choice == "3":
        logging.info("System check completed.")
    else:
        print("Invalid choice") 