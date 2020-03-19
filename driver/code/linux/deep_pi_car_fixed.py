import os
import logging
import datetime as dt
import cv2
import time

# Hardware import with fallback
try:
    import picar
    HARDWARE_AVAILABLE = True
    logging.info("PiCar hardware modules loaded successfully")
except ImportError as e:
    logging.warning("PiCar hardware not available: %s" % str(e))
    HARDWARE_AVAILABLE = False
    # Mock hardware for testing
    class MockPiCar:
        class MockBackWheels:
            def __init__(self):
                self.speed = 0
            def forward(self):
                logging.debug("MOCK: Back wheels forward at speed %d" % self.speed)
            def backward(self):
                logging.debug("MOCK: Back wheels backward at speed %d" % self.speed)
            def stop(self):
                logging.debug("MOCK: Back wheels stop")
        
        class MockFrontWheels:
            def __init__(self):
                self.angle = 90
            def turn(self, angle):
                self.angle = angle
                logging.debug("MOCK: Front wheels turn to %d degrees" % angle)
        
        @staticmethod
        def setup():
            logging.debug("MOCK: PiCar setup")
    
    picar = MockPiCar()

# Try to import lane followers with fallback
try:
    from hand_coded_lane_follower_fixed import HandCodedLaneFollower
except ImportError:
    try:
        from driver.code.hand_coded_lane_follower_test_windows import HandCodedLaneFollower
        logging.warning("Using original hand_coded_lane_follower (may have bugs)")
    except ImportError:
        logging.error("No lane follower available!")
        HandCodedLaneFollower = None

try:
    from end_to_end_lane_follower_fixed import EndToEndLaneFollower
except ImportError:
    try:
        from end_to_end_lane_follower import EndToEndLaneFollower
        logging.warning("Using original end_to_end_lane_follower (may have bugs)")
    except ImportError:
        logging.error("No end-to-end lane follower available!")
        EndToEndLaneFollower = None


