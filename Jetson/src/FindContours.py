#pylint disable=E1101

"""
    Code to find the contours of the table. This can be done in the init of the application. 

    File:
        find_countours.py
    Date:
        13-11-2019
    Version:
        1.1
    Modifier / Authors:
        Kelvin Sweere
        Chileam Bohnen
    Used_IDE:
        Pycharm (Python 3.6.7 64-bit)
    Schematic:
        -
    Version management:
        1.0:
            Headers veranderd.
        1.1:
            Google docstring format toegepast op functies.
        1.2:
            Constanten WIDTH en HEIGHT op 640 x 360 gezet
"""

import numpy as np
import cv2
from src.Backend.Extra import *

if __name__ == "__main__":
    from glob import glob

class FindContours:
    def __init__(self, debug=False):
        """Init van de Raster class
        
        Args:
            debug (bool, optional): Keuze of trackbars worden aangemaakt. Defaults to False.
        """

        self.biggest_contour = None
        self.gray_threshold = 160
        self.gray_cropped_threshold = 100   #was 120! --> oorzaak failed test 13-11-2019
        self.WIDTH = 640    #constante, hoogte van het beeld
        self.HEIGHT = 360   #constante, breedte van het beeld
        self.mask = None
        self.cropped_mask = None
        self.img = []
        self.drawing_img = []
        self.cropped_img = []
        self.return_img = []
        self.contour = []
        self.PIXEL_WIDTH = 10   #extra speling bij de gecropte images
        self.MAX_OPP = self.WIDTH * self.HEIGHT

        # manuel cropping parameters
        self.left_border = 55
        self.right_border = 595
        self.top_border = 35
        self.bottom_border = 445

        cv2.namedWindow("Manuel cropping")
        cv2.createTrackbar("Left border", "Manuel cropping", self.left_border, self.WIDTH, nothing)
        cv2.createTrackbar("Right border", "Manuel cropping", self.right_border, self.WIDTH, nothing)
        cv2.createTrackbar("Top border", "Manuel cropping", self.top_border, self.HEIGHT, nothing)
        cv2.createTrackbar("Bottom border", "Manuel cropping", self.bottom_border, self.HEIGHT, nothing)

        # debug mode for frame and field contour detection
        self.debug = debug
        if debug:
            cv2.namedWindow("Trackbars")
            cv2.createTrackbar("gray_threshold", "Trackbars", self.gray_threshold, 255, nothing)
            cv2.createTrackbar("gray_cropped_threshold", "Trackbars", self.gray_cropped_threshold, 255, nothing)

    def _get_table_threshold(self):
        """bewerk een grayscale img, zodat een mask waarop contours getekend kan worden over blijft.

        Args:
          img (np.array): orginele img in BGR format. Wordt later omgezet in grayscale.

        Returns:
            filt (np.array): gefilterde image van het orgineel.
        """
        # Settings uit slider.py gehaald
        gray = cv2.cvtColor(self.drawing_img, cv2.COLOR_BGR2GRAY)
        if self.debug:
            self.gray_threshold = cv2.getTrackbarPos("gray_threshold", "Trackbars")
        _, filt = cv2.threshold(gray, self.gray_threshold, 255, cv2.THRESH_BINARY)
        # return nieuwe image.
        return filt

    def _get_field_threshold(self, cropped):
        """bewerk een gecropte img, zodat een mask waarop contours getekend kan worden over blijft.

        Args:
          img (np.array): gecropte img in BGR format. Wordt later omgezet in grayscale.

        Returns:
            filt (np.array): gefilterde image van het orgineel.
        """
        cropped_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        if self.debug:
            self.gray_cropped_threshold = cv2.getTrackbarPos("gray_cropped_threshold", "Trackbars")
        _, filt = cv2.threshold(cropped_gray, self.gray_cropped_threshold, 255, cv2.THRESH_BINARY)
        return filt

    def _rotated_table(self, contour):
        """roteer de tafel, zodat de contour haaks komt te staan.
        
        Args:
            contour (np.array): Contour die recht gezet wordt.
        """
        _rect = cv2.minAreaRect(contour)
        center, shape, angle = _rect
        if angle < -45:
            angle += 90

        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        self.img = cv2.warpAffine(self.img, rot_mat, self.img.shape[1::-1], flags=cv2.INTER_LINEAR)
        self.drawing_img = cv2.warpAffine(self.drawing_img, rot_mat, self.img.shape[1::-1], flags=cv2.INTER_LINEAR)

    #krijg alleen tafel te zien (wit)
    def _get_white(self):        
        """bewerk een YUV img, zodat een mask waarop contours getekend kan worden over blijft.

        Args:
          img (np.array): orginele img in BGR format. Wordt later omgezet in YUV.

        Returns:
            filt (np.array): gefilterde zwart/wit image van het orgineel.
        """

        # Settings uit slider.py gehaald
        LOWHUE = 0  
        LOWSAT = 0
        LOWVAL = 0

        HIGHHUE = 220
        HIGHSAT = 240
        HIGHVAL = 235

        yuv = cv2.cvtColor(self.img, cv2.COLOR_BGR2YUV)
        colorLow = np.array([LOWHUE, LOWSAT, LOWVAL])
        colorHigh = np.array([HIGHHUE, HIGHSAT, HIGHVAL])
        #voeg filter toe
        mask = cv2.inRange(yuv, colorLow, colorHigh)
        ###############

        #Zorg dat de stijle lijnen beter worden weergegeven.
        # kernal = cv.getStructuringElement(cv.MORPH_ELLIPSE, (7, 7))
        mask = cv2.medianBlur(mask, 7)
        mask = cv2.bilateralFilter(mask, 15, 75, 75)

        filt = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, mask)
        filt = cv2.morphologyEx(filt, cv2.MORPH_OPEN, filt)
        
        # return nieuwe image.
        return filt

    def _calculate_area(self, cor1, cor2):            
        """berekend het oppervlakte wat tussen twee punten is bevestigd. 
        
        Args:
            cor1 ((int, int)): x,y cordinaat van linker boven hoek.
            cor2 ((int, int)): x,y cordinaat van recher onder hoek.
        
        Returns:
            int: oppervlakte tussen beide cordinaten.
        """
        x = abs(cor2[0] - cor1[0])
        y = abs(cor2[1] - cor1[1])
        return x*y

    def _find_table_contour(self, mask):
        """Vind het contour van de tafel met de gefilterde img van de tafel.
        
        Args:
            filt (np.array): mask van orginele img. Hier worden de contours over 
        
        Returns:
            (tuple): grootste contour die aanwezig is in de gefilterde img (input).
        """

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        biggest_current_opp = 0

        for contour in contours:
            _rect = cv2.minAreaRect(contour)
            _box = cv2.boxPoints(_rect)
            _box = np.int0(_box) 

            opp = self._calculate_area(tuple(_box[0]), tuple(_box[2])) #return opp van de contours
            # cv.drawContours(self.img, contour, -1, (0,0,255), 3)

            # check of het oppervlakte de grootste is die aanwezig is.
            if (opp > biggest_current_opp and opp < self.MAX_OPP):
                biggest_current_opp = opp
                self.biggest_contour = _box

        return self.biggest_contour

    def _crop_img_till_contour(self, _img, contour=None):
        """Crop een 'orginele' img naar een gecropte img.
        
        Args:
            img (np.darray): img die gecropt moet worden tot de cordinaten.
            contour_cor (tuple): cordinaten van de contours waar deze gecropt moet worden.
        
        Returns:
            (np.darray): gecropte image van het orgineel.
        """
        if contour is None:
            return _img[self.top_border:self.bottom_border, self.left_border:self.right_border]
        else:
            x, y, w, h = cv2.boundingRect(contour)
        return _img[y:y+h, x:x+w]

    def get_table_now(self):
        """
        High-level API, die gelijk de gecropte img teruggeeft van de tafel.
        
        Args:
            img (np.darray): input image van de (ongefilterde) tafel.
            filt (bool, optional): kies of de img wordt teruggegeven (False),
            of dat de gefilterde img wordt teruggegeven (True). Defaults to False.
        
        Returns:
            np.darray: gecropte image van de tafel.
        """
        
        self.mask = self._get_white()  # get black/white image
        self.contour = self._find_table_contour(self.mask)
        self.mask = self._crop_img_till_contour(self.mask)  #resize mask
        self.img = self._crop_img_till_contour(self.img)    #resize img
        return self.img

    def get_cropped_field(self, threshold=False):
        """
        High-level API, die gelijk de gecropte img teruggeeft van het veld.

        Args:
            threshold (bool, optional): de contouren van de tafel en veld worden gebruikt (True),
            of handmatig wordt het gebied ingesteld (False). Defaults to False.

        Returns:
            numpy.darray: gecropte image van het speel veld.
        """
        if threshold:
            self.mask = self._get_table_threshold()
            contour = self._find_table_contour(self.mask)

            # draw black border around contour
            cv2.drawContours(self.drawing_img, [contour], -1, (0, 0, 0), 45)

            # rotate img
            self._rotated_table(contour)

            self.cropped_img = self._crop_img_till_contour(self.drawing_img, contour)

            self.cropped_mask = self._get_field_threshold(self.cropped_img) #krijg mask terug.
            contour = self._find_table_contour(self.cropped_mask)
            self.return_img = self._crop_img_till_contour(self.cropped_img, contour)
        else:
            self.left_border = cv2.getTrackbarPos("Left border", "Manuel cropping")
            self.right_border = cv2.getTrackbarPos("Right border", "Manuel cropping")
            self.top_border = cv2.getTrackbarPos("Top border", "Manuel cropping")
            self.bottom_border = cv2.getTrackbarPos("Bottom border", "Manuel cropping")

            cv2.line(self.drawing_img, (self.left_border, 0), (self.left_border, self.HEIGHT), (0, 0, 255), 3)
            cv2.line(self.drawing_img, (self.right_border, 0), (self.right_border, self.HEIGHT), (0, 0, 255), 3)
            cv2.line(self.drawing_img, (0, self.top_border), (self.WIDTH, self.top_border), (0, 0, 255), 3)
            cv2.line(self.drawing_img, (0, self.bottom_border), (self.WIDTH, self.bottom_border), (0, 0, 255), 3)

            self.return_img = self._crop_img_till_contour(self.drawing_img)

        return self.return_img

    def get_mask(self):
        """Geeft de mask terug van de class.
        
        Returns:
            np.array: self.mask
        """
        return self.mask
    
    def get_img(self):
        """Geeft de img terug van de class.
        
        Returns:
            np.darray: self.img
        """
        return self.img

    def show_mask(self):
        """Laat de mask zien die in de class aanwezig is.
        """
        if self.mask is not None:
            cv2.imshow("mask", self.mask)
        else:
            print("Geen mask aangemaakt. Voer get_table_now() uit.")

    def show_img(self):
        """Laat de image zien die in de class aanwezig is met OpenCV.
        """
        cv2.imshow("img", self.img)

    def new_img(self, img):
        """Maak een nieuwe img aan.
        
        Args:
            img (np.array): Nieuwe foto die wordt toegevoegd aan de class.
        """
        self.img = img
        self.drawing_img = cv2.GaussianBlur(img, (3, 3), cv2.BORDER_DEFAULT)


#test script
if __name__ == "__main__":

    # filename = 'Foto/frame_1.png'
    # folder = "D:\\Stichting Hogeschool Utrecht\\NLE - Documenten\Test foto's\\nieuwe camera\\white_tape\\"

    # filename = "Foto/white_tape/new_white_tape_0.png"

    #img = cv.imread(filename)
    # filenames = glob("Foto/test_fotos/*.png")
    filenames = glob("D:\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\oud\\V1.3 cam normal Wide angle\\*.png")
    if(filenames == []):
        print("ERROR! Paniek! geen foto's gevonden!")
        exit()

    filenames.sort()
    raster = Raster()

    for filename in filenames:
        img = cv2.imread(filename)
        img = cv2.resize(img, (640, 480))

        while True:
            raster.new_img(img)

            print("foto tested --> ", filename)
            startTime = datetime.now()
            cropped = raster.get_cropped_field()
            print('\tTime elapsed: ', datetime.now() - startTime)
            print('\t', raster.HEIGHT * raster.WIDTH)

            cv2.imshow(("cropped " + filename), cropped)
            cv2.imshow("Drawing img", raster.drawing_img)

            key = cv2.waitKey(100)
            if key == ord('q'):
                break
