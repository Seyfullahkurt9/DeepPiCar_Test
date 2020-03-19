#!/usr/bin/env python3
"""
TensorFlow Linux Test - Linux/Raspberry Pi için optimize edilmiş TensorFlow testi
"""

import logging
import sys
import os
import numpy as np


def check_tensorflow_installation():
    """TensorFlow kurulumunu kontrol et"""
    logging.info("=== TensorFlow Installation Check ===")
    
    try:
        import tensorflow as tf
        logging.info("✅ TensorFlow imported successfully")
        logging.info("TensorFlow version: %s" % tf.__version__)
        
        # GPU availability check
        try:
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                logging.info("✅ GPU devices found: %d" % len(gpus))
                for i, gpu in enumerate(gpus):
                    logging.info("   GPU %d: %s" % (i, gpu.name))
            else:
                logging.info("ℹ️  No GPU devices found (using CPU)")
        except Exception as e:
            logging.warning("⚠️  GPU check failed: %s" % str(e))
        
        # Test basic operation
        try:
            # Simple tensor operation
            a = tf.constant([1, 2, 3])
            b = tf.constant([4, 5, 6])
            c = tf.add(a, b)
            
            logging.info("✅ Basic tensor operations work")
            logging.debug("Test result: %s" % c.numpy())
            
        except Exception as e:
            logging.error("❌ Basic tensor operations failed: %s" % str(e))
            return False
        
        return True
        
    except ImportError as e:
        logging.error("❌ TensorFlow import failed: %s" % str(e))
        logging.info("Try: pip install tensorflow")
        return False
    except Exception as e:
        logging.error("❌ TensorFlow check failed: %s" % str(e))
        return False


def test_model_loading():
    """Model yükleme testleri"""
    logging.info("=== Model Loading Test ===")
    
    try:
        import tensorflow as tf
        from tensorflow import keras
        
        # Model dosyalarını ara
        model_paths = [
            '../../../models/lane_navigation/data/model_result/lane_navigation.h5',
            '../../models/lane_navigation/data/model_result/lane_navigation.h5',
            './models/lane_navigation/data/model_result/lane_navigation.h5',
            '/home/pi/deeppicar/models/lane_navigation/data/model_result/lane_navigation.h5'
        ]
        
        model_found = False
        model = None
        
        for model_path in model_paths:
            full_path = os.path.abspath(model_path)
            logging.debug("Checking model path: %s" % full_path)
            
            if os.path.exists(full_path):
                logging.info("Found model file: %s" % full_path)
                try:
                    model = keras.models.load_model(full_path)
                    logging.info("✅ Model loaded successfully")
                    logging.info("Model summary:")
                    
                    # Model bilgilerini al
                    total_params = model.count_params()
                    logging.info("   Total parameters: %d" % total_params)
                    
                    # Input/Output shapes
                    if model.input_shape:
                        logging.info("   Input shape: %s" % str(model.input_shape))
                    if model.output_shape:
                        logging.info("   Output shape: %s" % str(model.output_shape))
                    
                    model_found = True
                    break
                    
                except Exception as e:
                    logging.error("❌ Failed to load model from %s: %s" % (full_path, str(e)))
            else:
                logging.debug("Model file not found: %s" % full_path)
        
        if not model_found:
            logging.warning("⚠️  No model file found, creating test model")
            model = create_test_model()
        
        return model
        
    except Exception as e:
        logging.error("❌ Model loading test failed: %s" % str(e))
        return None


