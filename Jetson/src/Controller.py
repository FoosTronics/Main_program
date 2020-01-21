"""
    In deze class kan er met behulp van twee coördinaat punten de benodigde keeper positie worden bepaald.
    Hierbij wordt: extra-polation toegepast, coördinaat naar mm geconverteerd, de keeper stap positie bepaald
    en de drivers aangestuurd.

    File:
        Controller.py
    Date:
        20-1-2020
    Version:
        1.32
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
""" 

#pylint: disable=E1101
import time
# import matplotlib.pyplot as plt
import numpy as np
from math import pi
import struct
from .Backend.USB import Driver
from .Backend.USB import Commands

# from src.mpu6050 import  MPU6050
from tkinter import *
import pygame
from pygame.locals import (
    K_w,
    K_a,
    K_s,
    K_d,
    K_h,
    K_p,
    K_v,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

class Controller:
    """In deze class kan er met behulp van twee coördinaat punten de benodigde keeper positie worden bepaald.
       Hierbij wordt: extra-polation toegepast, coördinaat naar mm geconverteerd, de keeper stap positie bepaald
       en de drivers aangestuurd.
    
    **Author**: 
        Daniël Boon \n
    **Version**:
        1.32        \n
    **Date**:
        20-1-2020 
    """

    def __init__(self):
        """Initialiseren van de communicatie met de drivers en het bepalen van de verhoudingen.
        """
        met_drivers = False
        self.driver = Driver(0)
        # self.gyroscoop = MPU6050()
        if self.driver.stepper_init():
            print("door init heen!")
            met_drivers = True
            self.go_home()
            # self.driver.select_performax_device(0)
            # self.driver.get_device_descriptors()
            # self.driver.open_connection()
        else:
            print("ERROR, PANIEK! --> geen stepper motor drivers gevonden!")
            exit()

        pygame.init()
        self.screen = pygame.display.set_mode([500, 500])
        self.clock = pygame.time.Clock()

        self.TABLE_LENGTH = 540 #mm
        self.y_length = 200 #coördinates
        self.ratio_MM_to_y = (self.y_length/self.TABLE_LENGTH)
        self.ratio_y_to_MM = (self.TABLE_LENGTH/self.y_length)
        self.STEP_DiSTANCE = 960 #steps
        self.D_GEAR = 32 #mm
        self.KEEPER_DIS = 180 #mm
        self.MOTOR_STEP = 1.8 #deg/step
        #print(self.driver.transceive_message(Commands.GET_DRVMS).decode("utf-8"))
        self.MICRO_STEP = int(self.driver.transceive_message(0, Commands.GET_DRVMS).decode("utf-8"))
        self.MOTOR_TOTAL_STEPS = (360/self.MOTOR_STEP)*self.MICRO_STEP
        self.ONE_ROTATION = self.D_GEAR*pi
        self.ONE_STEP = self.ONE_ROTATION/self.MOTOR_TOTAL_STEPS

    def test_lin_movement(self, co):
        """Bepaald de positie van de keeper en stuurt een opdracht naar drivers.
        
        Args:
            co: (int) het bepaalde coördinaat voor keeper vanuit de extra-polation.
        
        Returns:
            (int) returns De berekende stap positie (deze waarde is ter debug en mag genegeerd worden, 
            want de drivers worden in deze funtie al aangestuurd).
        """

        font = pygame.font.SysFont("arial", 15)
        TEXT_COLOR = (255, 255, 255)
        text = font.render("y coördinaat: ",True,TEXT_COLOR)
        self.screen.blit(text, (10, 10))

        # step_data = self.driver.transceive_message(Commands.GET_PX).decode("utf-8") 
        # step = int(step_data)#int.from_bytes(step_data, byteorder='big', signed=True)#struct.unpack('<B', step_data)
        #print(step)
        step_pos = int(round((co * self.ratio_y_to_MM)/ self.ONE_STEP))

        text = font.render(str(step_pos),True,TEXT_COLOR)
        self.screen.blit(text, (10, 20))
        pygame.display.flip()
        self.clock.tick(60)

        self.driver.transceive_message(0, Commands.SET_X, step_pos)
        return step_pos

    # def step_correction(self):
    #     """Haalt stapcorrectie van de gyroscoop op regelt de hendel terug naar 0 graden (begin positie).
    #     """
    #     angle = self.gyroscoop.getXRotation()   #krijg de hoek van x terug.
    #     # angle = self.gyroscoop.getYRotation()
    #     # check angle rotation of gyroscoop
    #     if int(angle) != 0:
    #         # calculate step size for correction
    #         step_size = int(self.MOTOR_STEP * angle * self.MICRO_STEP)
    #         # move to corrected position
    #         self.driver.transceive_message(1, Commands.SET_X, step_size)
    #         # reset motordriver steps to zero
    #         self.driver.transceive_message(1, Commands.SET_PX, 0)

    def shoot(self):
        """Bestuurt de drivers zodat er axiaal bewogen wordt.
        """
        if(len(self.driver.handlers)==2):
            self.driver.transceive_message(1, Commands.SET_X, 48)
            while(int(self.driver.transceive_message(1, Commands.GET_PS).decode("utf-8"))):
                pass
            self.driver.transceive_message(1, Commands.SET_X, -48)
            while(int(self.driver.transceive_message(1, Commands.GET_PS).decode("utf-8"))):
                pass
            self.driver.transceive_message(1, Commands.SET_X, 0)
            # change motordriver position when steps are lost
            # self.step_correction()

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

    def go_home(self, direction=0):
        """Beweegt de keeper terug naar de home positie.
        
        Args:
            direction: (int, optional) 0 is naar links, 1 is rechts gezien vanaf de hendel. Standaard 0 (links).
        """
        if(direction==0):
            self.driver.transceive_message(0, Commands.HOME_PLUS)
        else:
            self.driver.transceive_message(0, Commands.HOME_MIN)

        while(1):
            print(int(self.driver.transceive_message(0, Commands.GET_MST).decode("utf-8")))
            mst_code = self.bitfield(int(self.driver.transceive_message(0, Commands.GET_MST).decode("utf-8")))
            # print(mst_code)
            try:
                if(mst_code[6]):
                    print("bij min limit; doe H+")
                    self.driver.transceive_message(0, Commands.HOME_PLUS)
                elif(mst_code[5]):
                    print("bij plus limit; doe H-")
                    self.driver.transceive_message(0, Commands.HOME_MIN)
                elif((not int(self.driver.transceive_message(0, Commands.GET_PS).decode("utf-8"))) or (mst_code[7])):
                    print("bij home; break")
                    break
            except:
                pass
            time.sleep(0.1)


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
    """Test code voor Controller class met vier sliders om de coördinaten van punt 1 en 2 van de bal te bepalen.
    """

    # pc = PController()
    pc = Controller()

    half_dis = (pc.ratio_MM_to_y*pc.KEEPER_DIS)/2
    half_dis = int(half_dis)-1
    master = Tk()
    w1 = Scale(master, from_=5, to=200, orient=HORIZONTAL)
    w1.set(0)
    w1.pack()

    w2 = Scale(master, from_=-(half_dis*2), to=(half_dis*2), orient=HORIZONTAL)
    w2.set(0)
    w2.pack()

    w3 = Scale(master, from_=5, to=200, orient=HORIZONTAL)
    w3.set(0)
    w3.pack()

    w4 = Scale(master, from_=-(half_dis*2), to=(half_dis*2), orient=HORIZONTAL)
    w4.set(0)
    w4.pack()

    Button(master, text='SHOOT!', command=pc.shoot).pack()
    
    co = 0
    co_old = 0
    while(1):
        master.update_idletasks()
        master.update()

        pc.ratio_y_to_MM = (pc.TABLE_LENGTH/200) #200 is hierbij het aantal pixels in de breedte van de tafel
        pc.ratio_MM_to_y = (200/pc.TABLE_LENGTH)

        half_dis = (pc.ratio_MM_to_y*pc.KEEPER_DIS)/2
        _ , co = pc.linear_extrapolation((w1.get(),w2.get()), (w3.get(),w4.get()), 5, half_dis)
        #print(co)

        if co == None:
            co = 0
            pc.test_lin_movement(co)

        if(co != co_old):
            co_old = co
            pc.test_lin_movement(co)
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_h:
                    co = 0
                    w1.set(co)
                    w2.set(co)
                    w3.set(co)
                    w4.set(co)
                    pc.test_lin_movement(co)
                    time.sleep(0.1)
                elif event.key == K_p:
                    if int(pc.driver.transceive_message(0, Commands.GET_EO).decode("utf-8")):
                        pc.driver.transceive_message(0, Commands.SET_EO, 0)
                    else:
                        pc.driver.transceive_message(0, Commands.SET_EO, 1)
                elif event.key == K_v:
                    pc.go_home()

                elif event.key == K_ESCAPE:
                    break
