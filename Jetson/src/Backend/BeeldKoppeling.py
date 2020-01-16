'''
 * File     : beeld_koppeling.py
 * Datum    : 13-12-2019
 * Version  : 0.1
 * Modifier : Kelvin Sweere
 * Python version : V3.6.9
 * omschrijving: Koppelt de beeldherkenning aan de simulatie. Vertaalt hierbij de bal cordinaten in pixel positie
 van de beeldherkenning naar cordinaten voor de simulatie. 

 Wanneer debug_flag=True zal de bal bestuurd kunnen worden d.m.v. trackbars. Wanneer deze True is zal een vooraf gedifineerde
 video worden afgespeeld.

* schema via Lucidchart: NLE/AI/Bal update met beeldherkenning/BeeldKoppeling
'''

import cv2
#from BallDetection import BallDetection
import time

class BeeldKoppeling():
    """Class die beeldherkenning koppelt aan de simulatie.
    """
    def __init__(self, debug_flag=False):
        """        
        Args:
            debug_flag (bool, optional): Keuze of er trackbars worden gestart. Defaults to False.
        """
        # cordinaten van de bal (in verhouding)
        self.x_s = None     #x cordinaat simulatie
        self.y_s = None     #y cordinaat simulaite

        self.x_p = None     #x cordinaat simulatie
        self.y_p = None     #y cordinaat simulatie
        
        # settings van de img. Worden ook opgehaald door getBall()
        self.WIDTH_IMG = None
        self.HEIGHT_IMG = None
        self.DEBUG_FLAG = debug_flag    # Flag waarbij gekozen kan worden of trackbars worden toegevoegd.

        if self.DEBUG_FLAG:
            self._initTrackbars()   # Debug versie! Command wanneer de debug niet gebruikt wordt!
        else:
            # TODO: verwijderen wanneer niet meer gebruikt!:
                from glob import glob
                import os
                self.files = glob("C:\\Users\\" + os.getlogin() + "\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\V1.3 cam normal Wide angle + ball\\output_fast.avi")
                # files is een bestand met daarin de film. Dit is voor demonstartie doeleinde.
                self._initVideoFunction()

    def getPosVision(self):
        """Voert de gehele pipeline in een keer uit. Haalt de gegevens op van trackbars en returnt hiervan de cordinaten van de simulatie.
        
        Returns:
            tuple: (x_s,y_s) cordinaten van de bal voor de simulatie.
        """
        # TODO: terugzetten wanneer niet meer gebruikt!
        # self.getBall()
        self.testVideoFunction()
        # ! -------------------------------------------
        self._convert2SimCor()  #conv beeld pix -> sim pix
        return (self.x_s, self.y_s) #return simulatie cordinaten.


    def _initTrackbars(self):
        """initaliseer debug trackbars.
        """
        def nothing(x): #dummy functie voor cv2.createTrackbar
            pass

        cv2.namedWindow('Cordinates')   #maak window aan.
        self.MAX_TRACKBAR_VAL = 100
        # create trackbars for color change
        cv2.createTrackbar('X','Cordinates',0,self.MAX_TRACKBAR_VAL,nothing)
        cv2.createTrackbar('Y','Cordinates',0,self.MAX_TRACKBAR_VAL,nothing)
        
        # Zet de trackbars op 50%
        cv2.setTrackbarPos('X',"Cordinates", int(self.MAX_TRACKBAR_VAL/2))
        cv2.setTrackbarPos('Y',"Cordinates", int(self.MAX_TRACKBAR_VAL/2))


    def mapFunction(self, val, in_min, in_max, out_min, out_max):
        """Map functie (zoals in de Arduino IDE) die input schaald in verhouding naar de output.
        
        Args:
            val (int): waarde die geschaald moet worden.
            in_min (int): minimale waarde die de input kan hebben.
            in_max (int): maximale waarde die de input kan hebben.
            out_min (int): minimale waarde die de output mag krijgen.
            out_max (int): maximale waarde die de output mag krijgen.
        
        Returns:
            int: Geschaalde waarde van de input.
        """
        return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;


    def _convert2SimCor(self):
        """Zet de pixel positie van de beeldherkenning om naar pixel positie van de simulatie.
        """
        # x_simulatie posite
        self.x_s = self.mapFunction(self.x_p, 0, self.WIDTH_IMG, -19.35, 19.35)
        self.y_s = self.mapFunction(self.y_p, 0, self.HEIGHT_IMG, 17.42, 0)


    def _getTrackbars(self):
        """Krijg trackbar waardes binnen.
        """
        k = cv2.waitKey(1) & 0xFF
        # get current positions of four trackbars
        self.x_p = cv2.getTrackbarPos('X','Cordinates')
        self.y_p = cv2.getTrackbarPos('Y','Cordinates')
    
    # TODO: check deze functie!
    def getBall(self):
        """Krijg de cordinaten van de bal via de beeldherkenning. 
            NIET AF! Alleen nog maar debug modus.
        """
        if self.DEBUG_FLAG:
            self.HEIGHT_IMG = 100    # y
            self.WIDTH_IMG =  100    # x
            self.x_p = 50
            self.y_p = 50
            self._getTrackbars()
        else:
            print("Functie toevoegen die de bal van de beeldherkenning ophaalt!")
        # TODO: Functie toevoegen die de bal van de beeldherkenning ophaalt!


    def resetCoordinates(self):
        """Reset de cordinaten in de simulatie (en de trackbars).
        """
        self.x_s = 8.71 # midden van het veld.
        self.y_s = 0    # midden van het veld.
        self.resetTrackbarPos()


    def resetTrackbarPos(self):
        """reset trackbar positie van cordinaten.
        """
        cv2.setTrackbarPos('X','Cordinates', int(self.MAX_TRACKBAR_VAL/2))
        cv2.setTrackbarPos('Y','Cordinates', int(self.MAX_TRACKBAR_VAL/2))


    def testVideoFunction(self):
        """Haal frame uit de video op.
        """    
        cor = self.detect_ball.getball_pos()
        if cor is not None:
            (self.x_p, self.y_p) = cor
        else:
            (self.x_p, self.y_p) = (int(self.WIDTH_IMG/2), int(self.HEIGHT_IMG/2))  #zet in het midden van het speelveld.


    def _initVideoFunction(self):
        """Initaliseerd de video met de BallDetection class. Dit is een functie voor de demo.
        """

        for file in self.files:  #check per file
            self.detect_ball = BallDetection(file) #maak class aan
        
        # hoeft maar een keer uitgevoerd te worden, omdat er een vaste crop functie is.
        img = self.detect_ball.getFrame()
        self.HEIGHT_IMG, self.WIDTH_IMG, _ = img.shape


if __name__ == "__main__":
    pass