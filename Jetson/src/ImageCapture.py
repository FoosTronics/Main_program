"""
    Leest afbeelding uit het (video) geheugen.

    File:
      ImageCapture.py
    Date:
        20-1-2020
    Version:
        1.22
    Authors:
        Chileam Bohnen
    Used_IDE:
        PyCharm (Python 3.6.9 64-bit)
    Schemetic:
        -
    Version Management:
        1.0:
            Headers veranderd.
        1.1:
            Google docstring format toegepast op functies.
        1.20:
            Gebruik van een camera of een video bestand aangepast conform OpenCV library
        1.21:
            Doxygen commentaar toegevoegd.
        1.22:
            Spelling en grammatica commentaren nagekeken
"""

import cv2
import time

class ImageCapture:
    """
    Klasse voor het maken en ophalen van afbeeldingen met behulp van een webcam of raspi cam.

    **Author**: 
        Chileam Bohnen \n
    **Version**:
        1.22           \n
    **Date**:
        20-1-2020
    """

    def __init__(self, res=(640, 360), file=None, save=False):
        """Initialiseer de ImageCapture klasse. 
        
        Args:
            res: (tuple, optional) gewenste afbeelding resolutie(breedte, hoogte). Standaard (640, 360).
            file: (string, optional) bestandslocatie van afbeelding of video locatie. Standaard None.
            save: (bool, optional) bestandslocatie waar een opname wordt opgeslagen. Standaard False.
        """
        self.SAVE           = save
        self.FILE           = file
        self.RESOLUTION     = res
        self.FPS            = 60.0
        self.STABILIZATION  = False
        self.SHUTTER_TIME   = 0
        self.camera         = None
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
            self.camera = cv2.VideoCapture(self.FILE)
        else:
            gstream_string = self._gstreamer_pipeline()
            self.camera = cv2.VideoCapture(gstream_string, cv2.CAP_GSTREAMER)
        
        # warmup camera
        time.sleep(2)

    def get_frame(self):
        """
        Het ophalen van een afbeelding uit het geheugen.
        
        Returns:
            (np.ndarray) een afbeelding als numpy array in de vorm van [hoogte, breedte, kleurdiepte].
        """
        if self.FILE is not None:
            if ".png" in self.FILE or ".jpeg" in self.FILE:
                self.frame = cv2.imread(self.FILE)
                return cv2.resize(self.frame, self.RESOLUTION)
            else:
                ret, self.frame = self.camera.read()
                return cv2.resize(self.frame, self.RESOLUTION)
        else:
           ret, self.frame = self.camera.read()
           return self.frame

    def save_frame(self):
        """
        Het wegschrijven van een afbeelding naar het geheugen.
        """
        self.writer.write(self.frame)

    def _gstreamer_pipeline(self, capture_width=1280, capture_height=720, display_width=640,
            display_height=360, framerate=60, flip_method=0):
        """Initialisatie van de Gstreamer pipeline.

        Args:
            capture_width: (int, optional) breedte van de te nemen foto. Standaard 1280.
            capture_height: (int, optional) hoogte van de te nemen foto. Standaard 720.
            display_width: (int, optional) breedte voor het weergeven van de beelden. Standaard 640.
            display_height: (int, optional) hoogte voor het weergeven van de beelden. Standaard 360.
            framerate: (int, optional) snelheid van de camera in fps. Standaard 120.
            flip_method: (int, optional) kant waarop het camerabeeld toewijst. Standaard 2.

        Returns:
            (str) instellingen voor het aansturen van de camera met de parameters erin vewerkt.
        """
        return (
            "nvarguscamerasrc !  video/x-raw(memory:NVMM), "
            "width=1280, height=720, format=NV12, framerate=30/1 ! "
            "nvvidconv flip-method="+str(flip_method)+" ! "
            "video/x-raw, width="+str(display_width)+", height="+str(display_height)+", "
            "format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink"
            )


if __name__ == "__main__":
    file_name = "output_fast.avi"
    
    print("cv2.VideoCapture in main thread")
    print("==================================================================")
    
    capture = ImageCapture((640, 480))
    
    while True:
        start_time = time.time()
        frame = capture.get_frame()
        # print(frame)
        print("get_frame:", (time.time() - start_time) * 1000, "ms")
        cv2.imshow("frame", frame)
        key = cv2.waitKey(10)
        if key == 27:
            break
