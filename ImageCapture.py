# imports
import cv2
import time

from src.FileVideoStream import *

"""
Afbeeldingen ophalen uit video geheugen

File:
    ImageProcessing.py
Date:
    15.11.2019
Version:
    V1.0
Authors:
    Chileam Bohnen
Used_IDE:
    PyCharm (Python 3.6.9 64-bit)
"""

class ImageCapture:
    """
    Klasse voor het maken en ophalen van afbeeldingen met behulp van een webcam of raspi cam.
    """

    def __init__(self, res, file=None, save=False):
        """
        Initalisatie van klasse object
        
        Args:
            res (tuple): Gewenste afbeelding resolutie (breedte, hoogte)
            file (str, optional): Bestandlocatie van afbeelding of video locatie. Standaard waarde is None.
            save (bool, optional): Bestandlocatie waar een opnamen wordt opgeslagen. Standaard waarde is None.
        """
        self.SAVE           = save
        self.FILE           = file
        self.RESOLUTION     = res
        self.FPS            = 30.0
        self.STABILIZATION  = False
        self.SHUTTER_TIME   = 0
        self.camera         = FileVideoStream
        self.fourcc         = cv2.VideoWriter_fourcc(*'XVID')
        self.writer         = None
        self.frame          = []

        # set camera parameters and heat up
        self.start_camera()

    def start_camera(self):
        """
        Het configuren van het camera object.
        """
        print("start camera...")
        if self.SAVE:
            self.writer = cv2.VideoWriter(self.FILE, self.fourcc, self.FPS, self.RESOLUTION)
            self.camera = cv2.VideoCapture(0)
            return

        if self.FILE is not None:
            self.camera = FileVideoStream(self.FILE, 16).start()
        else:
            self.camera = cv2.VideoCapture(0)

    def get_frame(self):
        """
        Het ophalen van een afbeelding uit het geheugen.
        
        Returns:
            numpy.ndarray: Een afbeelding als numpy array in de vorm van [hoogte, breedte, kleurdiepte]
        """
        return self.camera.read()

    def save_frame(self):
        """
        Het wegschrijven van een afbeelding naar het geheugen.
        """
        self.writer.write(self.frame)

if __name__ == "__main__":
    file_name = "output_fast.avi"
    
    print("cv2.VideoCapture in main thread")
    print("==================================================================")
    
    capture = ImageCapture((640, 480), file_name)
    
    while True:
        start_time = time.time()
        frame = capture.get_frame()
        print(frame)
        print("get_frame:", (time.time() - start_time) * 1000, "ms")
        cv2.imshow("frame", frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
    
    print("")
    print("cv2.VideoCapture in new thread")
    print("==================================================================")
    
    fvs = FileVideoStream(file_name, 8).start()
    time.sleep(0.1)
    
    while fvs.more():
        start_time = time.time()
        frame = fvs.read()
        print("get_frame:", (time.time() - start_time) * 1000, "ms")
        cv2.imshow("frame", frame)
        print("Queue size:", fvs.Q.qsize())
        key = cv2.waitKey(1)
        if key == 27:
            break
