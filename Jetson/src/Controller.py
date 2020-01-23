"""
    In deze klasse kan er met behulp van twee coördinaat punten de benodigde keeper positie worden bepaald.
    Hierbij wordt: extra-polation toegepast, coördinaat naar mm geconverteerd, de keeper stap positie bepaald,
    laterale motor naar home positie gezet, axiale motor wordt mee geschoten en de drivers aangestuurd.

    File:
        Controller.py
    Date:
        23-1-2020
    Version:
        1.36
    Authors:
        Daniël Boon
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Schemetic:
        -
    Version management:
        1.1:
            -
        1.2:
            class p_controller veranderd naar CamelCase (PController)
        1.30:
            Google docstring format toegepast op functies.
        1.31:
            Doxygen commentaar toegevoegd.
        1.32:
            Spelling en grammatica commentaar nagekeken
        1.33:
            go_home functie operationeel zonder hardware sensor voor home positie
        1.34:
            fixed niet bestaande atributen
        1.35:
            Doxygen cometaar gecontroleerd + overtollig commetaar verwijdert 
        1.36:
            fixed error wanneer geen gyroscope is aangesloten
""" 

#pylint: disable=E1101
import time
import cv2
import numpy as np
from math import pi
from threading import Thread
from queue import Queue
import struct
from src.Backend.USB import Driver
from src.Backend.USB import Commands

try:
    from src.Backend.MPU6050 import  MPU6050
    MET_GYROS = True
except ModuleNotFoundError:
    print("MPU niet gevonden")
    MET_GYROS = False

