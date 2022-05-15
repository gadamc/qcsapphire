# Quantum Composer Saphire 9200 Pulser Control

Helper code to communicate with Quantum Composer's
Saphire 9200 TTL pulse generator box.

This code facilitates connections to the device and communication, but
does not offer a full API.

Full API of available commands is found [here](https://www.quantumcomposers.com/_files/ugd/fe3f06_357ff95b25534660b8390c0305582a3f.pdf).

## Installation

```
git clone https://github.com/gadamc/qcsaphire
cd qcsaphire
python setup.py install
```

## Usage

### Determine the port

First, you need to determine the name of the port connected to your device.

```python
import qcsaphire
qcsaphire.discover_devices()
```

Will return a list of ports and information about devices connected to those ports.
For example

```python
[['/dev/cu.BLTH', 'n/a', 'n/a'],
 ['/dev/cu.Bluetooth-Incoming-Port', 'n/a', 'n/a'],
 ['/dev/cu.usbmodem141101',
  'QC-Pulse Generator',
  'USB VID:PID=04D8:000A LOCATION=20-1.1']]
```

### Connection to Pulser

```python
my_pulser = qcsaphire.Pulser('/dev/cu.usmbodem141101')
```

### Communication

For normal usage, all commands sent to the device should use the `query()` method.
The `query()` method will write a command, read the response from the device,
check for errors (raising an Exception when an error is found) and return the string
response if no error is found. For example.

```python
ret_val = my_pulser.query(':PULSE0:STATE?')
print(ret_val)
'ok'
```

The user is responsible for sending the correct command strings by following
[the API](https://www.quantumcomposers.com/_files/ugd/fe3f06_357ff95b25534660b8390c0305582a3f.pdf).
However, there is no need to worry about string encoding and carriage returns / line feeds,
as that is taken care of by the code.
