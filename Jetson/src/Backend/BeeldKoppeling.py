"""
    Omschrijving: Koppelt de beeldherkenning aan de simulatie. Vertaalt hierbij de bal coördinaten in pixel positie
    van de beeldherkenning naar coördinaten voor de simulatie. 

    Wanneer debug_flag=True zal de bal bestuurd kunnen worden d.m.v. trackbars. Wanneer deze True is zal een vooraf gedifineerde
    video worden afgespeeld.

    File:
        BeeldKoppeling.py
    Date:
        13-12-2019
    Version:
        1.1
    Modifier:
        Kelvin Sweere
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Schematic:
        Lucidchart: NLE/AI/Bal update met beeldherkenning
    Version management:
        1.0:
            Release Jetson Nano.
        1.10:
            Functies met underscore gemaakt ipv C++ lowerCamelCase style.
        1.11:
            Doxygen documentatie toegevoegd.
            Spelling verbeterd.
"""

import cv2

class BeeldKoppeling():
    """Class die een koppeling maakt tussen de beeldherkenning en de simulatie. Vertaalt hierbij de bal coördinaten in pixel positie
    van de beeldherkenning naar coördinaten voor de simulatie. 

    **Author**: 
        Kelvin Sweere \n
    **Version**:
        1.1           \n
    **Date**:
        13-12-2019 
    """
    def __init__(self, debug_flag=False):
        """        
        Args:
            debug_flag: (bool, optional) keuze of er trackbars die de bal besturen worden gestart. Defaults to False.
        """
        # coördinaten van de bal (in verhouding)
        self.x_s = None     #x coördinaat  simulatie
        self.y_s = None     #y coördinaat  simulaite

        self.x_p = None     #x coördinaat  simulatie
        self.y_p = None     #y coördinaat  simulatie
        
        # settings van de img. Worden ook opgehaald door get_ball()
        self.WIDTH_IMG = None
        self.HEIGHT_IMG = None
        self.DEBUG_FLAG = debug_flag    # Flag waarbij gekozen kan worden of trackbars worden toegevoegd.

        if self.DEBUG_FLAG:
            self._init_trackbars()   # Debug versie! Command wanneer de debug niet gebruikt wordt!
        else:
            # TODO: verwijderen wanneer niet meer gebruikt!:
            from glob import glob
            import os
            self.files = glob("C:\\Users\\" + os.getlogin() + "\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\V1.3 cam normal Wide angle + ball\\output_fast.avi")
            # files is een bestand met daarin de film. Dit is voor demonstartie doeleinde.
            self._init_video_function()

    def get_pos_vision(self):
        """Voert de gehele pipeline in een keer uit. Haalt de gegevens op van trackbars en returnt hiervan de coördinaten van de simulatie.
        
        Returns:
            (tuple) x & y coördinaten van de simulatie van de bal.
        """
        # TODO: terugzetten wanneer niet meer gebruikt!
        # self.get_ball()
        self.test_video_function()
        # ! -------------------------------------------
        self._convert_2_sim_cor()  #conv beeld pix -> sim pix
        return (self.x_s, self.y_s) #return simulatie cordinaten.


    def _init_trackbars(self):
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


    def map_function(self, val, in_min, in_max, out_min, out_max):
        """Map functie (zoals in de Arduino IDE) die input schaald in verhouding naar de output.
        
        Args:
            val: (int) waarde die geschaald moet worden.
            in_min: (int) minimale waarde die de input kan hebben.
            in_max: (int) maximale waarde die de input kan hebben.
            out_min: (int) minimale waarde die de output mag krijgen.
            out_max: (int) maximale waarde die de output mag krijgen.
        
        Returns:
            (int) geschaalde waarde van de input.
        """
        return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;


    def _convert_2_sim_cor(self):
        """Zet de pixel positie van de beeldherkenning om naar x & y positie van de simulatie.
        """
        # x_simulatie posite
        self.x_s = self.map_function(self.x_p, 0, self.WIDTH_IMG, -19.35, 19.35)
        self.y_s = self.map_function(self.y_p, 0, self.HEIGHT_IMG, 17.42, 0)


    def _get_trackbars(self):
        """Krijg waardes van de OpenCV trackbar(s) binnen.
        """
        k = cv2.waitKey(1) & 0xFF
        # get current positions of four trackbars
        self.x_p = cv2.getTrackbarPos('X','Cordinates')
        self.y_p = cv2.getTrackbarPos('Y','Cordinates')
    
    # TODO: check deze functie!
    def get_ball(self):
        """Krijg de coördinaten van de bal via de beeldherkenning. 
        """
        # ! NIET AF! Alleen nog maar debug modus.
        if self.DEBUG_FLAG:
            self.HEIGHT_IMG = 100    # y
            self.WIDTH_IMG =  100    # x
            self.x_p = 50
            self.y_p = 50
            self._get_trackbars()
        else:
            print("Functie toevoegen die de bal van de beeldherkenning ophaalt!")
        # TODO: Functie toevoegen die de bal van de beeldherkenning ophaalt!


    def reset_coordinates(self):
        """Reset de coördinaten in de simulatie (en de trackbars).
        """
        self.x_s = 8.71 # midden van het veld.
        self.y_s = 0    # midden van het veld.
        self.reset_trackbar_pos()


    def reset_trackbar_pos(self):
        """Reset trackbar positie van cordinaten.
        """
        cv2.setTrackbarPos('X','Cordinates', int(self.MAX_TRACKBAR_VAL/2))
        cv2.setTrackbarPos('Y','Cordinates', int(self.MAX_TRACKBAR_VAL/2))


    def test_video_function(self):
        """Haal frame uit de video op.
        """    
        cor = self.detect_ball.get_ball_pos()
        if cor is not None:
            (self.x_p, self.y_p) = cor
        else:
            (self.x_p, self.y_p) = (int(self.WIDTH_IMG/2), int(self.HEIGHT_IMG/2))  #zet in het midden van het speelveld.


    def _init_video_function(self):
        """Initaliseerd de video met de BallDetection class. 
        Deze functie wordt gebruikt voor de demo.

        Note:
        **NameError**: Er is geen file meegegeven aan de init van de BeeldKoppeling class.
        """

        for file in self.files:  #check per file
            self.detect_ball = BallDetection(file) #maak class aan
        
        # hoeft maar een keer uitgevoerd te worden, omdat er een vaste crop functie is.
        img = self.detect_ball.get_frame()
        self.HEIGHT_IMG, self.WIDTH_IMG, _ = img.shape


if __name__ == "__main__":
    pass
