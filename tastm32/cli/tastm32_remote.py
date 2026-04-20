#!/usr/bin/env python3
import argparse
import sys
import time
import os
import gc
import struct

import psutil

import tastm32.internal.serial_helper as serial_helper
import tastm32


bmap = {
  "u": b"A\x08\x00A\x00\x00",
  "d": b"A\x04\x00A\x00\x00",
  "l": b"A\x02\x00A\x00\x00",
  "r": b"A\x01\x00A\x00\x00",
  "a": b"A\x00\x80A\x00\x00",
  "b": b"A\x80\x00A\x00\x00",
  "x": b"A\x00\x40A\x00\x00",
  "y": b"A\x40\x00A\x00\x00",
  "s": b"A\x20\x00A\x00\x00",
  "S": b"A\x10\x00A\x00\x00",
  "L": b"A\x00\x20A\x00\x00",
  "R": b"A\x00\x10A\x00\x00"
}

int_to_byte_struct = struct.Struct('B')
def int_to_byte(interger):
    return int_to_byte_struct.pack(interger)


def main():
    if os.name == 'nt':
        psutil.Process().nice(psutil.REALTIME_PRIORITY_CLASS)
    else:
        psutil.Process().nice(20)

    gc.disable()

    parser = argparse.ArgumentParser(description='Manually control a controller via the TAStm32 device')
    parser.add_argument('--serial', help='Preselect the serial port')
    args = parser.parse_args()

    if args.serial == None:
        dev = tastm32.TAStm32(serial_helper.select_serial_port())
    else:
        dev = tastm32.TAStm32(args.serial)

    dev.write(b'R')
    time.sleep(0.1)
    cmd = dev.read(2)
    print(bytes(cmd))

    # set up the SNES correctly
    dev.write(b'SAS\x80\x00')
    time.sleep(0.1)
    cmd = dev.read(2)
    print(bytes(cmd))

    dev.write(b'QA0')
    time.sleep(0.1)

    dev.ser.reset_input_buffer()

    dev.write(bytes([65,0,0]))

    while True:
        line = input()
        if line in bmap:
            dev.write(bmap[line])
        else:
            try:
                dev.write(b"A" + int_to_byte(int(line[0:2], 16)) + int_to_byte(int(line[2:4], 16)))
            except:
                pass

if __name__ == "__main__":
    main()
