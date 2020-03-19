from deep_pi_car_windows import DeepPiCarWindows
import logging
import sys

def main():
    # print system info
    logging.info('Starting DeepPiCar Windows Version, system info: ' + sys.version)
    
    try:
        with DeepPiCarWindows() as car:
            car.drive(40)
    except KeyboardInterrupt:
        logging.info('DeepPiCar stopped by user')
    except Exception as e:
        logging.error('DeepPiCar error: %s' % str(e))
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main() 