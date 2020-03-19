import os
import sys
import cv2
import logging
import numpy as np
import warnings

# Comprehensive warning suppression
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress all TensorFlow messages
os.environ['TF_SILENCE_ALL_WARNINGS'] = '1'

# Suppress Python warnings
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# TensorFlow import test with warning suppression
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import tensorflow as tf
        
        # Additional TensorFlow warning suppression
        tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
    
    print("TensorFlow version: {}".format(tf.__version__))
except ImportError as e:
    print("TensorFlow import hatasi: {}".format(e))
    sys.exit(1)

# Keras import test with modern style
try:
    # Try TensorFlow 2.x style first
    try:
        from tensorflow.keras.models import load_model
        print("Keras basariyla import edildi (TensorFlow 2.x style)")
    except (ImportError, AttributeError):
        # Fallback to legacy style
        from keras.models import load_model
        print("Keras basariyla import edildi (legacy style)")
except ImportError as e:
    print("Keras import hatasi: {}".format(e))
    sys.exit(1)

def test_model_loading():
    """Model yuklenebiliyor mu test et"""
    model_path = "../../models/lane_navigation/data/model_result/lane_navigation.h5"
    
    if not os.path.exists(model_path):
        print("HATA: Model dosyasi bulunamadi: {}".format(model_path))
        return False
        
    try:
        print("Model yukleniyor: {}".format(model_path))
        
        # Suppress warnings during model loading
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = load_model(model_path)
            
        print("Model basariyla yuklendi!")
        print("Model summary:")
        model.summary()
        return True
        
    except Exception as e:
        print("Model yukleme hatasi: {}".format(e))
        return False

def test_image_preprocessing():
    """Goruntu on isleme testleri"""
    test_images = [
        "../../models/lane_navigation/data/images/video01_000_085.png",
        "../../models/lane_navigation/data/images/video01_001_080.png",
        "../../models/lane_navigation/data/images/video01_002_077.png"
    ]
    
    for image_path in test_images:
        if not os.path.exists(image_path):
            print("Test resmi bulunamadi: {}".format(image_path))
            continue
            
        print("Test resmi: {}".format(image_path))
        
        # Resmi yukle
        image = cv2.imread(image_path)
        if image is None:
            print("Resim yuklenemedi!")
            continue
            
        # On isleme (end_to_end_lane_follower.py'deki img_preprocess fonksiyonu)
        height, _, _ = image.shape
        processed = image[int(height/2):,:,:]  # remove top half
        processed = cv2.cvtColor(processed, cv2.COLOR_BGR2YUV)  # YUV color space
        processed = cv2.GaussianBlur(processed, (3,3), 0)
        processed = cv2.resize(processed, (200,66)) # Nvidia model input size
        processed = processed / 255 # normalize
        
        print("Original shape: {}, Processed shape: {}".format(image.shape, processed.shape))
        
        # Gorselleri goster
        cv2.imshow('Original', image)
        cv2.imshow('Processed', processed)
        cv2.waitKey(1000)  # 1 saniye bekle
        cv2.destroyAllWindows()
        
        return True
    
    return False

def main():
    print("=== TensorFlow Lane Following Model Test ===")
    
    # 1. Model yukleme testi
    print("\n1. Model yukleme testi...")
    if not test_model_loading():
        print("Model yukleme basarisiz!")
        return
    
    # 2. Goruntu on isleme testi  
    print("\n2. Goruntu on isleme testi...")
    if not test_image_preprocessing():
        print("Goruntu on isleme testi basarisiz!")
        return
        
    print("\n=== TUM TESTLER BASARILI ===")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main() 