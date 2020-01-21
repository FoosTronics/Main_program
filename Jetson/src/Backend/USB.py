"""
    Backend to communicate with the USB drivers. 

    File:
        USB.py
    Datum:
        16-1-2020
    Versie:
        1.12
    Authors:
        Chileam Bohnen
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Version management:
        1.0:
            Header toegevoegd
        1.10:
            Docstrings toegevoegd.
        1.11:
            Doxygen template toegepast.
        1.12:
            HL- HL+ commando's toegevoegd.
================================================
"""

import usb1
from enum import Enum
import time

class Driver:
    """Class om de drivers aan te sturen dmv USB. 
    
    **Author**: 
        Chileam Bohnen \n
    **Version**:
        1.11           \n
    **Date**:
        16-1-2020  
    """
    def __init__(self, device_count):
        """Initaliseer de drivers.

        Args:
            device_count: (int) aantal verbonden USB stepper drivers
        """
        self.VENDOR_ID = 0x1589
        self.PRODUCT_ID = 0xA101
        self.w_ENDPOINT = 0x02
        self.r_ENDPOINT = 0x82
        self.INTERFACE_NUMBER = 0
        self.MICRO_STEP = 2
        self.STEP_SIZE = [100, 100]
        self.HIGH_SPEED = [2500, 2500]
        self.LOW_SPEED = [150, 150]
        self.ACCELERATION = [100, 150]
        self.DECELERATION = [1, 1]
        self.MAX_CURRENT = [1000, 1000]
        self.DEVICE_COUNT = device_count
        self.MSG_CR = bytes(13)  # ascii 13 [CR]
        self.DRIVER_ID = ['SDE11', 'SDE03']

        # TODO SET_DRVMS naar ratio 2 voor halfstep (fullstep is niet mogelijk)

        self.context, self.performax_devices = self.driver_init()
        self.descriptors = []
        self.device = usb1.USBDevice
        self.handlers = []
        self.is_open = False

    def stepper_init(self):
        """Deze functie initialiseerd de aangesloten stepper drivers.

        Returns:
            (bool) True wanneer initialisatie lukt, anders False
        """
        i = 0
        value = True
        for device in self.performax_devices:
            # Haal beschrijving van aangesloten USB apparaat op.
            self.get_device_descriptors(device)
            # Open een USB verbinding.
            handler = self.open_new_connection(device)
            self.handlers.append(handler)
            # Zet maximale stapsnelheid.

            if (self.transceive_message((len(self.handlers) - 1), Commands.GET_DN).decode("utf-8") == self.DRIVER_ID[
                0]):
                i = 0
            elif (self.transceive_message((len(self.handlers) - 1), Commands.GET_DN).decode("utf-8") == self.DRIVER_ID[
                1]):
                i = 0
            else:
                value = False

            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_HSPD,
                                             value=self.HIGH_SPEED[i]) == Commands.OK.name) if value else False
            # Zet minimale stapsnelheid.
            print(len(self.handlers) - 1)
            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_LSPD,
                                             value=self.LOW_SPEED[i]) == Commands.OK.name) if value else False
            # Zet versnellingstijd.
            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_ACC,
                                             value=self.ACCELERATION[i]) == Commands.OK.name) if value else False
            # Zet vertragingstijd.
            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_DEC,
                                             value=self.DECELERATION[i]) == Commands.OK.name) if value else False
            # Zet maximale stroom per wikkeling.
            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_DRVRC,
                                             value=self.MAX_CURRENT[i]) == Commands.OK.name) if value else False
            # Zet stepper modes in absolute positie.
            value = (self.transceive_message((len(self.handlers) - 1),
                                             Commands.ABS) == Commands.OK.name) if value else False
            # Zet micro stepping op 2, laagste waarde.
            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_DRVMS,
                                             2) == Commands.OK.name) if value else False
            time.sleep(2.5)
            # schrijf waarden naar flash.
            value = (self.transceive_message((len(self.handlers) - 1),
                                             Commands.RW) == Commands.OK.name) if value else False
            print("send command RW to driver, please wait")
            time.sleep(2.5)
            # Haal geschreven waarden op.
            print(self.transceive_message((len(self.handlers) - 1), Commands.GET_DRVMS))
            time.sleep(2.5)
            # Valideer geschreven waarde.
            value = (self.transceive_message((len(self.handlers) - 1),
                                             Commands.RR) == Commands.OK.name) if value else False
            print("send command RR to driver, please wait")
            time.sleep(2.5)
            # Zet de stepper motors aan.
            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_EO,
                                             1) == Commands.OK.name) if value else False
            time.sleep(2.5)
            # Sluit de USB verbinding
            # if(i==0):
            #     self.device2 = device
            #     #self.device2.stuur("shoot")
            #     self.transceive_message((len(self.handlers)-1), Commands.SET_DN, self.LIN_MOV_DRIVER_ID)
            # if(i==1):
            #     self.transceive_message((len(self.handlers)-1), Commands.SET_DN, self.SHOOT_MOV_DRIVER_ID)

            # self.close_connection()
            # i=+1

        if (len(self.handlers) == 2):
            try:
                if ((self.transceive_message(0, Commands.GET_DN).decode("utf-8") == self.DRIVER_ID[1]) and (
                        self.transceive_message(1, Commands.GET_DN).decode("utf-8") == self.DRIVER_ID[0])):
                    self.handlers[0], self.handlers[1] = self.handlers[1], self.handlers[0]
                elif ((self.transceive_message(0, Commands.GET_DN).decode("utf-8") != self.DRIVER_ID[1]) and (
                        self.transceive_message(1, Commands.GET_DN).decode("utf-8") != self.DRIVER_ID[1])):
                    print("ERROR! PANIEK! shooter driver niet gevonden!")
                elif ((self.transceive_message(0, Commands.GET_DN).decode("utf-8") != self.DRIVER_ID[0]) and (
                        self.transceive_message(1, Commands.GET_DN).decode("utf-8") != self.DRIVER_ID[0])):
                    print("ERROR! PANIEK! linear movemnt driver niet gevonden!")
                else:
                    print(self.transceive_message(0, Commands.GET_DN).decode("utf-8"))
                    print(self.transceive_message(1, Commands.GET_DN).decode("utf-8"))
                    print(self.transceive_message(0, Commands.GET_DN).decode("utf-8"))
            except:
                pass
        # else:
        #     value = False

        return value

    def driver_init(self):
        """Deze functie maakt een USB object aan en maakt een lijst van aangesloten stepper drivers.

        Returns:
            (usb1.USBContext, performax_devices[]) usb1.USBContext is het USB object, performax_devices bevat een lijst van stepper drivers.
        """
        _context = usb1.USBContext()
        _context.open()
        self.is_open = True
        return _context, self._is_num_device_connected(_context.getDeviceIterator())

    def select_performax_device(self, device_number):
        """Deze functie selecteerd een driver uit de lijst van stepper drivers.

        Args:
            device_number: (int) adres van het device. 
        """
        self.device = self.performax_devices[device_number]

    def get_device_descriptors(self, device):
        """Deze fucntie haalt het serienummer en productnummer van een aangesloten driver op.
        
        Args:
            device: (int) adress van desbetreffende  device.
        """
        self.descriptors.append([device.getSerialNumberDescriptor(), device.getProductDescriptor()])

    def open_new_connection(self, device):
        """Deze functie claimt een USB interface en opent de USB verbinding.\n
        De verbinding wordt gemaakt met een geslecteerde driver. zie select_performaxe_device(self, device_number).
        
        Args:
            device: (int) Adress van desbetreffende device.
        
        Returns:
            (handler) handle naar USB device. 
        """
        # USB context opent een USB handler
        handler = device.open()
        # USB handler voert USB handshake uit.
        handler.getASCIIStringDescriptor(descriptor=self.descriptors[len(self.handlers)][0])
        handler.getASCIIStringDescriptor(descriptor=self.descriptors[len(self.handlers)][1])
        # USB handler caimt USB interface.
        handler.claimInterface(interface=self.INTERFACE_NUMBER)
        # USB handler maakt verbinding.
        self._open_port(handler)
        # USB handler leegt lees geheugen.
        self._flush_port(handler)

        return handler

    def open_connection(self, device_num):
        """Deze functie claimt een USB interface en opent de USB verbinding.\n
        De verbinding wordt gemaakt met een geslecteerde driver. zie select_performaxe_device(self, device_number).
        
        Args:
            device_num: (int) adres van het device. 
        """

        # USB context opent een USB handler
        # self.handlers[device_num]   .append(self.device.open())
        # USB handler voert USB handshake uit.
        self.handlers[device_num].getASCIIStringDescriptor(descriptor=self.descriptors[0])
        self.handlers[device_num].getASCIIStringDescriptor(descriptor=self.descriptors[1])
        # USB handler caimt USB interface.
        self.handlers[device_num].claimInterface(interface=self.INTERFACE_NUMBER)
        # USB handler maakt verbinding.
        self._open_port()
        # USB handler leegt lees geheugen.
        self._flush_port()

    def close_connection(self, handler):
        """Deze functie laat de USB interface los en sluit de USB verbinding.
        
        Args:
            handler: (handler) handle naar de USB.
        """
        # USB hanlder sluit de verbinding.
        self._close_port(handler)
        # USB handler laat USB interface los.
        handler.releaseInterface(interface=self.INTERFACE_NUMBER)
        # USB context sluit USB hanlder.
        handler.close()
        self.is_open = False

    def close_connections(self):
        """Deze functie sluit alle verbonden USB verbinding.
        """
        for handler in self.handlers:
            self.close_connection(handler)

    def transceive_message(self, handler_num, command, value=None, read_size=128):
        """Deze functie verstuurd commando's naar een USB device.

        Args:
            command: (Commands) een commando uit class 'Commands'.

        Kwargs:
            value: (int) een waarde die naar de stepper driver geschreven wordt. Standaard None.
            read_size: (int) geheugen grote voor ontvangen berichten. Standaard 128.

        Returns:
            response: (bytes) ontvangen bericht. b'OK' of een waarde.
        """
        if value is not None:
            msg = command.name + bytearray(str(value), 'utf-8') + self.MSG_CR
        else:
            msg = command.name + self.MSG_CR

        self.handlers[handler_num].bulkWrite(endpoint=self.w_ENDPOINT, data=msg, timeout=1000)
        response = self.handlers[handler_num].bulkRead(endpoint=self.r_ENDPOINT, length=read_size, timeout=1000)
        response = response.split(b"\x00")[0]
        return response

    def _is_num_device_connected(self, devices_list):
        """Check of een stappenmotordriver device is aangesloten.

        Args:
            devices_list: (list) list van adressen van devices. 

        Returns:
            performax_devices: (list) list van geverifieerde drivers.
        """
        performax_devices = []
        for device in devices_list:
            if (device.getVendorID() == self.VENDOR_ID) and (device.getProductID() == self.PRODUCT_ID):
                performax_devices.append(device)

        return performax_devices

    def _open_port(self, handler):
        """Open een USB poort.
        
        Args:
            handler: (handler) handle naar de USB.
        """
        _null_msg = bytearray('', 'utf-8')
        handler.controlWrite(
            request_type=0x40,
            request=0x02,
            value=0x02,
            index=0x00,
            data=_null_msg,
        )

    def _flush_port(self, handler):
        """Maak de USB connectie leeg.
        
        Args:
            handler: (handler) handle naar de USB.
        """
        _null_msg = bytearray('', 'utf-8')
        handler.controlWrite(
            request_type=0x40,
            request=0x02,
            value=0x01,
            index=0x00,
            data=_null_msg,
        )

    def _close_port(self, handler):
        """Sluit de USB connectie.
        
        Args:
            handler: (handler) handle naar de USB.
        """
        _null_msg = bytearray('', 'utf-8')
        handler.controlWrite(
            request_type=0x40,
            request=0x02,
            value=0x04,
            index=0x00,
            data=_null_msg,
        )


