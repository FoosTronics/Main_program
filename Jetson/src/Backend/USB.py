"""
    Backend om te communiceren met de USB drivers.
    File:
        USB.py
    Datum:
        20-1-2020
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
            Spelling en grammatica commentaren nagekeken
            Engels vertaald naar Nederlands
        1.13:
            HL- HL+ commando's toegevoegd.
        1.14:
            Tabellen toegevoed voor Doxygen
================================================
"""

import usb1
from enum import Enum
import time

class Driver:
    """Klasse om de drivers aan te sturen dmv USB. 
    
    **Author**: 
        Chileam Bohnen \n
    **Version**:
        1.12           \n
    **Date**:
        20-1-2020
    """
    def __init__(self, device_count):
        """Initialiseer de drivers.

        Args:
            device_count: (int) aantal verbonden USB motordrivers.
        
        Tabel:
            | Motordriver instellingen | Waarden |
            |:-------------------------|:--------|
            | VENDOR_ID                | 0x1589  |
            | PRODUCT_ID               | 0xA101  |
            | WRITE ENDPOINT           | 0x02    |
            | READ ENDPOINT            | 0x82    |

            | Motordriver instellingen | Driver 0 | Driver 1 |
            |:-------------------------|:---------|:---------|
            | DRIVER_ID                | 2500     | 1500     |
            | HIGH_SPEED               | 250      | 250      |
            | LOW_SPEED                | 150      | 150      |
            | ACCELERATION             | 25       | 150      |
            | MAX_CURRENT              | 1000     | 1000     |

        """
        self.VENDOR_ID = 0x1589
        self.PRODUCT_ID = 0xA101
        self.w_ENDPOINT = 0x02
        self.r_ENDPOINT = 0x82
        self.INTERFACE_NUMBER = 0
        self.MICRO_STEP = 2
        self.STEP_SIZE = [100, 100]
        self.HIGH_SPEED = [2500, 1500]
        self.LOW_SPEED = [250, 250]
        self.ACCELERATION = [150, 150]
        self.DECELERATION = [25, 150]
        self.MAX_CURRENT = [1000, 1000]
        self.DEVICE_COUNT = device_count
        self.MSG_CR = bytes(13)  # ascii 13 [CR]
        self.DRIVER_ID = ['SDE11', 'SDE03']

        self.context, self.performax_devices = self.driver_init()
        self.descriptors = []
        self.device = usb1.USBDevice
        self.handlers = []
        self.is_open = False

    def stepper_init(self):
        """Deze functie initialiseerd de aangesloten motordrivers.

        Returns:
            (bool) True wanneer initialisatie lukt, anders False
        """
        i = 0
        value = True
        for device in self.performax_devices:
            # Haal beschrijving van het aangesloten USB apparaat op.
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
                i = 1
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
            # Zet mode voor de stappen naar absolute positie.
            value = (self.transceive_message((len(self.handlers) - 1),
                                             Commands.ABS) == Commands.OK.name) if value else False
            # Zet micro-stepping op 2, laagste waarde.
            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_DRVMS,
                                             value=self.MICRO_STEP) == Commands.OK.name) if value else False
            time.sleep(2.5)
            # Schrijf waarden naar flash geheugen.
            value = (self.transceive_message((len(self.handlers) - 1),
                                             Commands.RW) == Commands.OK.name) if value else False
            print("Stuur commando RW naar driver, even geduld a.u.b.")
            time.sleep(2.5)
            # Haal geschreven waarden op.
            print(self.transceive_message((len(self.handlers) - 1), Commands.GET_DRVMS))
            time.sleep(2.5)
            # Valideer geschreven waarde.
            value = (self.transceive_message((len(self.handlers) - 1),
                                             Commands.RR) == Commands.OK.name) if value else False
            print("Stuur commando RR naar driver, even geduld a.u.b.")
            time.sleep(2.5)
            # Zet de stappenmotoren aan.
            value = (self.transceive_message((len(self.handlers) - 1), Commands.SET_EO,
                                             1) == Commands.OK.name) if value else False
            time.sleep(2.5)

        if len(self.handlers) == 2:
            try:
                if ((self.transceive_message(0, Commands.GET_DN).decode("utf-8") == self.DRIVER_ID[1]) and (
                        self.transceive_message(1, Commands.GET_DN).decode("utf-8") == self.DRIVER_ID[0])):
                    self.handlers[0], self.handlers[1] = self.handlers[1], self.handlers[0]
                elif ((self.transceive_message(0, Commands.GET_DN).decode("utf-8") != self.DRIVER_ID[1]) and (
                        self.transceive_message(1, Commands.GET_DN).decode("utf-8") != self.DRIVER_ID[1])):
                    print("ERROR! PANIEK! schiet driver niet gevonden!")
                elif ((self.transceive_message(0, Commands.GET_DN).decode("utf-8") != self.DRIVER_ID[0]) and (
                        self.transceive_message(1, Commands.GET_DN).decode("utf-8") != self.DRIVER_ID[0])):
                    print("ERROR! PANIEK! lineaire beweging driver niet gevonden!")
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
        """Deze functie maakt een USB object aan en maakt een lijst van aangesloten motordrivers.

        Returns:
            (usb1.USBContext, performax_devices[]) usb1.USBContext is het USB object, performax_devices bevat een lijst van motordrivers.
        """
        _context = usb1.USBContext()
        _context.open()
        self.is_open = True
        return _context, self._is_num_device_connected(_context.getDeviceIterator())

    def select_performax_device(self, device_number):
        """Deze functie selecteerd een driver uit de lijst van motordrivers.

        Args:
            (int) nummer van een aangesloten device.
        """
        self.device = self.performax_devices[device_number]

    def get_device_descriptors(self, device):
        """Deze functie haalt het serienummer en productnummer van een aangesloten driver op.
        
        Args:
            (int) nummer van een aangesloten device.
        """
        self.descriptors.append([device.getSerialNumberDescriptor(), device.getProductDescriptor()])

    def open_new_connection(self, device):
        """Deze functie claimt een USB interface en opent de USB verbinding.\n
        De verbinding wordt gemaakt met een geselecteerde driver. zie select_performaxe_device(self, device_number).
        
        Args:
            device: (int) Adres van desbetreffende device.
        
        Returns:
            (handler) afhandelaar van USB-interface.
        """
        # USB context opent een USB afhandelaar
        handler = device.open()
        # USB afhandelaar voert USB handshake uit.
        handler.getASCIIStringDescriptor(descriptor=self.descriptors[len(self.handlers)][0])
        handler.getASCIIStringDescriptor(descriptor=self.descriptors[len(self.handlers)][1])
        # USB afhandelaar claimt USB interface.
        handler.claimInterface(interface=self.INTERFACE_NUMBER)
        # USB afhandelaar maakt verbinding.
        self._open_port(handler)
        # USB afhandelaar leegt lees geheugen.
        self._flush_port(handler)

        return handler

    def open_connection(self, device_num):
        """Deze functie claimt een USB interface en opent de USB verbinding.\n
        De verbinding wordt gemaakt met een geslecteerde driver. zie select_performaxe_device(self, device_number).
        
        Args:
            (int) nummer van een aangesloten device.
        """

        # USB context opent een USB afhandelaar
        # self.handlers[device_num]   .append(self.device.open())
        # USB afhandelaarr voert USB handshake uit.
        self.handlers[device_num].getASCIIStringDescriptor(descriptor=self.descriptors[0])
        self.handlers[device_num].getASCIIStringDescriptor(descriptor=self.descriptors[1])
        # USB afhandelaar caimt USB interface.
        self.handlers[device_num].claimInterface(interface=self.INTERFACE_NUMBER)
        # USB afhandelaar maakt verbinding.
        self._open_port()
        # USB afhandelaar leegt lees geheugen.
        self._flush_port()

    def close_connection(self, handler):
        """Deze functie laat de USB interface los en sluit de USB verbinding.
        
        Args:
            (handler) afhandelaar van het USB-interface.
        """
        # USB afhandelaar sluit de verbinding.
        self._close_port(handler)
        # USB afhandelaar laat USB interface los.
        handler.releaseInterface(interface=self.INTERFACE_NUMBER)
        # USB context sluit USB afhandelaar.
        handler.close()
        self.is_open = False

    def close_connections(self):
        """Deze functie sluit alle verbonden USB verbindingen.
        """
        for handler in self.handlers:
            self.close_connection(handler)

    def transceive_message(self, handler_num, command, value=None, read_size=128):
        """Deze functie verstuurd commando's naar een USB apparaat.

        Args:
            command: (Commands) een commando uit de klasse 'Commands'.

        Kwargs:
            value: (int) een waarde die naar de motordriver geschreven wordt. Standaard None.
            read_size: (int) geheugen grootte voor ontvangen berichten. Standaard 128.

        Returns:
            (bytes) ontvangen bericht. b'OK' of een waarde.
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
        """Controleer of er een motordriver is aangesloten.

        Args:
            devices_list: (list) lijst van adressen van apparaten. 

        Returns:
            (list) lijst van geverifieerde drivers.
        """
        performax_devices = []
        for device in devices_list:
            if (device.getVendorID() == self.VENDOR_ID) and (device.getProductID() == self.PRODUCT_ID):
                performax_devices.append(device)

        return performax_devices

    def _open_port(self, handler):
        """Open een USB poort.
        
        Args:
            handler: (handler) afhandelaar van het USB-interface.
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
            handler: (handler) afhandelaar van het USB-interface.
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
            handler: (handler) afhandelaar van het USB-interface.
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
        
    Tabel:
        | Commando      | Waarde   |
        |:--------------|----------|
        | OK            | b'OK'    |
        | STOP          | b'STOP'  |
        | ABORT         | b'ABORT' |
        | LIMIT_PLUS    | b'L+'    |
        | LIMIT_MIN     | b'L-'    |
        | HOME_PLUS     | b'H+'    |
        | HOME_MIN      | b'H-'    |
        | JPLUS         | b'J+'    |
        | JMIN          | b'J-'    |
        | ABS           | b'ABS'   |
        | INC           | b'INC'   |
        | MM            | b'MM'    |
        | RW            | b'RW'    |
        | RR            | b'RR'    |
        | HOME_PLUS_LOW | b'HL+'   |
        | HOME_MIN_LOW  | b'HL-'   |

        | Commando  | Waarde    |
        |:----------|-----------|
        | SET_DN    | b'DN='    |
        | SET_EO    | b'EO='    |
        | SET_HSPD  | b'HSPD='  |
        | SET_LSPD  | b'LSPD='  |
        | SET_ACC   | b'ACC='   |
        | SET_DEC   | b'DEC='   |
        | SET_X     | b'X'      |
        | SET_PX    | b'PX='    |
        | SET_DRVRC | b'DRVRC=' |
        | SET_DRVMS | b'DRVMS=' |

        | Commando  | Waarde    |
        |:----------|-----------|
        | GET_ID    | b'ID'     |
        | GET_DN    | b'DN'     |
        | GET_EO    | b'EO'     |
        | GET_HSPD  | b'HSPD'   |
        | GET_LSPD  | b'LSDP'   |
        | GET_ACC   | b'ACC'    |
        | GET_DEC   | b'DEC'    |
        | GET_MST   | b'MST'    |
        | GET_PX    | b'PX'     |
        | GET_DRVIC | b'DRVIC'  |
        | GET_DRVMS | b'DRVMS'  |
        | GET_PS    | b'PS'     |

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
    JPLUS = 7, b'J+'
    JMIN = 8, b'J-'
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
