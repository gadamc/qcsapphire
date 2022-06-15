# Quantum Composer Sapphire 9200 Pulser Control

Helper code to communicate with [Quantum Composer's
Sapphire 9200 TTL pulse generator](https://www.quantumcomposers.com/_files/ugd/fe3f06_357ff95b25534660b8390c0305582a3f.pdf).

This code facilitates connections to the device, communication, error handling and system status.

## Installation

```
git clone https://github.com/gadamc/qcsapphire
cd qcsapphire
python -m pip install .
```

## Usage

### Determine the port


```python
import qcsapphire
qcsapphire.discover_devices()
```

Will return a list of ports and information about devices connected to those ports.
For example, on *nix platforms, you may see

```python
[['/dev/cu.BLTH', 'n/a', 'n/a'],
 ['/dev/cu.Bluetooth-Incoming-Port', 'n/a', 'n/a'],
 ['/dev/cu.usbmodem141101',
  'QC-Pulse Generator',
  'USB VID:PID=04D8:000A LOCATION=20-1.1']]
```

The device here is connected to `\dev\cu.usbmodem141101`.

On Windows you may see

```python
[['COM3',
  'Intel(R) Active Management Technology - SOL (COM3)',
  'PCI\\VEN_8086&DEV_43E3&SUBSYS_0A541028&REV_11\\3&11583659&1&B3'],
 ['COM5',
  'USB Serial Device (COM5)',
  'USB VID:PID=0483:A3E5 SER=206A36705430 LOCATION=1-2:x.0'],
 ['COM6',
  'USB Serial Device (COM6)',
  'USB VID:PID=04D8:000A SER= LOCATION=1-8:x.0'],
 ['COM7',
  'USB Serial Device (COM7)',
  'USB VID:PID=239A:8014 SER=3B0D07C25831555020312E341A3214FF LOCATION=1-6:x.0']]
  ```

It is certainly not obvious to which USB port the QC Sapphire is connected. However,
using the Windows Task Manager, as well as trial and error, should eventually
reveal the correct serial port to use. In this case, `COM6`.

### Connection to Pulser

```python
my_pulser = qcsapphire.Pulser('COM6')
```

### Communication

For normal usage, all commands sent to the device should use the `query()` method or
with property-like calls (see section below).

The `query()` method will write a command, read the response from the device,
check for errors (raising an Exception when an error is found) and return the string
response. For example,

```python
ret_val = my_pulser.query(':PULSE0:STATE?')
print(ret_val)
'0'
```

```python
ret_val = my_pulser.query(':PULSE1:WIDTH 0.000025')
print(ret_val)
'ok'

ret_val = my_pulser.query(':PULSE1:WIDTH?')
print(ret_val)
'0.000025000'
```

#### Property-Like Calls

It's possible to make the same calls to the pulser using a property-like call.
Instead of calling `my_pulser.query("command1:subcommand:subsubcommand value")`,
one can call `my_pulser.command1.subcommand.subsubcommand(value)`, which is more readable.

For example,

```python
ret_val = my_pulser.pulse1.width(0.000025) #sets the width of channel A
print(ret_val) # 'ok'

width = my_pulser.pulse1.width() #asks for the width of channel A
print(width) # '0.000025000'
```

All of the SCPI commands can be built this way.

In either case, the user is responsible
for sending the correct command strings by following
[the API](https://www.quantumcomposers.com/_files/ugd/fe3f06_357ff95b25534660b8390c0305582a3f.pdf).
It should be pointed out there is no need to worry about string encoding and carriage returns / line feeds,
as that is taken care of by the code.

### Global and Channel States

Two methods exist to report on global and channel settings

##### Global Settings

```python
import pprint
pp = pprint.PrettyPrinter(indent=4)

pp.pprint(my_pulser.report_global_settings())
```

##### Channel Settings

```python
for channel in range(1,5):
    pp.pprint(f'channel {channel}')
    pp.pprint(my_pulser.report_channel_settings(channel))
```

### Examples

After reading the documentation for the device, you'll notice there
are four output channels (A, B, C and D) and an internal global system.

The internal global system is referenced as `:PULSE0` (or `my_pulser.pulse0`).
To the output channels are references as (A = `pulse1`, B = `pulse2'`, C = `pulse3`,
and D = `pulse4`).


#### Continuous Pulse on Channel A

```python
import qcsapphire

my_pulser = qcsapphire.Pulser('COM6')

my_pulser.pulse0.mode('normal')
my_pulser.pulse0.period(1.00) #1 second period on internal trigger
my_pulser.pulse0.external.mode('disabled')
my_pulser.pulse1.cmode('normal')
my_pulser.pulse1.polarity('normal')
my_pulser.pulse1.width(0.05) #50 ms wide pulse

#don't turn on yet
my_pulser.pulse1.state(0)
my_pulser.pulse0.state(0)

#turn on Pulser
my_pulser.pulse0.state(1) #turns on internal signal (pulse0)
my_pulser.pulse1.state(1) #turns on channel A (A = pulse1, B = pulse2, C = pulse3, D = pulse4)
```

#### Trigger Pulses on Channel A via Software Trigger

```python
my_pulser.pulse0.mode('single')
my_pulser.pulse0.period(0.2) #200 ms system pulse
my_pulser.pulse0.external.mode('trigger')
my_pulser.pulse1.cmode('single')
my_pulser.pulse1.polarity('normal')
my_pulser.pulse1.width(0.05) #50 ms wide pulse
my_pulser.pulse1.state(0)
my_pulser.pulse0.state(0)


#trigger loop example

#wait N seconds between triggers
wait_N = 5.0
N_pulses = 50

#activate pulser and output channel
my_pulser.pulse0.state(1)
my_pulser.pulse1.state(1)

for i in range(N_pulses):
    my_pulser.software_trigger() #trigger the pulser
    time.sleep(wait_N)

#deactivate
my_pulser.pulse0.state(0)
my_pulser.pulse1.state(0)
```


### Debugging

If you hit an error, especially when trying to use the property-like calls,
the last string written to the Serial port is found in the
`.last_write_command` attribute of the pulser object.

```python
my_pulser.pulse1.width(25e-6)
print(my_pulser.last_write_command)
# ':PULSE1:WIDTH 2.5e-05'
```

Additionally, you can see the recent command history of the object (last 1000 commands)

```python
for command in my_pulser.command_history():
  print(command)
```

# LICENSE

[LICENCE](LICENSE)

##### Acknowledgments

The `Property` class of this code was taken from `easy-scpi`: https://github.com/bicarlsen/easy-scpi
and modified.