class Commands(Enum):
    """Enum van mogelijke commando's die uit de datasheet van de Arcus Arcus Technology ACE-SDE zijn gehaald.
    
    Args:
        Enum (Enum): Enum van lijst van commando's.
    """
    def __init__(self, value, name):
        self._value_ = value
        self._name_ = name

    # From 0: Normal commando's
    OK = 0, b'OK'
    STOP = 1, b'STOP'
    ABORT = 2, b'ABORT'
    LIMIT_PLUS = 3, b'L+'
    LIMIT_MIN = 4, b'L-'
    HOME_PLUS = 5, b'H+'
    HOME_MIN = 6, b'H-'
    JPLUS = 7, b'JPLUS'
    JMIN = 8, b'JMIN'
    ABS = 9, b'ABS'
    INC = 10, b'INC'
    MM = 11, b'MM'
    RW = 12, b'RW'
    RR = 13, b'RR'
    HOME_PLUS_LOW = 14, b'HL+'
    HOME_MIN_LOW = 15, b'HL-'

    # From 100: Set commando's
    SET_DN = 100, b'DN='
    SET_EO = 101, b'EO='
    SET_HSPD = 102, b'HSPD='
    SET_LSPD = 103, b'LSPD='
    SET_ACC = 104, b'ACC='
    SET_DEC = 105, b'DEC='
    SET_X = 106, b'X'
    SET_PX = 107, b'PX='
    SET_DRVRC = 108, b'DRVRC='
    SET_DRVMS = 109, b'DRVMS='

    # From 200: Get commando's
    GET_ID = 200, b'ID'
    GET_DN = 201, b'DN'
    GET_EO = 202, b'EO'
    GET_HSPD = 203, b'HSPD'
    GET_LSPD = 204, b'LSDP'
    GET_ACC = 205, b'ACC'
    GET_DEC = 206, b'DEC'
    GET_MST = 207, b'MST'
    GET_PX = 208, b'PX'
    GET_DRVIC = 209, b'DRVIC'
    GET_DRVMS = 210, b'DRVMS'
    GET_PS = 211, b'PS'
