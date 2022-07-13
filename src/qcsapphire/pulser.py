import os
import sys
import collections
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


class Property( object ):
    '''
    Represents a scpi property of the instrument
    '''

    #--- class methods ---

    def __init__( self, inst, name, arg_separator = ':' ):
        '''
        Represents a call to a SCPI instrument's property or method.
        :param inst: A SCPI instrument resource.
        :param name: Name of the property.
            Used to recursively build the property call message.
        :param arg_separator: Separator to use to separate
            arguments in a method call.
            [Default: ':']
        '''
        self._pulser = inst  # a Pulser object
        self.name = name.upper()
        self.arg_separator = arg_separator


    def __getattr__( self, name ):
        return Property(
            self._pulser,
            ':'.join( ( self.name, name.upper() ) ),
            arg_separator = self.arg_separator
        )


    def __call__( self, *values ):
        if len( values ) == 0:
            # get property
            return self._pulser.query( f'{self.arg_separator}{ self.name }?')

        else:
            # set value
            def _to_str(val):
                if type(val) == str:
                    return val
                if type(val) == int:
                    return str(val)
                else:
                    return '{:.8f}'.format(val)

            values = [ _to_str( val ) for val in values ]
            values = self.arg_separator.join( values )

            cmd = f'{self.arg_separator}{ self.name } { values }'
            return self._pulser.query( cmd )


class Pulser:

    def __init__(self, port, timeout=3):
        self._port = port
        self._inst = None
        self._timeout = timeout
        self.arg_separator = ':'
        self.last_write_command = None
        self.open()
        self._command_history = collections.deque(maxlen=1000)
        self._read_hardware_versions()

## PRIVATE
    def __del__(self):
        self.close()

    def __enter__( self ):
        return self

    def __exit__( self, exc_type, exc_value, traceback ):
        self.close()

    def __getattr__( self, name ):
        resp = Property( self, name, arg_separator = self.arg_separator )
        return resp

    def _check_error(self, string):

        try:
            if string[0] == '?':
                if string[1] == '1':
                    raise Exception(f'Incorrect prefix, i.e. no colon or * to start command. Last write command == {self.last_write_command}')
                elif string[1] == '2':
                    raise Exception(f'Missing command keyword. Last write command == {self.last_write_command}')
                elif string[1] == '3':
                    raise Exception(f'Invalid command keyword. Last write command == {self.last_write_command}')
                elif string[1] == '4':
                    raise Exception(f'Missing parameter. Last write command == {self.last_write_command}')
                elif string[1] == '5':
                    raise Exception(f'Invalid parameter. Last write command == {self.last_write_command}')
                elif string[1] == '6':
                    raise Exception(f'Query only, command needs a question mark. Last write command == {self.last_write_command}')
                elif string[1] == '7':
                    raise Exception(f'Invalid query, command does not have a query form. Last write command == {self.last_write_command}')
                elif string[1] == '8':
                    raise Exception(f'Command unavailable in current system state. Last write command == {self.last_write_command}')
                else:
                    raise Exception(f'Unknown Error Indicator {string}. Last write command == {self.last_write_command}')
        except Exception as e:
            self._readlines() #flush out the read return on error to be ready for next query
            raise e

        return string

    def _write(self, data):
        '''
        Write to device.

        Args:
            data (str): write data
        '''

        #not sure if this needs to be different for windows/*nix platforms
        newline_char = '\n'
        if sys.platform == 'win32':
            newline_char = '\r\n'

        if not data.endswith(newline_char):
            data += newline_char

        self._inst.write(data.encode('utf-8'))

        #we put this below the .write method in case it raises an exception
        self.last_write_command = data.strip()
        self._command_history.append(data.strip())

    def _readline(self):
        '''
        Read from device.

        Returns:
            a string response from the device.
        '''
        rdata = self._inst.readline()
        return self._check_error(rdata.decode('utf-8').strip())

    def _readlines(self):
        '''
        Read from device.

        Returns:
            a list of strings from the device.
        '''
        rdata = self._inst.readlines()
        return [self._check_error(x.decode('utf-8').strip()) for x in rdata]

    def _read_hardware_versions(self):
        res_str = self.query('*IDN?')
        _, model_number, serial_number, firm_fpga = res_str.split(',')
        self.model_number = model_number
        self.serial_number = serial_number
        self.firmware_version, self.fpga_version = firm_fpga.split('-')

    def _convert_channel_name_to_int(self, channel):

        assert type(channel) in [type('A'), type(0)]
        channels = self.channel_names()

        if type(channel) == type('A'):
            if channels.index(channel) == -1:
                raise ValueError(f'Incorrect channel name. {channel} not in {channels}')
            channel = channels.index(channel)
        else:
            assert channel in list(range(len(channels)))

        return channel

