import logging
import sys
import os

# Import with fallback to original
try:
    from deep_pi_car_fixed import DeepPiCar
    logging.info("Using fixed DeepPiCar version")
except ImportError:
    try:
        from deep_pi_car import DeepPiCar
        logging.warning("Using original DeepPiCar (may have issues)")
    except ImportError:
        logging.error("No DeepPiCar module available!")
        sys.exit(1)

def check_prerequisites():
    """Linux sisteminin gereksinimlerini kontrol et"""
    logging.info("=== DeepPiCar Prerequisites Check ===")
    
    # Python version check
    python_version = sys.version_info
    logging.info("Python version: %d.%d.%d" % (python_version.major, python_version.minor, python_version.micro))
    
    if python_version.major < 3:
        logging.error("Python 3 required!")
        return False
    
    # Required modules check
    required_modules = ['cv2', 'numpy', 'logging']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            logging.info("✅ %s available" % module)
        except ImportError:
            logging.error("❌ %s missing" % module)
            missing_modules.append(module)
    
    # Optional modules check
    optional_modules = ['keras', 'tensorflow']
    for module in optional_modules:
        try:
            __import__(module)
            logging.info("✅ %s available (for AI features)" % module)
        except ImportError:
            logging.warning("⚠️  %s not available (AI features disabled)" % module)
    
    # Camera check
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            logging.info("✅ Camera available")
            cap.release()
        else:
            logging.warning("⚠️  Camera not accessible")
    except Exception as e:
        logging.warning("⚠️  Camera check failed: %s" % str(e))
    
    # Hardware check
    try:
        import picar
        logging.info("✅ PiCar hardware modules available")
    except ImportError:
        logging.warning("⚠️  PiCar hardware not available (mock mode will be used)")
    
    # GPIO check for Raspberry Pi
    try:
        import RPi.GPIO as GPIO
        logging.info("✅ RPi.GPIO available")
    except ImportError:
        logging.warning("⚠️  RPi.GPIO not available (not on Raspberry Pi?)")
    
    # Permission check
    if os.getuid() == 0:
        logging.info("✅ Running as root (good for GPIO access)")
    else:
        logging.warning("⚠️  Not running as root (may need sudo for GPIO)")
    
    if missing_modules:
        logging.error("Missing critical modules: %s" % missing_modules)
        return False
    
    logging.info("✅ Prerequisites check completed")
    return True


def main():
    """Ana fonksiyon - Linux için optimize edilmiş"""
    # Sistem bilgilerini logla
    logging.info('Starting DeepPiCar Linux Version')
    logging.info('System info: %s' % sys.version)
    logging.info('Platform: %s' % sys.platform)
    
    # Prerequisites kontrolü
    if not check_prerequisites():
        logging.error("Prerequisites check failed. Please install missing components.")
        sys.exit(1)
    
    # Speed parametresi
    default_speed = 40
    if len(sys.argv) > 1:
        try:
            speed = int(sys.argv[1])
            if speed < 0 or speed > 100:
                logging.warning("Speed should be 0-100, using default: %d" % default_speed)
                speed = default_speed
        except ValueError:
            logging.warning("Invalid speed parameter, using default: %d" % default_speed)
            speed = default_speed
    else:
        speed = default_speed
    
    logging.info("Driving speed set to: %d" % speed)
    
    # DeepPiCar'ı başlat
    try:
        with DeepPiCar() as car:
            logging.info("DeepPiCar initialized successfully")
            logging.info("Press Ctrl+C to stop")
            car.drive(speed)
            
    except KeyboardInterrupt:
        logging.info('DeepPiCar stopped by user (Ctrl+C)')
    except RuntimeError as e:
        logging.error('DeepPiCar runtime error: %s' % str(e))
        logging.info('This might be due to camera or hardware issues')
        sys.exit(1)
    except Exception as e:
        logging.error('DeepPiCar unexpected error: %s' % str(e))
        import traceback
        logging.debug('Full traceback: %s' % traceback.format_exc())
        sys.exit(1)
    
    logging.info('DeepPiCar session completed successfully')


def test_mode():
    """Test modu - donanım olmadan sistem testi"""
    logging.info("=== DeepPiCar Test Mode ===")
    
    try:
        # DeepPiCar oluşturmayı dene
        car = DeepPiCar()
        logging.info("✅ DeepPiCar object created successfully")
        
        # Camera test
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                logging.info("✅ Camera capture test successful")
                logging.info("   Frame size: %dx%d" % (frame.shape[1], frame.shape[0]))
            else:
                logging.warning("⚠️  Camera opened but cannot read frames")
            cap.release()
        else:
            logging.warning("⚠️  Cannot open camera")
        
        # Lane follower test
        if car.lane_follower:
            logging.info("✅ Lane follower available")
        else:
            logging.warning("⚠️  Lane follower not available")
            
        if hasattr(car, 'end_to_end_lane_follower') and car.end_to_end_lane_follower:
            logging.info("✅ End-to-end lane follower available")
        else:
            logging.warning("⚠️  End-to-end lane follower not available")
        
        # Cleanup
        car.cleanup()
        logging.info("✅ Test mode completed successfully")
        
    except Exception as e:
        logging.error("❌ Test mode failed: %s" % str(e))


if __name__ == '__main__':
    # Log formatını ayarla
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Komut satırı argümanlarını kontrol et
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_mode()
    else:
        main() 