class DeepPiCar(object):

    __INITIAL_SPEED = 0
    __SCREEN_WIDTH = 320
    __SCREEN_HEIGHT = 240

    def __init__(self):
        logging.info('Creating a DeepPiCar...')
        
        # Hardware setup with checks
        self.setup_hardware()
        
        # Camera setup with multiple fallbacks
        self.setup_camera()
        
        # Lane follower setup
        self.setup_lane_followers()
        
        # Recording setup
        self.setup_recording()

    def setup_hardware(self):
        """Setup hardware with availability checks"""
        if HARDWARE_AVAILABLE:
            try:
                picar.setup()
                
                self.back_wheels = picar.back_wheels.Back_Wheels()
                self.front_wheels = picar.front_wheels.Front_Wheels()
                
                self.back_wheels.speed = self.__INITIAL_SPEED  # speed is 0~100
                self.front_wheels.turn(90)  # 90 is straight
                
                logging.info("Hardware initialized successfully")
            except Exception as e:
                logging.error("Hardware initialization failed: %s" % str(e))
                self.setup_mock_hardware()
        else:
            self.setup_mock_hardware()

    def setup_mock_hardware(self):
        """Setup mock hardware for testing"""
        logging.info("Setting up mock hardware")
        self.back_wheels = picar.MockBackWheels()
        self.front_wheels = picar.MockFrontWheels()
        self.back_wheels.speed = self.__INITIAL_SPEED

    def setup_camera(self):
        """Setup camera with multiple source attempts"""
        self.camera = None
        
        # Try different camera sources
        camera_sources = [0, 1, '/dev/video0', '/dev/video1']
        
        for source in camera_sources:
            try:
                logging.info("Trying camera source: %s" % source)
                self.camera = cv2.VideoCapture(source)
                
                if self.camera.isOpened():
                    # Test camera by reading a frame
                    ret, test_frame = self.camera.read()
                    if ret and test_frame is not None:
                        logging.info("Camera successfully initialized: %s" % source)
                        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.__SCREEN_WIDTH)
                        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.__SCREEN_HEIGHT)
                        break
                    else:
                        logging.warning("Camera opened but cannot read frames: %s" % source)
                        self.camera.release()
                        self.camera = None
                else:
                    logging.warning("Cannot open camera: %s" % source)
                    self.camera = None
                    
            except Exception as e:
                logging.warning("Camera initialization error for %s: %s" % (source, e))
                if self.camera:
                    self.camera.release()
                    self.camera = None
        
        if self.camera is None:
            logging.error("No working camera found!")
            raise RuntimeError("Camera initialization failed")

    def setup_lane_followers(self):
        """Setup lane following algorithms"""
        if HandCodedLaneFollower:
            self.lane_follower = HandCodedLaneFollower(self)
            logging.info("Hand-coded lane follower initialized")
        else:
            self.lane_follower = None
            logging.error("No hand-coded lane follower available")
            
        if EndToEndLaneFollower:
            try:
                self.end_to_end_lane_follower = EndToEndLaneFollower(self)
                logging.info("End-to-end lane follower initialized")
            except Exception as e:
                logging.error("End-to-end lane follower initialization failed: %s" % str(e))
                self.end_to_end_lane_follower = None
        else:
            self.end_to_end_lane_follower = None
            logging.warning("No end-to-end lane follower available")

    def setup_recording(self):
        """Setup video recording"""
        try:
            self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
            
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                logging.info("Created data directory: %s" % data_dir)
            
            video_file = os.path.join(data_dir, 'car_video_%s.avi' % str(dt.datetime.now()).replace(' ', '_').replace(':', '-'))
            self.video_writer = cv2.VideoWriter(video_file, self.fourcc, 20.0, (self.__SCREEN_WIDTH, self.__SCREEN_HEIGHT))
            logging.info("Video recording setup: %s" % video_file)
            
        except Exception as e:
            logging.error("Video recording setup failed: %s" % str(e))
            self.video_writer = None

    def drive(self, speed=60):
        """Main driving loop with enhanced error handling"""
        logging.info('Starting to drive at speed %d' % speed)
        
        if self.lane_follower is None:
            logging.error("No lane follower available, cannot drive")
            return
            
        self.back_wheels.speed = speed
        self.back_wheels.forward()
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    logging.error("Failed to read frame from camera")
                    break
                
                try:
                    # Process frame with lane follower
                    frame = self.lane_follower.follow_lane(frame)
                    
                    # Record video if available
                    if self.video_writer:
                        self.video_writer.write(frame)
                    
                    # Performance monitoring
                    frame_count += 1
                    if frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        fps = frame_count / elapsed
                        logging.info("Processed %d frames, FPS: %.1f" % (frame_count, fps))
                    
                    # Display frame (optional, for debugging)
                    cv2.imshow('DeepPiCar', frame)
                    
                    # Check for quit command
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logging.info("Quit command received")
                        break
                        
                except Exception as e:
                    logging.error("Error processing frame: %s" % str(e))
                    # Continue with next frame
                    continue
                    
        except KeyboardInterrupt:
            logging.info("Interrupted by user")
        except Exception as e:
            logging.error("Unexpected error in drive loop: %s" % str(e))
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        logging.info("Stopping the car, resetting hardware.")
        
        try:
            self.back_wheels.speed = 0
            self.back_wheels.stop()
            self.front_wheels.turn(90)
        except Exception as e:
            logging.error("Error during hardware cleanup: %s" % str(e))
        
        try:
            if self.camera:
                self.camera.release()
        except Exception as e:
            logging.error("Error releasing camera: %s" % str(e))
            
        try:
            if self.video_writer:
                self.video_writer.release()
        except Exception as e:
            logging.error("Error releasing video writer: %s" % str(e))
        
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            logging.error("Error destroying windows: %s" % str(e))

    def __enter__(self):
        return self

    def __exit__(self, _type, value, traceback):
        self.cleanup()


def check_raspberry_pi_environment():
    """Check if running on Raspberry Pi with proper setup"""
    logging.info("=== Raspberry Pi Environment Check ===")
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                logging.info("Running on Raspberry Pi hardware")
            else:
                logging.warning("Not running on Raspberry Pi hardware")
    except:
        logging.warning("Cannot determine hardware type")
    
    # Check GPIO availability
    try:
        import RPi.GPIO as GPIO
        logging.info("RPi.GPIO available")
    except ImportError:
        logging.warning("RPi.GPIO not available")
    
    # Check camera module
    if os.path.exists('/dev/video0'):
        logging.info("Camera device /dev/video0 available")
    else:
        logging.warning("Camera device /dev/video0 not found")
    
    # Check permissions
    import os
    if os.getuid() == 0:
        logging.info("Running as root (good for GPIO access)")
    else:
        logging.warning("Not running as root (may need sudo for GPIO)")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    
    check_raspberry_pi_environment()
    
    try:
        with DeepPiCar() as car:
            car.drive(40)
    except Exception as e:
        logging.error("Failed to start DeepPiCar: %s" % str(e)) 