import cv2
import numpy as np
import logging
import math
import os
import warnings

# Comprehensive warning suppression
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_SILENCE_ALL_WARNINGS'] = '1'

# Modern TensorFlow/Keras import
try:
    # TensorFlow 2.x style (preferred)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import tensorflow as tf
        tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
        from tensorflow.keras.models import load_model
        logging.debug("Using TensorFlow 2.x style imports")
except ImportError:
    try:
        # TensorFlow 1.x fallback
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from keras.models import load_model
            logging.warning("Using legacy Keras imports (TensorFlow 1.x)")
    except ImportError:
        logging.error("Neither TensorFlow 2.x nor legacy Keras available")
        load_model = None

from hand_coded_lane_follower_test_windows import HandCodedLaneFollower

_SHOW_IMAGE = False


class EndToEndLaneFollower(object):

    def __init__(self, car=None):
        logging.info('Creating a EndToEndLaneFollower...')
        
        # Windows path için model dosyasını bul
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, '..', '..', 'models', 'lane_navigation', 'data', 'model_result', 'lane_navigation.h5')
        
        if not os.path.exists(model_path):
            logging.warning('Model file not found at %s' % model_path)
            logging.info('Creating a mock model for Windows testing...')
            self.model = None
        else:
            try:
                if load_model is None:
                    logging.error('Model loading not available (Keras/TensorFlow not installed)')
                    self.model = None
                else:
                    # Suppress TensorFlow warnings during model loading
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.model = load_model(model_path)
                        logging.info('Model loaded successfully from %s' % model_path)
            except Exception as e:
                logging.error('Failed to load model: %s' % str(e))
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
            # Mock steering angle for Windows testing
            logging.debug('Using mock steering angle (no model available)')
            return 90 + np.random.randint(-10, 10)
            
        preprocessed = img_preprocess(frame)
        X = np.asarray([preprocessed])
        steering_angle = self.model.predict(X)[0]

        logging.debug('new steering angle: %s' % steering_angle)
        return int(steering_angle + 0.5) # round the nearest integer


def img_preprocess(image):
    height, _, _ = image.shape
    image = image[int(height/2):,:,:]  # remove top half of the image, as it is not relevant for lane following
    image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)  # Nvidia model said it is best to use YUV color space
    image = cv2.GaussianBlur(image, (3,3), 0)
    image = cv2.resize(image, (200,66)) # input image size (200,66) Nvidia model
    image = image / 255 # normalizing, the processed image becomes black for some reason.  do we need this?
    return image

def display_heading_line(frame, steering_angle, line_color=(0, 0, 255), line_width=5, ):
    heading_image = np.zeros_like(frame)
    height, width, _ = frame.shape

    # figure out the heading line from steering angle
    # heading line (x1,y1) is always center bottom of the screen
    # (x2, y2) requires a bit of trigonometry

    # Note: the steering angle of:
    # 0-89 degree: turn left
    # 90 degree: going straight
    # 91-180 degree: turn right 
    steering_angle_radian = steering_angle / 180.0 * math.pi
    x1 = int(width / 2)
    y1 = height
    x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
    y2 = int(height / 2)

    cv2.line(heading_image, (x1, y1), (x2, y2), line_color, line_width)
    heading_image = cv2.addWeighted(frame, 0.8, heading_image, 1, 1)

    return heading_image


def show_image(title, frame, show=_SHOW_IMAGE):
    if show:
        cv2.imshow(title, frame)


############################
# Test Functions
############################
def test_photo_windows():
    """Windows test with webcam capture"""
    lane_follower = EndToEndLaneFollower()
    
    # Webcam'den bir frame yakala
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        combo_image = lane_follower.follow_lane(frame)
        show_image('final', combo_image, True)
        logging.info("Windows test: model steering angle = %3d" % lane_follower.curr_steering_angle)
        cv2.waitKey(2000)  # 2 saniye göster
        cv2.destroyAllWindows()
    else:
        logging.error("Could not capture frame from webcam")


def test_video_comparison_windows():
    """Windows'ta webcam ile hand-coded vs end-to-end karşılaştırması"""
    end_to_end_lane_follower = EndToEndLaneFollower()
    hand_coded_lane_follower = HandCodedLaneFollower()
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot open webcam")
        return
        
    logging.info("Starting live comparison test. Press 'q' to quit.")
    
    try:
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_copy = frame.copy()
            
            # Her 10 frame'de bir log
            if frame_count % 10 == 0:
                logging.info('Frame %s' % frame_count)
            
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

            frame_count += 1
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("End-to-End Lane Follower Windows Test")
    print("1. Single photo test")
    print("2. Live comparison test")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        test_photo_windows()
    elif choice == "2":
        test_video_comparison_windows()
    else:
        print("Invalid choice") 