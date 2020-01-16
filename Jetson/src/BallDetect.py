"""
    Detecting the ball on the field. 

    File:
        BallDetectClass.py
    Date:
        15-11-2019
    Version:
        3.1
    Authors:
        Sipke Vellinga
    Used_IDE:
        Pycharm (Python 3.6.7 64-bit)
    Schematic:
        -
    Version management:
        2.1:
            __init__ aangepast
        3.0:
            def getimageFrame en def getvideoFrame samengevoegd
        3.1:
            def showFrame opgeschoond
"""

import numpy as np
import cv2
import imutils

center2 = (0, 0)

class BallDetection: #of Beeldherkenning?

    def __init__(self, file=None):
        """
        Lijst van vaste parameters
        Args:
            file: bestand voor de input van de frames
        """
        self.ilowY  =       110 # 0
        self.ihighY =       255 # 255
        self.ilowU  =       65 # 0
        self.ihighU =       255 # 111
        self.ilowV  =       180 # 0
        self.ihighV =       255 # 150
        self.mask   =       []
        self.dim    =       (640, 480)
        self.frame_capture =[]

        if type(file) == str:
            if file.split(".")[-1] == "png" or file.split(".")[-1] == "jpg":
                self.frame = cv2.imread(file)
                self.frame_capture = "image"
            else:
                self.cap = cv2.VideoCapture(file)
                #self.frame = [] is deze nodig?
                self.frame_capture = "video"
        else:
            self.frame  = file
        self.center = (0, 0)

    def _callback(self, x):
        """
        Functienaam voor het aanmaken van de trackbar. De trackbar genereert een pointer
        die deze functie aanroept wanneer de slider van positie verandert.
        #underscore is voor lokaal gebruik
        """
        pass

    def create_trackbar(self):
        """
        Maakt een trackbar aan waarmee de parameters van de gedefinieerde kleurruimte
        veranderd kunnen worden.
        """
        cv2.namedWindow('Trackbar')

        cv2.createTrackbar('lowY', 'Trackbar', self.ilowY, 255, self._callback)
        cv2.createTrackbar('highY', 'Trackbar', self.ihighY, 255, self._callback)

        cv2.createTrackbar('lowU', 'Trackbar', self.ilowU, 255, self._callback)
        cv2.createTrackbar('highU', 'Trackbar', self.ihighU, 255, self._callback)

        cv2.createTrackbar('lowV', 'Trackbar', self.ilowV, 255, self._callback)
        cv2.createTrackbar('highV', 'Trackbar', self.ihighV, 255, self._callback)

    def get_trackbarpos(self):
        """
        Slaat de ingestelde waardes van de trackbar op in de variabelen.
        """
        self.ilowY = cv2.getTrackbarPos('lowY', 'Trackbar')
        self.ihighY = cv2.getTrackbarPos('highY', 'Trackbar')

        self.ilowU = cv2.getTrackbarPos('lowU', 'Trackbar')
        self.ihighU = cv2.getTrackbarPos('highU', 'Trackbar')

        self.ilowV = cv2.getTrackbarPos('lowV', 'Trackbar')
        self.ihighV = cv2.getTrackbarPos('highV', 'Trackbar')

    def getball_pos(self):
        """
        Roept de functies aan die nodig zijn om de bal te detecteren

        Returns: Geeft de x,y pixel positie van de bal terug
        """
        #self.getFrame()
        #self.get_trackbarpos()
        self.imageFilter()
        self.ball_detect()
        #self.showFrame()

        return self.center

    def new_frame(self, img):
        self.frame = img

    def getFrame(self):
        """
        Haalt een frame binnen en resized deze
        Returns: Geeft de geresizede image terug
        """
        if self.frame_capture == 'video':
            ret, frame_capture = self.cap.read()
            cv2.waitKey(10)
            if frame_capture is not None:
                self.frame = cv2.resize(frame_capture, self.dim)
                return self.frame
        elif self.frame_capture == 'image':
            self.frame = cv2.resize(self.frame, self.dim)
            return self.frame

    # TODO Video frame via ImageCapture
    # def getvideoFrame(self):
    #     """
    #     Haalt een frame op van een vooraf gedefinieerd medium (file) zoals een afbeelding, video of livestream.
    #
    #     Returns: Geeft het beeld terug die de read() functie heeft opgepikt.
    #
    #     """
    #     ret, frame_capture = self.cap.read()
    #     cv2.waitKey(10)
    #     if frame_capture is not None:
    #         self.frame = cv2.resize(frame_capture, self.dim)
    #         return self.frame

    def imageFilter(self):
        """
        Set van beeldfilters waarmee een mask wordt gecreeerd om de bal te kunnen volgen.
        """
        yuv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2YUV)
        #blur = cv2.blur(yuv, (5, 5))
        #gaussian = cv2.GaussianBlur(yuv, (3, 3), 0)
        yuvlower = np.array([self.ilowY, self.ilowU, self.ilowV])
        yuvupper = np.array([self.ihighY, self.ihighU, self.ihighV])
        mask_inrange = cv2.inRange(yuv, yuvlower, yuvupper)
        mask_inrange = cv2.erode(mask_inrange, None, iterations=2)
        self.mask = cv2.dilate(mask_inrange, None, iterations=3)
        #cv2.imshow("mask", self.mask)

    def ball_detect(self):
        """
        Volgt de bal op het speelveld met behulp van de functie imageFilter
        #Adrian Rosebrock https://www.pyimagesearch.com/2015/09/14/ball-tracking-with-opencv/
        """
        # Vind de contouren in het masker en
        # initialiseer het huidige (x, y) middelpunt van de bal
        global center2
        cnts = cv2.findContours(self.mask, cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        #self.center = None

        # Ga alleen verder als er tenminste één contour aanwezig is
        if len(cnts) > 0:
            # vind het grootste contour in het masker en gebruik deze
            # om de minimale enclosing circle en centroid te berekenen
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            self.center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            # Ga alleen verder als de radius een minimaal grootte heeft
            if radius > 2:
                #teken de cirkel en centroid op het frame
                cv2.circle(self.frame, (int(x), int(y)), int(radius),
                           (0, 255, 255), 2)
                cv2.circle(self.frame, self.center, 5, (0, 0, 255), -1)
                center2 = self.center
                return center2

        if self.center == (0, 0):
            self.center = center2

    def showFrame(self):
        """
        Laat het beeld zien dat met de getFrame functie is opgehaald
        """
        print(self.center)
        cv2.putText(self.frame, str(self.center), (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("FrameYUV", self.frame)

        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     if self.frame_capture == 'video':
        #         self.cap.release()
        #     cv2.destroyAllWindows()



if __name__ == "__main__":
    """
    test script om te testen of de code het doet. 
    De code checkt in: /Test foto's/ball/   map naar alle foto's en stuurt deze in de class om te testen. 
    """
    from glob import glob

    # ! zorg dat de goede map wordt geselecteerd.
    files = glob("D:\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\oud\\V1.3 cam normal Wide angle\\*.png")

    files.sort()
    detect_ball = BallDetection()

    for file in files:  #check per file
        #code vanaf BallDetectionMain.py
        img = cv2.imread(file)
        detect_ball.new_frame(img)
        detect_ball.create_trackbar()
        while True:
            detect_ball.get_trackbarpos()
            pos = detect_ball.getball_pos()
            print("ball pos:", pos)
            cv2.imshow("ball", detect_ball.frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
