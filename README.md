
# TAStm32

This is a python library for controlling a [TAStm32 replay device](https://github.com/Ownasaurus/TAStm32/tree/master)


## Installation

Install tastm32 with pip

```bash
  pip install tastm32
```

## Executables

Provides the following executables

`tastm32-play` Play files using cli arguments

`tastm32-tasd` Play TASD files directly (Experimental)

`tastm32-clear` Reset the state of the TAStm32 device

`tastm32-controller` Basic mapping of XInput controller to SNES

`tastm32-dfu` Reset TAStm32 into DFU firmware mode

`tastm32-dumpinfo` Query and display a variety of infomation baked into the firmware onboard the TAStm32

`tastm32-ping` Simple ping of the device to confirm communication

`tastm32-power` Manage Reset pin state (On, Off, Reset)

`tastm32-remote` Basic CLI app for sending single inputs

`tastm32-stream-nes-mono` Script for streaming raw pcm audio to a NES (for JukeNES payload)

`tastm32-stream-snes-stereo` Script for streaming raw pcm audio to a SNES (for JukeSNES payload)



## API Usage/Examples


Simple script that setups the device and pings it, wating for a response
```py
from tastm32 import TAStm32
dev = tastm32.TAStm32("/dev/ttyACM0")
dev.ping()
dev.waitForPong()
```
