"""
    Omschrijving: Koppelt de beeldherkenning aan de simulatie. Vertaalt hierbij de bal coördinaten in pixel positie
    van de beeldherkenning naar coördinaten voor de simulatie. 

    Wanneer debug_flag=True zal de bal bestuurd kunnen worden d.m.v. trackbars. Wanneer deze True is zal een vooraf gedefinieerde
    video worden afgespeeld.

    File:
        BeeldKoppeling.py
    Date:
        20-1-2020
    Version:
        1.12
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
        1.12:
            Spelling en grammatica commentaren nagekeken
"""

import cv2

class BeeldKoppeling():
    """Klasse die een koppeling maakt tussen de beeldherkenning en de simulatie. Vertaalt hierbij de bal coördinaten in pixel positie
    van de beeldherkenning naar coördinaten voor de simulatie. 

    **Author**: 
        Kelvin Sweere \n
    **Version**:
        1.12           \n
    **Date**:
        20-1-2020
    """
    def __init__(self, debug_flag=False):
        """        
        Args:
            debug_flag: (bool, optional) keuze of er trackbars worden gestart die de bal besturen. Default is False.
        """
        # Coördinaten van de bal (in verhouding).
        self.x_s = None     # X coördinaat simulatie
        self.y_s = None     # Y coördinaat simulaite

        self.x_p = None     # X coördinaat simulatie
        self.y_p = None     # Y coördinaat simulatie
        
        # Settings van de img. Worden ook opgehaald door get_ball().
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
            # Files is een bestand met daarin de video. Dit is voor demonstartie doeleinde.
            self._init_video_function()

    def get_pos_vision(self):
        """Voert de gehele pipeline in een keer uit. Haalt de gegevens op van trackbars en geeft hiervan de coördinaten van de simulatie terug.
        
        Returns:
            (tuple) x & y coördinaten van de simulatie van de bal.
        """
        # TODO: terugzetten wanneer niet meer gebruikt!
        # self.get_ball()
        self.test_video_function()
        # ! -------------------------------------------
        self._convert_2_sim_cor()  # Converteren beeld pix -> sim pix
        return (self.x_s, self.y_s) # Geeft de simulatie coördinaten terug.


    def _init_trackbars(self):
        """initialiseer debug trackbars.
        """
        def nothing(x): # Dummy functie voor cv2.createTrackbar.
            pass

        cv2.namedWindow('Cordinates')   # Maakt een window aan.
        self.MAX_TRACKBAR_VAL = 100
        # Maakt trackbars aan voor het verander van de kleur/
        cv2.createTrackbar('X','Cordinates',0,self.MAX_TRACKBAR_VAL,nothing)
        cv2.createTrackbar('Y','Cordinates',0,self.MAX_TRACKBAR_VAL,nothing)
        
        # Zet de trackbars op 50%
        cv2.setTrackbarPos('X',"Cordinates", int(self.MAX_TRACKBAR_VAL/2))
        cv2.setTrackbarPos('Y',"Cordinates", int(self.MAX_TRACKBAR_VAL/2))


    def map_function(self, val, in_min, in_max, out_min, out_max):
        """Map functie (zoals in de Arduino IDE) die de input in een vaste verhouding verschaalt naar de output.
        
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
        """Zet de pixel positie van de beeldherkenning om naar een x & y positie voor de simulatie.
        """
        # x_simulatie posite
        self.x_s = self.map_function(self.x_p, 0, self.WIDTH_IMG, -19.35, 19.35)
        self.y_s = self.map_function(self.y_p, 0, self.HEIGHT_IMG, 17.42, 0)


    def _get_trackbars(self):
        """Krijg waardes van de OpenCV trackbar(s) binnen.
        """
        k = cv2.waitKey(1) & 0xFF
        # get current positions of four trackbars
        self.x_p = cv2.getTrackbarPos('X','Coördinaten')
        self.y_p = cv2.getTrackbarPos('Y','Coördinaten')
    
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
        cv2.setTrackbarPos('X','Coördinaten', int(self.MAX_TRACKBAR_VAL/2))
        cv2.setTrackbarPos('Y','Coördinaten', int(self.MAX_TRACKBAR_VAL/2))


    def test_video_function(self):
        """Haal een frame uit de video op.
        """    
        cor = self.detect_ball.get_ball_pos()
        if cor is not None:
            (self.x_p, self.y_p) = cor
        else:
            (self.x_p, self.y_p) = (int(self.WIDTH_IMG/2), int(self.HEIGHT_IMG/2))  #zet in het midden van het speelveld.


    def _init_video_function(self):
        """Initialiseerd de video met de BallDetection klasse. 
        Deze functie wordt gebruikt voor de demo.

        Note:
        **NameError**: Er is geen file meegegeven aan de init van de BeeldKoppeling klasse.
        """

        for file in self.files:  #check per file
            self.detect_ball = BallDetection(file) #maak klasse aan
        
        # Hoeft maar een keer uitgevoerd te worden, omdat er een vaste crop functie is.
        img = self.detect_ball.get_frame()
        self.HEIGHT_IMG, self.WIDTH_IMG, _ = img.shape


if __name__ == "__main__":
    pass