## PUBLIC

    def open(self):
        if self._inst is None:
            self._inst = Serial(port=self._port, timeout=self._timeout)

    def close(self):
        if self._inst is not None:
            self._inst.close()
            self._inst = None

    def query(self, data):
        '''
        Write to device and read response.

        Args:
            data (str)

        Returns:
            a string response from the device.

            IF the argument to this fuction, data = ":INST:COMM?", however,
            the return is a list of strings from the device.
        '''
        self._write(data)
        if data.upper() in [':INST:COMM?',':INSTRUMENT:COMM?',':INST:COMMANDS?',':INSTRUMENT:COMMANDS?']:
            return_val = self._readlines()
        else:
            return_val = self._readline()

        return return_val

    def multiplex(self, timer_channels, output_channel):
        mux_value = 0
        for timer in timer_channels:
            timer_chan = self._convert_channel_name_to_int(timer)
            mux_value += 2**(timer_chan - 1) #channel A starts at 1

        return self.channel(output_channel).mux(mux_value)

    def flush(self):
        return self._readlines()

    def report_hardware(self):
        return [self.model_number, self.serial_number, self.firmware_version, self.fpga_version]

    def report_global_settings(self):
        system_command_list = ['STATE','PERIOD','MODE','BCOUNTER','PCOUNTER',
                                'OCOUNTER','EXTERNAL:MODE','EXTERNAL:LEVEL',
                                'EXTERNAL:EDGE','EXTERNAL:POLARITY']

        setting_vals = []
        for c in system_command_list:
            command = f':PULSE0:{c}?'
            setting_vals.append( (command, self.query(command)) )

        return setting_vals

    def report_channel_settings(self, channel):

        channel = self._convert_channel_name_to_int(channel)

        channel_command_list = ['STATE','WIDTH','DELAY','SYNC','MUX',
                                'POLARITY','OUTPUT:AMPLITUDE','CMODE',
                                'BCOUNTER','PCOUNTER','OCOUNTER','WCOUNTER','CGATE']

        setting_vals = []
        for c in channel_command_list:
            command = f':PULSE{channel}:{c}?'
            setting_vals.append( (command, self.query(command) ))

        return setting_vals

    def command_history(self):
        '''
        returns an iterator to the most recent 1000 commands
        sent to the device by an instance of this class.

        The interator is in order of most recent command first.

        '''
        return reversed(self._command_history)

## Special COMMANDS
    def software_trigger(self):
        '''
        Issue software trigger: '*TRG'
        '''
        return self.query('*TRG')

## Helper Functions

    def get_number_of_channels(self):
        if self.model_number.startswith('9214'):
            return 4
        if self.model_number.startswith('9212'):
            return 2
        else:
            return -1

    def set_all_state_off(self):
        self.pulse0.state(0)
        self.pulse1.state(0)
        self.pulse2.state(0)
        if self.model_number.startswith('9214'):
            self.pulse3.state(0)
            self.pulse4.state(0)

    def channel(self, chan):
        '''
        alias to Pulser.pulse(chan)
        '''
        return self.pulse(chan)


    def channel_names(self):
        if self.model_number.startswith('9214'):
            channels = ['T', 'A', 'B', 'C', 'D']
        else:
            channels = ['T', 'A', 'B']

        return channels

    def pulse(self, chan):
        chan = self._convert_channel_name_to_int(chan)
        return self.__getattr__(f'pulse{chan}')

    @property
    def system(self):
        return self.channel("T")
