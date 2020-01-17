
"""
    Class for the MPU6050 gyroscope. 

    Reads with I2C the regiseters. Can used in a timer thread or in a function.

    File:
        MPU6050.py
    Date:
        17-1-2020
    Version:
        1.3
    Modifier:
        Kelvin Sweere
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Version management:
        1.0:
            Headers gewijzigd. 
        1.1:
            Functies met underscore gemaakt ipv C++ lowerCamelCase style.
        1.2:
            Docstrings in Google-format (aangevuld)
        1.3:
            Doxygen template toegepast als pilot.
"""
#!/bin/bash

import smbus, math, threading
import time

class MPU6050:
    """
    Class om de mpu6050 gyroscoop aan te sturen dmv I2C. 

    **Author**: 
        Kelvin Sweere \n
    **Version**:
        1.2           \n
    **Date**:
        17-1-2020     
    """
    def __init__(self, i2c_address=0x68, threading=False, debug=False):
        """        
        Args:
            i2c_address: (hexadecimal, optional) I2C adress van de gyroscoop. Standaard I2C adress van de mpu6050 is 0x68.
            threading: (bool) Keuze om het threaden aan te zetten. Variabelen die deze param aanpast is: THREAD_REG_TIME. Standaard False.
            debug: (bool) Keuze om debug berichten weer te geven. Standaard False.
        """
        # params voor i2c bus.
        self.bus = smbus.SMBus(1)        #gevonden met i2cdetect voor de mpu6050 gyro.
        self.address = i2c_address      # This is the address value read via the i2cdetect command
        self.thread_act = threading     # thread active?
        self.debug = debug              

        # params voor de hoeken.
        self.init_hoek_x = 0    # start hoek x
        self.init_hoek_y = 0    # start hoek y
        self.y_hoek = 0         # huidige y hoek
        self.x_hoek = 0         # huidige x hoek

        # params voor de thread in secondes.
        self.THREAD_REG_TIME = 0.2   # warning? -> moet boven self._init_thread()
        
        if(self._try_to_connect()):    #test of iets is aangesloten
            self.bus.write_byte_data(self.address, 0x6b, 0)    #wake-up sensor with register 0x6b (power_mgmt_1)
            self._get_all_register_values()
            self._init_angle_cor()

            if self.thread_act: #de thread mag alleen draaien als connectors goed zijn aangesloten.
                self._init_thread()


    def _init_thread(self):
        """Init de timer thread
        """
        # * t_t = thread_timing
        self.t_t = threading.Timer(self.THREAD_REG_TIME, self._thread_for_registers)
        self.t_t.daemon = True  # Waneer de thread niet meer wordt gebruikt, kill it with fire!
        self.t_t.start()        # Start de thread.


    def _thread_for_registers(self):
        """Geactiveerde functie door de thread, leest de waardes van de gyroscoop.
        """
        self._get_all_register_values()
        self.t_t.run() # zorg dat de thread opnieuw kan wordt gerunt. 
    

    def _init_angle_cor(self):
        """Zorg dat de hoek zoals deze nu staat het nulpunt is.
        """
        self.init_hoek_x = self.get_x_rotation()
        self.init_hoek_y = self.get_y_rotation()
        if self.debug:
            print("Hoek x = ", self.init_hoek_x, ' vanaf nu 0 graden')
            print("Hoek y = ", self.init_hoek_y, ' vanaf nu 0 graden')


    def _read_word(self, adr):
        """lezen van de bus via I2C.
        
        Args:
            adr: (uint16_t) adres naar het te lezen register.   
        
        Returns:
            (uint16_t) register waarde van het adres.
        """
        high = self.bus.read_byte_data(self.address, adr)
        low = self.bus.read_byte_data(self.address, adr+1)
        val = (high << 8) + low     
        return val


    def _read_word_2c(self, adr):
        """leest twee registers uit dmv de functie _read_word(adr)
        
        Args:
            adr: (uint16_t) adres van registers
        
        Returns:
            (uint16_t) register waardes.
        """
        val = self._read_word(adr)
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val  
    

    def _get_all_register_values(self):
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
        """Bereken de hoek dmv pythagoras.
        
        Args:
            a: (int) vector 1.
            b: (int) vector 2.
        
        Returns:
            (int) resulterende vector.
        """
        return math.sqrt((a*a)+(b*b))
    

    def _get_y_rotation(self):
        """Bereken de rotatie van de y-as in graden. 
        """
        radians = math.atan2(self.accel_xout_scaled, self._dist(self.accel_yout_scaled,self.accel_zout_scaled))
        return -math.degrees(radians)   
    

    def _get_x_rotation(self):
        """Bereken de rotatie van de x-as in graden. 
        """
        radians = math.atan2(self.accel_yout_scaled, self._dist(self.accel_xout_scaled,self.accel_zout_scaled))
        return math.degrees(radians)
    

    def get_y_rotation(self):
        """Return de hoek van de de y-as van de MPU6050.

        Note:
            **IOError**: Pinnen van de MPU6050 niet (goed) aangesloten.
        """
        if not self.thread_act:
            self._get_all_register_values() # wordt niet meer gebruikt i.v.m. de thread
        
        try:
            self.y_hoek = self._get_y_rotation()
        except IOError:
            print("MPU6050 niet goed aangesloten. Controlleer pinnen!")
            self.y_hoek = None
        # return min de hoekverdraaiing zoals op het begin.
        return self.y_hoek - self.init_hoek_y


    def get_x_rotation(self):
        """Return de hoek van de de x-as van de MPU6050.

        Note:
            **IOError**: Pinnen van de MPU6050 niet (goed) aangesloten.
        """
        # ** is dikgedrukt in doxygen **

        if not self.thread_act:
            self._get_all_register_values() # wordt niet meer gebruikt i.v.m. de thread
        
        try:
            self.x_hoek = self._get_x_rotation()
        except IOError:
            print("MPU6050 niet goed aangesloten. Controlleer pinnen!")
            self.x_hoek = None
        # return min de hoekverdraaiing zoals op het begin.
        return self.x_hoek - self.init_hoek_x
   

    def _try_to_connect(self):
        """Probeer verbinding te maken met de MPU6050. 
        
        Returns:
            (bool) returnt True als de MPU6050 is gevonden.
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
        print("y rotation = ", int(gyro.get_y_rotation()))
        print("x rotation = ", int(gyro.get_x_rotation()))
        time.sleep(0.5)
        # beweeg in de tussentijd de gyroscoop!
