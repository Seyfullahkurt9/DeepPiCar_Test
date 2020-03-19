#!/usr/bin/env python3
"""
OpenCV Linux Test - Linux/Raspberry Pi için optimize edilmiş kamera testi
"""

import cv2
import os
import logging
import sys
import datetime

def get_camera_info(cap):
    """Kamera bilgilerini al"""
    if not cap.isOpened():
        return {}
    
    info = {}
    info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    info['fps'] = cap.get(cv2.CAP_PROP_FPS)
    info['fourcc'] = int(cap.get(cv2.CAP_PROP_FOURCC))
    
    return info


def test_camera_sources():
    """Farklı kamera kaynaklarını test et"""
    logging.info("=== Camera Sources Test ===")
    
    camera_sources = [0, 1, 2, '/dev/video0', '/dev/video1']
    working_cameras = []
    
    for source in camera_sources:
        try:
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    info = get_camera_info(cap)
                    logging.info("✅ Camera %s works: %dx%d" % (source, info.get('width', 0), info.get('height', 0)))
                    working_cameras.append((source, info))
                else:
                    logging.warning("⚠️  Camera %s opens but can't read frames" % source)
                cap.release()
            else:
                logging.debug("❌ Camera %s cannot be opened" % source)
        except Exception as e:
            logging.debug("❌ Camera %s error: %s" % (source, str(e)))
    
    return working_cameras


def test_raspberry_pi_camera():
    """Raspberry Pi kamerasını özel olarak test et"""
    logging.info("=== Raspberry Pi Camera Test ===")
    
    try:
        # Raspberry Pi kamerası için özel ayarlar
        cap = cv2.VideoCapture(0)
        
        # Raspberry Pi camera için optimal ayarlar
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        if cap.isOpened():
            info = get_camera_info(cap)
            logging.info("RPi Camera configured: %dx%d @ %.1f fps" % 
                        (info['width'], info['height'], info['fps']))
            
            # Test frame capture
            ret, frame = cap.read()
            if ret:
                logging.info("✅ RPi Camera frame capture successful")
                return cap
            else:
                logging.error("❌ RPi Camera cannot capture frames")
        else:
            logging.error("❌ RPi Camera cannot be opened")
        
        cap.release()
        
    except Exception as e:
        logging.error("❌ RPi Camera test failed: %s" % str(e))
    
    return None


def main():
    """Ana test fonksiyonu"""
    logging.info("OpenCV Linux Camera Test Starting...")
    
    # System info
    logging.info("OpenCV version: %s" % cv2.__version__)
    logging.info("Platform: %s" % sys.platform)
    
    # Test different camera sources
    working_cameras = test_camera_sources()
    
    if not working_cameras:
        logging.error("No working cameras found!")
        return False
    
    # Use first working camera
    camera_source, camera_info = working_cameras[0]
    logging.info("Using camera: %s" % camera_source)
    
    # Raspberry Pi specific test
    rpi_cap = test_raspberry_pi_camera()
    if rpi_cap:
        cap = rpi_cap
    else:
        cap = cv2.VideoCapture(camera_source)
    
    if not cap.isOpened():
        logging.error("Cannot open camera %s" % camera_source)
        return False
    
    # Create output directory
    output_dir = '/home/pi/deeppicar_test' if os.path.exists('/home/pi') else './test_output'
    os.makedirs(output_dir, exist_ok=True)
    logging.info("Output directory: %s" % output_dir)
    
    # Camera test loop
    frame_count = 0
    max_frames = 100  # Linux'ta daha az frame test edelim
    
    logging.info("Starting camera capture test...")
    logging.info("Press 'q' to quit early")
    
    while frame_count < max_frames:
        ret, frame = cap.read()
        
        if not ret:
            logging.error("Failed to capture frame %d" % frame_count)
            break
        
        frame_count += 1
        
        # Her 10 frame'de bir bilgi ver
        if frame_count % 10 == 0:
            logging.info("Captured %d frames" % frame_count)
        
        # Her 25 frame'de bir kaydet
        if frame_count % 25 == 0:
            filename = os.path.join(output_dir, 'test_frame_%03d.jpg' % frame_count)
            cv2.imwrite(filename, frame)
            logging.info("Saved frame: %s" % filename)
        
        # Display frame if possible (X11 forwarding or local display)
        try:
            cv2.imshow('Linux Camera Test', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logging.info("User requested quit")
                break
        except cv2.error:
            # No display available, continue without showing
            pass
    
    # Test summary
    logging.info("=== Test Summary ===")
    logging.info("Total frames captured: %d" % frame_count)
    logging.info("Camera source: %s" % camera_source)
    logging.info("Frame size: %dx%d" % (camera_info.get('width', 0), camera_info.get('height', 0)))
    
    # Performance check
    if frame_count >= max_frames:
        logging.info("✅ Camera test completed successfully")
        success = True
    elif frame_count > max_frames // 2:
        logging.warning("⚠️  Camera test partially successful (%d/%d frames)" % (frame_count, max_frames))
        success = True
    else:
        logging.error("❌ Camera test failed (%d/%d frames)" % (frame_count, max_frames))
        success = False
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    return success


def check_opencv_installation():
    """OpenCV kurulumunu kontrol et"""
    logging.info("=== OpenCV Installation Check ===")
    
    try:
        import cv2
        logging.info("✅ OpenCV imported successfully")
        logging.info("OpenCV version: %s" % cv2.__version__)
        
        # Build info
        build_info = cv2.getBuildInformation()
        logging.debug("OpenCV build info: %s" % build_info)
        
        # Video support check
        backends = cv2.videoio_registry.getBackends()
        logging.info("Video backends: %s" % [cv2.videoio_registry.getBackendName(b) for b in backends])
        
        return True
        
    except ImportError as e:
        logging.error("❌ OpenCV import failed: %s" % str(e))
        return False
    except Exception as e:
        logging.error("❌ OpenCV check failed: %s" % str(e))
        return False


if __name__ == '__main__':
    # Setup logging
    log_level = logging.DEBUG if '-v' in sys.argv else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("OpenCV Linux Test Suite")
    
    # Check OpenCV installation first
    if not check_opencv_installation():
        logging.error("OpenCV installation check failed!")
        sys.exit(1)
    
    # Run main test
    if main():
        logging.info("✅ All tests passed!")
        sys.exit(0)
    else:
        logging.error("❌ Some tests failed!")
        sys.exit(1) 