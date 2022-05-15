import os
import sys
from serial import Serial

def discover_devices():
    '''
    Returns a list of discovered devices.

    Each row in the list contains the
        port, device description, hardware id.

    Find your device and use the port value to instantiate a Pulser object.

    '''

    import serial.tools.list_ports
    if os.name == 'nt':  # sys.platform == 'win32':
        from serial.tools.list_ports_windows import comports
    elif os.name == 'posix':
        from serial.tools.list_ports_posix import comports

    iterator = sorted(comports(include_links=True))
    devices = [[port, desc, hwid] for port, desc, hwid in iterator]
    return devices

#todo -- change all print statements to logger

class Pulser:

    def __init__(self, instpath, timeout=3):
        self.__instpath = instpath
        self.__inst = None
        self._timeout = timeout
        self.open()

    def __del__(self):
        self.close()

    @property
    def instrument(self):
        return self.__inst

    def open(self):
        if self.__inst is not None:
            raise RuntimeError('Device has already been opened.')
        self.__inst = Serial(port=self.__instpath, timeout=self._timeout)

    def close(self):
        if self.__inst is not None:
            self.__inst.close()
            self.__inst = None

    def check_error(self, string):

        if string[0] == '?':
            if string[1] == '1':
                raise Exception('Incorrect prefix, i.e. no colon or * to start command.')
            elif string[1] == '2':
                raise Exception('Missing command keyword.')
            elif string[1] == '3':
                raise Exception('Invalid command keyword.')
            elif string[1] == '4':
                raise Exception('Missing parameter.')
            elif string[1] == '5':
                raise Exception('Invalid parameter.')
            elif string[1] == '6':
                raise Exception('Query only, command needs a question mark.')
            elif string[1] == '7':
                raise Exception('Invalid query, command does not have a query form.')
            elif string[1] == '8':
                raise Exception('Command unavailable in current system state.')
            else:
                raise Exception(f'Unknown Error Indicator {string}')
        return string

    def write(self, data):
        """Write to device.

        Args:
            data (str): write data
        """
        #not sure if this needs to be different for windows/*nix platforms
        newline_char = '\n'
        if sys.platform == 'win32':
            newline_char = '\r\n'

        if not data.endswith(newline_char):
            data += newline_char
        self.__inst.write(data.encode('utf-8'))

    def readline(self):
        """Read from device.

        Returns:
            str: data
        """
        rdata = self.__inst.readline()
        return self.check_error(rdata.decode('utf-8').strip())

    def readlines(self):
        """Read from device.

        Returns:
            str: list of data
        """
        rdata = self.__inst.readlines()
        return [self.check_error(x.decode('utf-8').strip()) for x in rdata]

    def query(self, data):
        """Write to device and read response.

        Args:
            data (str): write data

        Returns:
            str: list of data
        """
        self.write(data)
        if data.upper() in [':INST:COMM?',':INSTRUMENT:COMM?',':INST:COMMANDS?',':INSTRUMENT:COMMANDS?']:
            return_val = self.readlines()
        else:
            return_val = [self.readline()] #we do this so that this function has a consistent return type

        return return_val
