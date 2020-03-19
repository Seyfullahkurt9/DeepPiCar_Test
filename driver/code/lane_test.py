import sys
import os
import cv2
import logging

# Hand coded lane follower'i import et
from driver.code.hand_coded_lane_follower_test_windows import HandCodedLaneFollower

def test_lane_detection():
    print("Lane Detection Test basliyor...")
    
    # Test fotograflarinin yolunu ayarla
    test_images = [
        "../data/road1_240x320.png",
        "../data/road2_240x320.png", 
        "../data/road3_240x320.png"
    ]
    
    # Lane follower'i baslatir
    lane_follower = HandCodedLaneFollower()
    
    for i, image_path in enumerate(test_images):
        if not os.path.exists(image_path):
            print("HATA: {} dosyasi bulunamadi!".format(image_path))
            continue
            
        print("Test {}: {}".format(i+1, image_path))
        
        # Goruntu yukle
        frame = cv2.imread(image_path)
        if frame is None:
            print("HATA: Goruntu yuklenemedi: {}".format(image_path))
            continue
            
        # Lane detection yap
        try:
            combo_image = lane_follower.follow_lane(frame)
            
            # Sonuclari goster
            cv2.imshow('Original Image', frame)
            cv2.imshow('Lane Detection Result', combo_image)
            
            print("Test {} tamamlandi. Devam etmek icin herhangi bir tusa basin...".format(i+1))
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        except Exception as e:
            print("Test {} hatasi: {}".format(i+1, e))
            cv2.destroyAllWindows()
    
    print("Tum testler tamamlandi!")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_lane_detection() 