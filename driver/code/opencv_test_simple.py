import cv2
import sys

def main():
    print("OpenCV kamera testi basliyor...")
    print("Kameraya erismege calisiyor...")
    
    # Windows'ta genellikle 0 ilk kameradır
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("HATA: Kameraya erisilemedi!")
        print("Cozum onerileri:")
        print("   - Bilgisayarinizda webcam var mi kontrol edin")
        print("   - Baska program kamerayi kullaniyor olabilir")
        print("   - Windows kamera izinlerini kontrol edin")
        return False
    
    print("Kamera basariyla acildi!")
    print("'q' tusuna basarak cikabilirsiniz")
    
    camera.set(3, 640)
    camera.set(4, 480)
    
    frame_count = 0
    while camera.isOpened():
        ret, image = camera.read()
        
        if not ret:
            print("Kameradan goruntu alinamadi!")
            break
            
        frame_count += 1
        if frame_count % 30 == 0:  # Her 30 frame'de bir yazdır
            print("{} frame islendi...".format(frame_count))
        
        cv2.imshow('Original', image)
        
        b_w_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imshow('B/W', b_w_image)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    camera.release()
    cv2.destroyAllWindows()
    print("OpenCV test tamamlandi!")
    return True

if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        print("Beklenmeyen hata: {}".format(e))
        sys.exit(1) 