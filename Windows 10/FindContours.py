#pylint disable=E1101

"""
Code voor het vinden van de contouren rond de tafel.
Hierin wordt de grootste contour gevonden, waarbij de img wordt gecropt en gereturnt.

File:       find_countours.py
Author:     Kelvin Sweere & Chileam Bohnen
Date:	    13-11-2019
Version     1.0
Test:       Failed
Tester:     Daniël Boon
"""


import numpy as np
import cv2 as cv
from datetime import datetime

if __name__ == "__main__":
    from glob import glob

class Raster:
    def __init__(self, img):
        """Init van de Raster class
        
        Args:
            img (np.array): image die moet worden gecropt. Deze moet een size hebben van 640 bij 480.
        """
        self.biggest_contour = None
        self.gray_threshold = 230
        self.gray_cropped_threshold = 100   #was 120! --> oorzaak failed test 13-11-2019
        self.WIDTH = 480    #constante, hoogte van het beeld
        self.HEIGHT = 640   #constante, breedte van het beeld
        self.mask = None
        self.cropped_mask = None
        self.img = img
        self.drawing_img = cv.GaussianBlur(img, (3, 3), cv.BORDER_DEFAULT)
        self.cropped_img = []
        self.return_img = []
        self.contour = []
        self.PIXEL_WIDTH = 10   #extra speling bij de gecropte images
        self.MAX_OPP = self.WIDTH * self.HEIGHT

    def _get_table_threshold(self):
        """bewerk een grayscale img, zodat een mask waarop contours getekend kan worden over blijft.

        Args:
          img (numpy array): orginele img in BGR format. Wordt later omgezet in grayscale.

        Returns:
            filt (numpy array): gefilterde image van het orgineel.
        """
        # Settings uit slider.py gehaald
        gray = cv.cvtColor(self.drawing_img, cv.COLOR_BGR2GRAY)
        _, filt = cv.threshold(gray, self.gray_threshold, 255, cv.THRESH_BINARY)
        # return nieuwe image.
        return filt

    def _get_field_threshold(self, cropped):
        """bewerk een gecropte img, zodat een mask waarop contours getekend kan worden over blijft.

        Args:
          img (numpy array): gecropte img in BGR format. Wordt later omgezet in grayscale.

        Returns:
            filt (numpy array): gefilterde image van het orgineel.
        """
        cropped_gray = cv.cvtColor(cropped, cv.COLOR_BGR2GRAY)
        _, filt = cv.threshold(cropped_gray, self.gray_cropped_threshold, 255, cv.THRESH_BINARY)
        return filt

    def _rotated_table(self, contour):
        """roteer de tafel zodat de contour haaks komt te staan.
        
        Args:
            contour (np.array): Contour die recht gezet wordt.
        """
        _rect = cv.minAreaRect(contour)
        center, shape, angle = _rect
        if angle < -45:
            angle += 90

        rot_mat = cv.getRotationMatrix2D(center, angle, 1.0)
        self.img = cv.warpAffine(self.img, rot_mat, self.img.shape[1::-1], flags=cv.INTER_LINEAR)
        self.drawing_img = cv.warpAffine(self.drawing_img, rot_mat, self.img.shape[1::-1], flags=cv.INTER_LINEAR)

    #krijg alleen tafel te zien (wit)
    def _get_white(self):        
        """bewerk een YUV img, zodat een mask waarop contours getekend kan worden over blijft.

        Args:
          img (numpy array): orginele img in BGR format. Wordt later omgezet in YUV.

        Returns:
            filt (numpy array): gefilterde image van het orgineel.
        """

        # Settings uit slider.py gehaald
        LOWHUE = 0  
        LOWSAT = 0
        LOWVAL = 0

        HIGHHUE = 220
        HIGHSAT = 240
        HIGHVAL = 235

        # TODO: 48 tot 54 in functie
        yuv = cv.cvtColor(self.img, cv.COLOR_BGR2YUV)
        colorLow = np.array([LOWHUE, LOWSAT, LOWVAL])
        colorHigh = np.array([HIGHHUE, HIGHSAT, HIGHVAL])
        #voeg filter toe
        mask = cv.inRange(yuv, colorLow, colorHigh)
        ###############

        # TODO: blur als functie maken
        #Zorg dat de stijle lijnen beter worden weergegeven.
        # kernal = cv.getStructuringElement(cv.MORPH_ELLIPSE, (7, 7))
        mask = cv.medianBlur(mask, 7)
        mask = cv.bilateralFilter(mask, 15 ,75, 75)

        filt = cv.morphologyEx(mask, cv.MORPH_CLOSE, mask)
        filt = cv.morphologyEx(filt, cv.MORPH_OPEN, filt)

        # self.show_img()
        # self.show_mask()
        
        # return nieuwe image.
        return filt

    def _calculate_area(self, cor1, cor2):            
        """berekend het oppervlakte wat tussen twee punten is bevestigd. 
        
        Args:
            cor1 (tuple): x,y cordinaat van linker boven hoek.
            cor2 (tuple): x,y cordinaat van recher onder hoek.
        
        Returns:
            int: oppervlakte tussen beide cordinaten.
        """
        x = abs(cor2[0] - cor1[0])
        y = abs(cor2[1] - cor1[1])
        return x*y

    def _find_table_contour(self, mask):
        """vind de contour van de tafel met de gefilterde img van de tafel.
        
        Args:
            filt (numpy.array): mask van orginele img. Hier worden de contours over 
        
        Returns:
            (tuple): grootste contour die aanwezig is in de gefilterde img (input).
        """

        contours, _ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)

        biggest_current_opp = 0

        for contour in contours:
            _rect = cv.minAreaRect(contour)
            _box = cv.boxPoints(_rect)
            _box = np.int0(_box) 

            opp = self._calculate_area(tuple(_box[0]), tuple(_box[2])) #return opp van de contours
            # cv.drawContours(self.img, contour, -1, (0,0,255), 3)

            # check of het oppervlakte de grootste is die aanwezig is.
            if (opp > biggest_current_opp and opp < self.MAX_OPP):
                biggest_current_opp = opp
                self.biggest_contour = _box

        return self.biggest_contour

    def _crop_img_till_contour(self, _img, contour):
        """Crop een 'orginele' img naar een gecropte img.
        
        Args:
            img (numpy.darray): img die gecropt moet worden tot de cordinaten.
            contour_cor (tuple): cordinaten van de contours waar deze gecropt moet worden.
        
        Returns:
            (numpy.darray): gecropte image van het orgineel.
        """
        x, y, w, h = cv.boundingRect(contour)
        #print(x,y,w,h)
        # return img[y:y+h, x:x+w]
        # return img[y - self.PIXEL_WIDTH:y + h + self.PIXEL_WIDTH, x - self.PIXEL_WIDTH:x + w + self.PIXEL_WIDTH]
        return _img[y:y+h, x:x+w]

    def get_table_now(self):
        """
        High-level API, die gelijk de gecropte img teruggeeft van de tafel.
        
        Args:
            img (numpy.darray): input image van de (ongefilterde) tafel.
            filt (bool, optional): kies of de img wordt teruggegeven (False),
            of dat de gefilterde img wordt teruggegeven (True). Defaults to False.
        
        Returns:
            numpy.darray: gecropte image van de tafel.
        """
        
        self.mask = self._get_white()  # get black/white image
        self.contour = self._find_table_contour(self.mask)
        #TODO: terugzetten 
        self.mask = self._crop_img_till_contour(self.mask)  #resize mask
        self.img = self._crop_img_till_contour(self.img)    #resize img
        return self.img

    def get_cropped_field(self):
        """
        High-level API, die gelijk de gecropte img teruggeeft van het veld.

        Args:
            img (numpy.darray): input image van de (ongefilterde) tafel.
            filt (bool, optional): kies of de img wordt teruggegeven (False),
            of dat de gefilterde img wordt teruggegeven (True). Defaults to False.

        Returns:
            numpy.darray: gecropte image van de tafel.
        """
        self.mask = self._get_table_threshold()
        contour = self._find_table_contour(self.mask)

        # draw black border around contour
        cv.drawContours(self.drawing_img, [contour], -1, (0, 0, 0), 45)

        # rotate img
        self._rotated_table(contour)

        self.cropped_img = self._crop_img_till_contour(self.drawing_img, contour)

        self.cropped_mask = self._get_field_threshold(self.cropped_img) #krijg mask terug.
        contour = self._find_table_contour(self.cropped_mask)

        self.return_img = self._crop_img_till_contour(self.cropped_img, contour)

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
            cv.imshow("mask", self.mask)
            cv.waitKey(0)
        else:
            print("Geen mask aangemaakt. Voer get_table_now() uit.")

    def show_img(self):
        """Laat de image zien die in de class aanwezig is.
        """
        cv.imshow("img", self.img)
        cv.waitKey(0)


#test script
if __name__ == "__main__":

    # filename = 'Foto/frame_1.png'
    # folder = "D:\\Stichting Hogeschool Utrecht\\NLE - Documenten\Test foto's\\nieuwe camera\\white_tape\\"

    # filename = "Foto/white_tape/new_white_tape_0.png"

    #img = cv.imread(filename)
    # filenames = glob("Foto/test_fotos/*.png")
    filenames = glob("C:\\Users\\kelvi\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\ball\\*.png")
    if(filenames == []):
        print("ERROR! Paniek! geen foto's gevonden!")
        exit()

    filenames.sort()

    for filename in filenames:
        img = cv.imread(filename)
        img = cv.resize(img, (640, 480))

        raster = Raster(img)
        print("foto tested --> ", filename)
        startTime = datetime.now()
        cropped = raster.get_cropped_field()
        print('\tTime elapsed: ', datetime.now() - startTime)
        cv.imshow(("cropped "+ filename), cropped)
        print('\t', raster.HEIGHT * raster.WIDTH)

    cv.waitKey(0)
    cv.destroyAllWindows()