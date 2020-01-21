#pylint disable=E1101

"""
    Code voor het vinden van de contouren van de tafel. 

    File:
        FindContours.py
    Date:
       20-1-2020
    Version:
        1.22
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
        1.20:
            Constanten WIDTH en HEIGHT op 640 x 360 gezet
        1.21:
            Doxygen commentaar toegevoegd. 
        1.22:
            Spelling en grammatica commentaar nagekeken
"""

import numpy as np
import cv2
from src.Backend.Extra import *

if __name__ == "__main__":
    from glob import glob

class FindContours:
    """Klasse die de contouren van het veld kan detecteren. 
    Dit wordt gedaan door een handmatige init in de main applicatie. 
    
    **Author**:         \n
        Kelvin Sweere   \n
        Chileam Bohnen  \n
    **Version**:
        1.22            \n
    **Date**:
        20-1-2020   
    """
    def __init__(self, debug=False):
        """Init van de FindContours klasse. 
        
        Args:
            debug: (bool, optional) keuze of trackbars worden aangemaakt. Defaults to False.
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

        cv2.namedWindow("Handmatig bijsnijden")
        cv2.createTrackbar("Linkerrand", "Handmatig bijsnijden", self.left_border, self.WIDTH, nothing)
        cv2.createTrackbar("Rechterrand", "Handmatig bijsnijden", self.right_border, self.WIDTH, nothing)
        cv2.createTrackbar("Bovenrand", "Handmatig bijsnijden", self.top_border, self.HEIGHT, nothing)
        cv2.createTrackbar("Onderrand", "Handmatig bijsnijden", self.bottom_border, self.HEIGHT, nothing)

        # debug mode for frame and field contour detection
        self.debug = debug
        if debug:
            cv2.namedWindow("Trackbars")
            cv2.createTrackbar("gray_threshold", "Trackbars", self.gray_threshold, 255, nothing)
            cv2.createTrackbar("gray_cropped_threshold", "Trackbars", self.gray_cropped_threshold, 255, nothing)

    def _get_table_threshold(self):
        """Bewerk een grijskleur afbeelding, zodat er een mask overblijft, waarop contours getekend kan worden.

        Args:
          img: (np.array) orginele afbeelding in BGR format. Wordt later omgezet in grijskleur.

        Returns:
            (np.array) gefilterde afbeelding van het orgineel.
        """
        # Settings uit slider.py gehaald
        gray = cv2.cvtColor(self.drawing_img, cv2.COLOR_BGR2GRAY)
        if self.debug:
            self.gray_threshold = cv2.getTrackbarPos("gray_threshold", "Trackbars")
        _, filt = cv2.threshold(gray, self.gray_threshold, 255, cv2.THRESH_BINARY)
        # return nieuwe image.
        return filt

    def _get_field_threshold(self, cropped):
        """Bewerk een bijgesneden afbeelding, zodat een mask over blijft, waarop contours getekend kan worden.

        Args:
          img: (np.array) Bijgesneden afbeelding in BGR format. Wordt later omgezet in grijskleur.

        Returns:
            (np.array) gefilterde afbeelding van het orgineel.
        """
        cropped_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        if self.debug:
            self.gray_cropped_threshold = cv2.getTrackbarPos("gray_cropped_threshold", "Trackbars")
        _, filt = cv2.threshold(cropped_gray, self.gray_cropped_threshold, 255, cv2.THRESH_BINARY)
        return filt

    def _rotated_table(self, contour):
        """Roteer de tafel zodat de contour haaks komt te staan.
        
        Args:
            contour: (np.array) contour die recht gezet wordt.
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
        """Bewerk een YUV afbeelding, zodat een mask over blijft, waarop contours getekend kan worden.

        Args:
          img: (np.array) orginele afbeelding in BGR format. Wordt later omgezet in YUV.

        Returns:
            (np.array) gefilterde zwart/wit afbeelding van het orgineel.
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
        """Berekend het oppervlakte wat tussen twee punten is bevestigd. 
        
        Args:
            cor1: (tuple) x,y coördinaat  van linker boven hoek.
            cor2: (tuple) x,y coördinaat  van recher onder hoek.
        
        Returns:
            (int) oppervlakte tussen beide coördinaten.
        """
        x = abs(cor2[0] - cor1[0])
        y = abs(cor2[1] - cor1[1])
        return x*y

    def _find_table_contour(self, mask):
        """Vind het contour van de tafel met de gefilterde afbeelding van de tafel.
        
        Args:
            filt: (np.array) mask van orginele afbeelding. Hier worden de contours overheen getekend
        
        Returns:
            (tuple) grootste contour die aanwezig is in de gefilterde afbeelding (input).
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
        """Snijdt een 'orginele' afbeelding bij tot het juiste contour.
        
        Args:
            img: (np.darray) afbeelding die bijgesneden moet worden tot de coördinaten.
            contour_cor: (tuple) coördinaten van het contour waarop bijgesneden moet worden.
        
        Returns:
            (np.darray) Bijgesneden afbeelding van het orgineel.
        """
        if contour is None:
            return _img[self.top_border:self.bottom_border, self.left_border:self.right_border]
        else:
            x, y, w, h = cv2.boundingRect(contour)
        return _img[y:y+h, x:x+w]

    def get_table_now(self):
        """
        High-level API, die gelijk de bijgesneden afbeelding teruggeeft van de tafel.
        
        Args:
            img: (np.darray) input afbeelding van de (ongefilterde) tafel.
            filt: (bool, optional) kies of de afbeelding wordt teruggegeven (False), 
            of dat de gefilterde afbeelding wordt teruggegeven (True). Default is False.
        
        Returns:
            (np.darray) bijgesneden afbeelding van de tafel.
        """
        
        self.mask = self._get_white()  # get black/white image
        self.contour = self._find_table_contour(self.mask)
        self.mask = self._crop_img_till_contour(self.mask)  #resize mask
        self.img = self._crop_img_till_contour(self.img)    #resize img
        return self.img

    def get_cropped_field(self, threshold=False):
        """
        High-level API, die gelijk de bijgesneden afbeelding teruggeeft van het veld.

        Args:
            threshold: (bool, optional) de contouren van de tafel en veld worden gebruikt (True),
            of het gebied wordt handmatig ingesteld (False). Default is False.

        Returns:
            (numpy.darray) bijgesneden afbeelding van het speelveld.
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
            self.left_border = cv2.getTrackbarPos("Linkerrand", "Handmatig bijsnijden")
            self.right_border = cv2.getTrackbarPos("Rechterrand", "Handmatig bijsnijde")
            self.top_border = cv2.getTrackbarPos("Bovenrand", "Handmatig bijsnijde")
            self.bottom_border = cv2.getTrackbarPos("Onderrand", "Handmatig bijsnijde")

            cv2.line(self.drawing_img, (self.left_border, 0), (self.left_border, self.HEIGHT), (0, 0, 255), 3)
            cv2.line(self.drawing_img, (self.right_border, 0), (self.right_border, self.HEIGHT), (0, 0, 255), 3)
            cv2.line(self.drawing_img, (0, self.top_border), (self.WIDTH, self.top_border), (0, 0, 255), 3)
            cv2.line(self.drawing_img, (0, self.bottom_border), (self.WIDTH, self.bottom_border), (0, 0, 255), 3)

            self.return_img = self._crop_img_till_contour(self.drawing_img)

        return self.return_img

    def get_mask(self):
        """Geeft de mask terug van de klasse.
        
        Returns:
            (np.array) self.mask
        """
        return self.mask
    
    def get_img(self):
        """Geeft de afbeelding terug van de klasse.
        
        Returns:
            (np.darray) self.img
        """
        return self.img

    def show_mask(self):
        """Laat de mask zien die in de klasse aanwezig is.
        """
        if self.mask is not None:
            cv2.imshow("mask", self.mask)
        else:
            print("Geen mask aangemaakt. Voer get_table_now() uit.")

    def show_img(self):
        """Laat de afbeelding zien die in de klasse aanwezig is met OpenCV.
        """
        cv2.imshow("img", self.img)

    def new_img(self, img):
        """Maak een nieuwe afbeelding aan.
        
        Args:
            img (np.array): Nieuwe foto die wordt toegevoegd aan de klasse.
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
