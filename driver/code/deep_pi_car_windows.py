import logging
import warnings
import os

# Comprehensive warning suppression
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_SILENCE_ALL_WARNINGS'] = '1'

import mock_picar as picar  # Mock picar kullan
import cv2
import datetime
from hand_coded_lane_follower_test_windows import HandCodedLaneFollower
# from objects_on_road_processor import ObjectsOnRoadProcessor  # Object detection devre disi

_SHOW_IMAGE = True


class DeepPiCarWindows(object):

    __INITIAL_SPEED = 0
    __SCREEN_WIDTH = 320
    __SCREEN_HEIGHT = 240

    def __init__(self):
        """ Init camera and wheels"""
        logging.info('Creating a DeepPiCar for Windows...')

        picar.setup()

        logging.debug('Set up camera')
        # Suppress OpenCV warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.camera = cv2.VideoCapture(0)  # Windows'ta 0 
            self.camera.set(3, self.__SCREEN_WIDTH)
            self.camera.set(4, self.__SCREEN_HEIGHT)

        self.pan_servo = picar.Servo.Servo(1)
        self.pan_servo.offset = -30  # calibrate servo to center
        self.pan_servo.write(90)

        self.tilt_servo = picar.Servo.Servo(2)
        self.tilt_servo.offset = 20  # calibrate servo to center
        self.tilt_servo.write(90)

        logging.debug('Set up back wheels')
        self.back_wheels = picar.back_wheels.Back_Wheels()
        self.back_wheels.speed = 0  # Speed Range is 0 (stop) - 100 (fastest)

        logging.debug('Set up front wheels')
        self.front_wheels = picar.front_wheels.Front_Wheels()
        self.front_wheels.turning_offset = -25  # calibrate servo to center
        self.front_wheels.turn(90)  # Steering Range is 45 (left) - 90 (center) - 135 (right)

        self.lane_follower = HandCodedLaneFollower(self)
        # self.traffic_sign_processor = ObjectsOnRoadProcessor(self)  # Object detection devre disi
        # lane_follower = DeepLearningLaneFollower()

        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        datestr = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        
        # Video kayit yollari Windows icin
        os.makedirs('../data/tmp', exist_ok=True)
        
        self.video_orig = self.create_video_recorder('../data/tmp/car_video{}.avi'.format(datestr))
        self.video_lane = self.create_video_recorder('../data/tmp/car_video_lane{}.avi'.format(datestr))
        # self.video_objs = self.create_video_recorder('../data/tmp/car_video_objs%s.avi' % datestr)

        logging.info('Created a DeepPiCar for Windows')

    def create_video_recorder(self, path):
        return cv2.VideoWriter(path, self.fourcc, 20.0, (self.__SCREEN_WIDTH, self.__SCREEN_HEIGHT))

    def __enter__(self):
        """ Entering a with statement """
        return self

    def __exit__(self, _type, value, traceback):
        """ Exit a with statement"""
        if traceback is not None:
            # Exception occurred:
            logging.error('Exiting with statement with exception {}'.format(traceback))

        self.cleanup()

    def cleanup(self):
        """ Reset the hardware"""
        logging.info('Stopping the car, resetting hardware.')
        self.back_wheels.speed = 0
        self.front_wheels.turn(90)
        self.camera.release()
        self.video_orig.release()
        self.video_lane.release()
        # self.video_objs.release()
        cv2.destroyAllWindows()

    def drive(self, speed=__INITIAL_SPEED):
        """ Main entry point of the car, and put it in drive mode

        Keyword arguments:
        speed -- speed of back wheel, range is 0 (stop) - 100 (fastest)
        """

        logging.info('Starting to drive at speed {}...'.format(speed))
        self.back_wheels.speed = speed
        i = 0
        while self.camera.isOpened():
            _, image_lane = self.camera.read()
            if image_lane is None:
                logging.error("Kameradan görüntü alınamadı!")
                break
                
            # image_objs = image_lane.copy()
            i += 1
            self.video_orig.write(image_lane)

            # Object detection devre disi
            # image_objs = self.process_objects_on_road(image_objs)
            # self.video_objs.write(image_objs)
            # show_image('Detected Objects', image_objs)

            image_lane = self.follow_lane(image_lane)
            self.video_lane.write(image_lane)
            show_image('Lane Lines', image_lane)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.cleanup()
                break

    def process_objects_on_road(self, image):
        # Object detection devre disi
        logging.debug("Object detection disabled for Windows")
        return image

    def follow_lane(self, image):
        image = self.lane_follower.follow_lane(image)
        return image


############################
# Utility Functions
############################
def show_image(title, frame, show=_SHOW_IMAGE):
    if show:
        cv2.imshow(title, frame)


def main():
    with DeepPiCarWindows() as car:
        car.drive(40)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-5s:%(asctime)s: %(message)s')
    
    main() 