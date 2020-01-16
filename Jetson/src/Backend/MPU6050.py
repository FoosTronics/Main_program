#!/bin/bash
"""Class voor de MPU6050 gyroscoop.

Leest d.m.v. I2C de MPU6050 gyroscoop uit. Kan gebruikt worden met een timer thread
en een functie. 

Programmer(s):
    Kelvin Sweere
Date:
    9-12-2019
Tester:
    ...
Test Done:
    Not yet

Python Packages:
    - smbus (i2c)
    - math
    - threading 
"""

import smbus, math, threading
import time

class MPU6050:
    def __init__(self, i2c_address=0x68, threading=False, debug=False):
        """Init van de class. 
        
        Args:
            i2c_address (hexadecimal): I2C adress van de gyroscoop. Standard I2C adress van de mpu6050 is 0x68.
            threading (bool): Keuze om het threaden aan te zetten. Variabelen die deze param aanpast is: THREAD_REG_TIME. Standaard False.
            debug (bool): Keuze om debug berichten weer te geven. Standaard False.
        """
        # params voor i2c bus.
        self.bus = smbus.SMBus(1)   #gevonden met i2cdetect voor de mpu6050 gyro.
        self.address = i2c_address      # This is the address value read via the i2cdetect command
        self.thread_act = threading     # thread active?
        self.debug = debug

        # params voor de hoeken.
        self.init_hoek_x = 0    # start hoek x
        self.init_hoek_y = 0    # start hoek y
        self.y_hoek = 0         # huidige y hoek
        self.x_hoek = 0         # huidige x hoek

        # params voor de thread
        self.THREAD_REG_TIME = 0.2   # moet boven self._init_thread()
        
        if(self._tryToConnect()):    #test of iets is aangesloten
            self.bus.write_byte_data(self.address, 0x6b, 0)    #wake-up sensor with register 0x6b (power_mgmt_1)
            self._getAllRegisterValues()
            #TODO: nog niet getest!
            self._init_hoek_cor()
            # ! ------------------

            if self.thread_act: #de thread mag alleen draaien als connectors goed zijn aangesloten.
                self._init_thread()

    def _init_thread(self):
        """Init de timer thread
        """
        # * t_t = thread_timing
        self.t_t = threading.Timer(self.THREAD_REG_TIME, self._thread_for_registers)
        self.t_t.daemon = True  # Waneer de thread niet meer wordt gebruikt, kill it with fire!
        self.t_t.start()    # Start de thread.

    def _thread_for_registers(self):
        """
        Geactiveerde functie door de thread. Handelt het lezen + corrigeren steppers af.
        """

        self._getAllRegisterValues()

        self.t_t.run() # zorg dat de thread opnieuw kan wordt gerunt. 
    
    def _init_hoek_cor(self):
        self.init_hoek_x = self.getXRotation()
        self.init_hoek_y = self.getYRotation()
        if self.debug:
            print("Hoek x = ", self.init_hoek_x, ' vanaf nu 0 graden')
            print("Hoek y = ", self.init_hoek_y, ' vanaf nu 0 graden')

    def _read_word(self, adr):
        """lezen van de bus.
        
        Args:
            adr (uint16_t): adres naar het te lezen register.   
        
        Returns:
            uint16_t: register waarde van het adres.
        """
        high = self.bus.read_byte_data(self.address, adr)
        low = self.bus.read_byte_data(self.address, adr+1)
        val = (high << 8) + low     
        return val

    def _read_word_2c(self, adr):
        """leest twee registers uit d.m.v. de functie _read_word(adr)
        
        Args:
            adr (uint16_t): adres van registers
        
        Returns:
            uint16_t: register waardes.
        """
        val = self._read_word(adr)
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val  
    
    def _getAllRegisterValues(self):
        """Leest alle registers uit van de MPU6050.
        """
        self.gyro_xout = self._read_word_2c(0x43)
        self.gyro_yout = self._read_word_2c(0x45)
        self.gyro_zout = self._read_word_2c(0x47)

        self.accel_xout = self._read_word_2c(0x3b)
        self.accel_yout = self._read_word_2c(0x3d)
        self.accel_zout = self._read_word_2c(0x3f)

        self.accel_xout_scaled = self.accel_xout / 16384.0
        self.accel_yout_scaled = self.accel_yout / 16384.0
        self.accel_zout_scaled = self.accel_zout / 16384.0
         
    
    def _dist(self, a,b):
        """Bereken de hoek d.m.v. pythagoras.
        
        Args:
            a (int): vector 1.
            b (int): vector 2.
        
        Returns:
            int: resulterende vector.
        """
        return math.sqrt((a*a)+(b*b))
    
    def _get_y_rotation(self):
        radians = math.atan2(self.accel_xout_scaled, self._dist(self.accel_yout_scaled,self.accel_zout_scaled))
        return -math.degrees(radians)   
    
    def _get_x_rotation(self):
        radians = math.atan2(self.accel_yout_scaled, self._dist(self.accel_xout_scaled,self.accel_zout_scaled))
        return math.degrees(radians)
    
    def getYRotation(self):
        """
        Return de hoek van de de y-as van de MPU6050.
        """
        if not self.thread_act:
            self._getAllRegisterValues() # wordt niet meer gebruikt i.v.m. de thread
        
        try:
            self.y_hoek = self._get_y_rotation()
        except IOError:
            print("MPU6050 niet goed aangesloten. Controlleer pinnen!")
            self.y_hoek = None
        # return min de hoekverdraaiing zoals op het begin.
        return self.y_hoek - self.init_hoek_y


    def getXRotation(self):
        """
        Return de hoek van de de x-as van de MPU6050.
        """
        if not self.thread_act:
            self._getAllRegisterValues() # wordt niet meer gebruikt i.v.m. de thread
        
        try:
            self.x_hoek = self._get_x_rotation()
        except IOError:
            print("MPU6050 niet goed aangesloten. Controlleer pinnen!")
            self.x_hoek = None
        # return min de hoekverdraaiing zoals op het begin.
        return self.x_hoek - self.init_hoek_x
   
    def _tryToConnect(self):
        """Probeer verbinding te maken met de MPU6050. 
        
        Returns:
            bool: returnt True als de MPU6050 is gevonden.
        """
        try:
            # self.bus.write_byte_data(self.address, self.power_mgmt_1, 0)    #wake-up sensor
            self._read_word_2c(0x45)    
        except IOError:
            print("MPU6050 niet goed aangesloten. Controlleer de pinnen!")
            return 0
        else:
            if(self.debug):
                print("MPU6050 kan gebruikt worden.")
            return 1
 
if __name__ == "__main__":
    print("Testscript voor mpu6050.py")
    gyro = MPU6050(i2c_address=0x68, threading=True, debug=True)    #init class
        
    while True:
        print("y rotation = ", int(gyro.getYRotation()))
        print("x rotation = ", int(gyro.getXRotation()))

        time.sleep(0.5)
    
    # beweeg in de tussentijd de gyroscoop!