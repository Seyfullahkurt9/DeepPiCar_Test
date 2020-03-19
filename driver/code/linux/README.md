# DeepPiCar Linux Fixed Versions

Bu klasör Windows'ta tespit edilen sorunların Linux/Raspberry Pi için düzeltilmiş versiyonlarını içerir.

## 🔧 Windows'ta Tespit Edilen Sorunlar ve Linux Çözümleri

### 1. Sıfıra Bölme Hatası (OverflowError)
**Sorun:** `make_points` fonksiyonunda slope=inf olduğunda sistem çöküyor
**Çözüm:** `hand_coded_lane_follower_fixed.py`'da matematik kontrolü eklendi

### 2. Path Sorunları
**Sorun:** Hard-coded Linux path'leri Windows'ta çalışmıyor
**Çözüm:** `end_to_end_lane_follower_fixed.py`'da multiple path check eklendi

### 3. Hardware Availability
**Sorun:** PiCar kütüphaneleri yoksa sistem başlamıyor
**Çözüm:** `deep_pi_car_fixed.py`'da hardware fallback sistemi eklendi

### 4. Camera Detection
**Sorun:** Kamera index'i sistemlerde farklı olabiliyor
**Çözüm:** Multiple camera source denemesi eklendi

## 📁 Dosyalar

### Core Files
- **`hand_coded_lane_follower_fixed.py`** - Matematik hatası düzeltilmiş lane follower
- **`end_to_end_lane_follower_fixed.py`** - Path ve error handling iyileştirilmiş AI model
- **`deep_pi_car_fixed.py`** - Hardware check ve fallback'li ana sistem
- **`driver_main_fixed.py`** - Gelişmiş ana driver, prerequisites check ile
- **`traffic_objects_test_fixed.py`** - Linux'a uyarlanmış traffic objects test suite
- **`opencv_test_linux.py`** - Linux/RPi kamera test sistemi  
- **`tensorflow_test_linux.py`** - Linux/RPi TensorFlow test ve optimizasyon

### Önemli Düzeltmeler

#### hand_coded_lane_follower_fixed.py
```python
# CRITICAL FIX: Windows'ta bulduğumuz sıfıra bölme kontrolü
if abs(slope) < 0.001:  # slope sıfıra çok yakınsa
    logging.info('Detected near-vertical line, using center vertical line')
    return [[int(width/2), y1, int(width/2), y2]]  # dikey çizgi döndür
```

#### end_to_end_lane_follower_fixed.py
```python
# Linux path için model dosyasını bul - multiple locations check
possible_paths = [
    '/home/pi/DeepPiCar/models/lane_navigation/data/model_result/lane_navigation.h5',
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models', 'lane_navigation', 'data', 'model_result', 'lane_navigation.h5'),
    './models/lane_navigation/data/model_result/lane_navigation.h5',
    '../models/lane_navigation/data/model_result/lane_navigation.h5'
]
```

#### deep_pi_car_fixed.py
```python
# Hardware import with fallback
try:
    import picar
    HARDWARE_AVAILABLE = True
except ImportError as e:
    logging.warning("PiCar hardware not available: %s" % str(e))
    HARDWARE_AVAILABLE = False
    # Mock hardware için fallback sistemi
```

## 🚀 Kullanım

### Sistem Kontrol
```bash
python end_to_end_lane_follower_fixed.py 3  # Sistem kontrolü
```

### Lane Following Test
```bash
# Hand-coded lane follower
python hand_coded_lane_follower_fixed.py

# End-to-end AI model
python end_to_end_lane_follower_fixed.py 1  # Photo test
python end_to_end_lane_follower_fixed.py 2  # Live test

# Ana sistem (gelişmiş sürüm)
python driver_main_fixed.py         # Normal mod
python driver_main_fixed.py test    # Test modu

# Original sistem
python deep_pi_car_fixed.py
```

### Test Systems
```bash
# OpenCV ve kamera testi
python opencv_test_linux.py         # Normal test
python opencv_test_linux.py -v      # Verbose test

# TensorFlow ve model testi  
python tensorflow_test_linux.py     # Normal test
python tensorflow_test_linux.py -v  # Verbose test

# Traffic objects testi
python traffic_objects_test_fixed.py 1   # Basic test
python traffic_objects_test_fixed.py 2   # Real objects test
python traffic_objects_test_fixed.py 3   # System check
python traffic_objects_test_fixed.py 4   # All tests
```

## 🔍 Raspberry Pi Kontrolleri

Sistem otomatik olarak şunları kontrol eder:
- Raspberry Pi hardware detection
- GPIO availability check
- Camera device presence (`/dev/video0`, `/dev/video1`)
- Model file locations
- Permission levels (root access)

## 📊 Beklenen İyileştirmeler

Windows testlerinden öğrendiğimiz derslere göre bu versiyon:
- ✅ Sıfıra bölme hatalarını önler
- ✅ Multiple camera source'u dener  
- ✅ Model bulunamazsa graceful degradation yapar
- ✅ Hardware yoksa mock mode'da çalışır
- ✅ Comprehensive error logging yapar
- ✅ System requirements check yapar

## 🔧 Kurulum

```bash
# Raspberry Pi'de gerekli paketler
sudo apt update
sudo apt install python3-opencv python3-numpy

# Python paketleri
pip3 install tensorflow keras

# PiCar kütüphanesi (hardware varsa)
# https://github.com/sunfounder/SunFounder_PiCar-V
```

## ⚠️ Notlar

- Bu kodlar test edilmemiştir (Raspberry Pi donanımı yok)
- Windows'ta tespit edilen sorunların çözümlerini içerir
- Gerçek Raspberry Pi'de additional tuning gerekebilir
- GPIO permissions için `sudo` gerekebilir

---
*Windows geliştirme deneyiminden Linux adaptasyonu* 