def create_test_model():
    """Test için basit bir model oluştur"""
    logging.info("Creating test model...")
    
    try:
        import tensorflow as tf
        from tensorflow import keras
        
        # Simple sequential model (Nvidia style)
        model = keras.Sequential([
            keras.layers.Lambda(lambda x: x/127.5-1.0, input_shape=(160, 320, 3)),
            keras.layers.Conv2D(24, (5, 5), strides=(2, 2), activation='elu'),
            keras.layers.Conv2D(36, (5, 5), strides=(2, 2), activation='elu'),
            keras.layers.Conv2D(48, (5, 5), strides=(2, 2), activation='elu'),
            keras.layers.Conv2D(64, (3, 3), activation='elu'),
            keras.layers.Conv2D(64, (3, 3), activation='elu'),
            keras.layers.Flatten(),
            keras.layers.Dense(100, activation='elu'),
            keras.layers.Dense(50, activation='elu'),
            keras.layers.Dense(10, activation='elu'),
            keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        
        total_params = model.count_params()
        logging.info("✅ Test model created with %d parameters" % total_params)
        
        return model
        
    except Exception as e:
        logging.error("❌ Test model creation failed: %s" % str(e))
        return None


def test_model_prediction():
    """Model tahmin testi"""
    logging.info("=== Model Prediction Test ===")
    
    try:
        # Model yükle
        model = test_model_loading()
        if model is None:
            logging.error("❌ No model available for prediction test")
            return False
        
        # Test görüntüsü oluştur
        test_image = np.random.randint(0, 255, (160, 320, 3), dtype=np.uint8)
        test_batch = np.expand_dims(test_image, axis=0)
        
        logging.info("Test image shape: %s" % str(test_batch.shape))
        
        # Tahmin yap
        prediction = model.predict(test_batch, verbose=0)
        logging.info("✅ Prediction successful")
        logging.info("Prediction result: %s" % prediction)
        
        # Steering angle kontrolü
        if prediction.shape[-1] == 1:
            steering_angle = float(prediction[0][0])
            logging.info("Predicted steering angle: %.2f degrees" % steering_angle)
            
            # Reasonable range check
            if -90 <= steering_angle <= 90:
                logging.info("✅ Steering angle in reasonable range")
            else:
                logging.warning("⚠️  Steering angle outside normal range")
        
        return True
        
    except Exception as e:
        logging.error("❌ Model prediction test failed: %s" % str(e))
        return False


def test_raspberry_pi_optimization():
    """Raspberry Pi optimizasyonlarını test et"""
    logging.info("=== Raspberry Pi Optimization Test ===")
    
    try:
        import tensorflow as tf
        
        # Thread configuration for Raspberry Pi
        tf.config.threading.set_intra_op_parallelism_threads(2)
        tf.config.threading.set_inter_op_parallelism_threads(2)
        logging.info("✅ Thread configuration optimized for RPi")
        
        # Memory growth configuration
        try:
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logging.info("✅ GPU memory growth configured")
            else:
                logging.info("ℹ️  No GPU, using CPU optimizations")
        except Exception as e:
            logging.debug("GPU memory config failed: %s" % str(e))
        
        # Test with smaller model for RPi
        logging.info("Testing lightweight model for RPi...")
        
        from tensorflow import keras
        
        # Lightweight model for RPi
        rpi_model = keras.Sequential([
            keras.layers.Lambda(lambda x: x/127.5-1.0, input_shape=(80, 160, 3)),  # Smaller input
            keras.layers.Conv2D(8, (5, 5), strides=(2, 2), activation='relu'),   # Fewer filters
            keras.layers.Conv2D(16, (3, 3), strides=(2, 2), activation='relu'),
            keras.layers.Flatten(),
            keras.layers.Dense(50, activation='relu'),  # Smaller dense layers
            keras.layers.Dense(1)
        ])
        
        rpi_model.compile(optimizer='adam', loss='mse')
        
        # Test prediction speed
        import time
        test_image = np.random.randint(0, 255, (1, 80, 160, 3), dtype=np.uint8)
        
        start_time = time.time()
        prediction = rpi_model.predict(test_image, verbose=0)
        inference_time = time.time() - start_time
        
        logging.info("✅ RPi-optimized model inference time: %.3f seconds" % inference_time)
        
        if inference_time < 0.1:  # 100ms threshold
            logging.info("✅ Inference speed acceptable for real-time")
        else:
            logging.warning("⚠️  Inference speed may be too slow for real-time")
        
        return True
        
    except Exception as e:
        logging.error("❌ RPi optimization test failed: %s" % str(e))
        return False


def check_dependencies():
    """Gerekli bağımlılıkları kontrol et"""
    logging.info("=== Dependencies Check ===")
    
    dependencies = {
        'numpy': 'numpy',
        'cv2': 'opencv-python',
        'keras': 'keras',
        'PIL': 'Pillow'
    }
    
    available = []
    missing = []
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            available.append(module)
            logging.info("✅ %s available" % module)
        except ImportError:
            missing.append(package)
            logging.error("❌ %s missing (install: pip install %s)" % (module, package))
    
    if missing:
        logging.error("Missing dependencies: %s" % missing)
        return False
    else:
        logging.info("✅ All dependencies available")
        return True


def main():
    """Ana test fonksiyonu"""
    logging.info("TensorFlow Linux Test Starting...")
    
    # System info
    logging.info("Python version: %s" % sys.version)
    logging.info("Platform: %s" % sys.platform)
    
    # Check dependencies first
    if not check_dependencies():
        logging.error("Dependencies check failed!")
        return False
    
    # TensorFlow installation check
    if not check_tensorflow_installation():
        logging.error("TensorFlow installation check failed!")
        return False
    
    # Model loading test
    model = test_model_loading()
    if model is None:
        logging.warning("Model loading failed, but continuing with other tests")
    
    # Prediction test
    if not test_model_prediction():
        logging.warning("Model prediction test failed")
    
    # Raspberry Pi optimizations
    if not test_raspberry_pi_optimization():
        logging.warning("RPi optimization test failed")
    
    logging.info("✅ TensorFlow Linux test completed")
    return True


if __name__ == '__main__':
    # Setup logging
    log_level = logging.DEBUG if '-v' in sys.argv else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("TensorFlow Linux Test Suite")
    
    if main():
        logging.info("✅ All tests completed!")
        sys.exit(0)
    else:
        logging.error("❌ Some tests failed!")
        sys.exit(1) 