class Controller:
    """In deze klasse kan er met behulp van twee coördinaat punten de benodigde keeper positie worden bepaald.
    Hierbij wordt: extra-polation toegepast, coördinaat naar mm geconverteerd, de keeper stap positie bepaald,
    laterale motor naar home positie gezet, axiale motor wordt mee geschoten en de drivers aangestuurd.
    
    **Author**: 
        Daniël Boon \n
    **Version**:
        1.36        \n
    **Date**:
        23-1-2020 
    """

    def __init__(self):
        """Initialiseren van de communicatie met de drivers en het bepalen van de verhoudingen.
        """
        met_drivers = False
        self.driver = Driver(0)
        if MET_GYROS:
            self.gyroscoop = MPU6050(debug=True)
        if self.driver.stepper_init():
            print("door init heen!")
            met_drivers = True
            self.calibrate_go_home()
            self.go_home()
        else:
            print("ERROR, PANIEK! --> geen stepper motor drivers gevonden!")

        self.TABLE_LENGTH = 540 #mm
        self.y_length = 200 #coördinates
        self.ratio_MM_to_y = (self.y_length/self.TABLE_LENGTH)
        self.ratio_y_to_MM = (self.TABLE_LENGTH/self.y_length)
        self.STEP_DiSTANCE = 960 #steps
        self.D_GEAR = 32 #mm
        self.KEEPER_DIS = 180 #mm
        self.MOTOR_STEP = 1.8 #deg/step
        self.MICRO_STEP = 2 
        self.MOTOR_TOTAL_STEPS = (360/self.MICRO_STEP)*self.MICRO_STEP
        self.ONE_ROTATION = self.D_GEAR*pi
        self.ONE_STEP = self.ONE_ROTATION/self.MOTOR_TOTAL_STEPS
        # self.step_correction()

        # threads parameters
        self.que = Queue(1)
        self.running = False

    def start_controller_thread(self):
        """Opstarten van een nieuw proces die de functie get_ai_motion uitvoert.
        """
        ball_thread = Thread(target=self.get_ai_motion, args=())
        ball_thread.daemon = True
        self.running = True
        ball_thread.start()

    def get_ai_motion(self):
        while self.running:
            if not self.que.empty():
                motion = self.que.get()
                # UP
                if motion == 0:
                    self.jog_motor(motion)
                    pass
                # DOWN
                elif motion == 1:
                    self.jog_motor(motion)
                    pass
                # SHOOT
                elif motion == 2:
                    self.shoot()
                # STILL
                elif motion == 3:
                    self.stop_motor()
                    pass
                # go home
                elif motion == 4:
                    self.go_home()

    def stop_controller_thread(self):
        self.running = False
        self.driver.close_connections()

    def test_lin_movement(self, co):
        """Bepaald de positie van de keeper en stuurt een opdracht naar drivers.
        
        Args:
            co: (int) het bepaalde coördinaat voor keeper vanuit de extra-polation.
        
        Returns:
            (int) returns De berekende stap positie (deze waarde is ter debug en mag genegeerd worden, 
            want de drivers worden in deze funtie al aangestuurd).
        """

        step_pos = int(round((co * self.ratio_y_to_MM)/ self.ONE_STEP))

        self.driver.transceive_message(0, Commands.SET_X, step_pos)
        return step_pos

    def step_correction(self):
        """haalt stapcorrectie van de gyroscoop op regelt de hendel terug naar 0 graden (begin positie).
        """
        self.driver.transceive_message(1, Commands.SET_PX, 0)
        angle_x = int(self.gyroscoop.get_x_rotation())   #krijg de hoek van x terug.
        print("angle_x:", angle_x)

        # check angle rotation of gyroscoop
        if int(angle_x) != 0:
            # calculate step size for correction
            step_size = -1 * int( (angle_x / (self.MOTOR_STEP / self.MICRO_STEP)/2) )
            print("step_size:", step_size)
            # move to corrected position
            self.driver.transceive_message(1, Commands.SET_X, step_size)
            while(int(self.driver.transceive_message(1, Commands.GET_PS).decode("utf-8"))):
                pass
            time.sleep(0.05)
            print("pos 3:", self.driver.transceive_message(1, Commands.GET_PX))
            # reset motordriver steps to zero
            self.driver.transceive_message(1, Commands.SET_PX, 0)
            time.sleep(0.05)

    def shoot(self):
        """Bestuurt de drivers zodat er axiaal bewogen wordt.
        """
        if(len(self.driver.handlers)==2):
            self.driver.transceive_message(1, Commands.SET_X, 48)
            while(int(self.driver.transceive_message(1, Commands.GET_PS).decode("utf-8"))):
                pass
            time.sleep(0.05)
            print("pos 0:", self.driver.transceive_message(1, Commands.GET_PX))
            self.driver.transceive_message(1, Commands.SET_X, -48)
            while(int(self.driver.transceive_message(1, Commands.GET_PS).decode("utf-8"))):
                pass
            time.sleep(0.05)
            print("pos 1:", self.driver.transceive_message(1, Commands.GET_PX))
            self.driver.transceive_message(1, Commands.SET_X, 0)
            while(int(self.driver.transceive_message(1, Commands.GET_PS).decode("utf-8"))):
                pass
            time.sleep(0.1)
            print("pos 2:", self.driver.transceive_message(1, Commands.GET_PX))
            #change motordriver position when steps are lost
            if MET_GYROS:
                self.step_correction()

    def bitfield(self, n):
        """Converteerd een bit list naar een integer list.
        
        Args:
            n: (byte) byte die moet worden vertaald naar een integer.
        
        Returns:
            (list) integer list van het byte array.
        """
        array = [int(digit) for digit in bin(n)[2:]] # [2:] to chop off the "0b" part 
        for i in range(11-len(array)):
            array.insert(0, 0)
        return array

    def calibrate_go_home(self):
        """Kalibreer halve doel afstand waarde.
        """
        self.driver.transceive_message(0, Commands.SET_HSPD, self.driver.HIGH_SPEED[0])
        # ga op langzame snelheid naar positief limiet en wacht tot de keeper er is
        self.driver.transceive_message(0, Commands.JPLUS)
        

        while(int(self.driver.transceive_message(0, Commands.GET_PS).decode("utf-8"))):
            pass
        
        # onthoud positie positief limiet, ga naar negatief limiet en wacht tot de keeper er is
        pos_plus = int(self.driver.transceive_message(0, Commands.GET_PX).decode("utf-8"))
        time.sleep(0.1)
        self.driver.transceive_message(0, Commands.JMIN)
        
        while(int(self.driver.transceive_message(0, Commands.GET_PS).decode("utf-8"))):
            pass
        
        # onthoud positie negatief limiet en bepaal het halve doel afstand waarde
        pos_min = int(self.driver.transceive_message(0, Commands.GET_PX).decode("utf-8"))
        self.half_dis = (abs(pos_plus - pos_min)/2)
        self.driver.transceive_message(0, Commands.SET_HSPD, self.driver.HIGH_SPEED[0])


    def go_home(self, direction=0):
        """Beweegt de keeper terug naar de home positie.
        
        Args:
            direction: (int, optional) 0 is naar links, 1 is rechts gezien vanaf de hendel. Standaard 0 (links).
        """
        # bepaal richting
        time.sleep(0.1)
        if(direction==0):
            self.driver.transceive_message(0, Commands.JPLUS)
            home_point = -self.half_dis
        else:
            self.driver.transceive_message(0, Commands.JMIN)
            home_point = self.half_dis
        
        # wacht tot deze bij limiet is
        while(int(self.driver.transceive_message(0, Commands.GET_PS).decode("utf-8"))):
            pass
        time.sleep(0.1)
        # maakt limiet punt 0 en verplaats met halve doel afstand
        self.driver.transceive_message(0, Commands.SET_PX, 0)
        self.driver.transceive_message(0, Commands.SET_X, home_point)

        # wacht tot deze bij het halve doel afstand is
        while(int(self.driver.transceive_message(0, Commands.GET_PS).decode("utf-8"))):
            pass

    def stop_motor(self):
        """Stop motor
        """
        self.driver.transceive_message(0, Commands.STOP)
    
    def jog_motor(self, direction=0):
        """Beweeg motor met high speed instelling.
        
        Args:
            direction: (int, optional) 0 = JOG_MIN en 1 = JOG_PLUS. Defaults to 0.
        """
        self.driver.transceive_message(0, Commands.STOP)
        while(int(self.driver.transceive_message(0, Commands.GET_PS).decode("utf-8"))):
            pass
        if(direction):
            self.driver.transceive_message(0, Commands.JPLUS)
        else:
            self.driver.transceive_message(0, Commands.JMIN)


    def linear_extrapolation(self, pnt1, pnt2, value_x=5, max_y=32):
        """Toepassen van extra-polation om de keeper coördinaten te bepalen.
        
        Args:
            pnt1: (tuple) x, y coördinaten punt 1 van bal.
            pnt2: (tuple) x, y coördinaten punt 2 van bal.
            value_x: (int, optional) coördinaat waar keeper staat in x. Standaard 5.
            max_y: (int, optional) halve coördinaat afstand waar de keeper kan komen. Standaard 32.
        
        Returns:
            (tuple) x, y snijpunt coördinaten van keeper en de vector van de bal.
        """

        # keep is the pixel position of keeper rod on the x-axis
        keep_x = value_x

        value1 = ((pnt1[1] * (pnt2[0] - keep_x) + pnt2[1] * (keep_x - pnt1[0])))
        value2 = (pnt2[0] - pnt1[0])

        # check if divide by zero
        if value2 != 0:
            keep_y = (value1 / value2)
        else:
            keep_y = pnt1[1] 

        if (value2>0) or (abs(keep_y)>max_y):
            return None, None #geen snijpunt waar keeper bij kan
        else:
            return keep_x, keep_y

if __name__ == "__main__":
    """Test code voor Controller klasse voor schietfunctie
    """

    pc = Controller()

    while True:
        key = input()
        pc.shoot()



        

