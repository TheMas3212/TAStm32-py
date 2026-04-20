#!/usr/bin/env python3
import argparse
import time
import json

import serial

import tastm32.internal.serial_helper as serial_helper
import tastm32

_verbose = False
def vPrint(*args, **kwargs):
    if _verbose:
        print(*args, **kwargs)


def readUntil(dev, char):
    while True:
        try:
            c = dev.read(1)
            if c == b'':
                continue
            if c == char:
                return
        except serial.SerialException:
            print('ERROR: Serial Exception caught!')
            raise
        except KeyboardInterrupt:
            print('^C Exiting')
            raise

def readByte(dev):
    while True:
        try:
            c = dev.read(1)
            if c == b'':
                continue
            return c
        except serial.SerialException:
            print('ERROR: Serial Exception caught!')
            raise
        except KeyboardInterrupt:
            print('^C Exiting')
            raise

def readBytes(dev, size):
    chunks = []
    remaining = size
    while True:
        try:
            c = dev.read(1)
            if c == b'':
                continue
            remaining -= 1
            numBytes = dev.ser.inWaiting()
            if numBytes > 0:
                c += dev.read(min(numBytes, remaining))
                remaining -= min(numBytes, remaining)
            chunks.append(c)
            if remaining == 0:
                return b"".join(chunks)
        except serial.SerialException:
            print('ERROR: Serial Exception caught!')
            raise
        except KeyboardInterrupt:
            print('^C Exiting')
            raise

def readVarInt(dev):
    value = 0
    byte = 0
    while True:
        cb = readByte(dev)[0]
        value |= ( (cb & 0x7f) << (7*byte) )
        if cb & 0x80:
            byte += 1
            continue
        return value

def readVarArray(dev):
    arraysize = readVarInt(dev)
    vPrint(f"--- array size: {arraysize}")
    items = []
    chunkremainder = b''
    while True:
        chunk = b''
        if arraysize > 1024:
            arraysize -= 1024
            chunk = readBytes(dev, 1024)
        else:
            chunk = readBytes(dev, arraysize)
            arraysize = 0
        splitchunks = (chunkremainder+chunk).split(b'\x00')
        chunkremainder = splitchunks.pop()
        for item in splitchunks:
            items.append(item.decode('utf8'))
        if arraysize == 0:
            return items

def main():
    global _verbose
    parser = argparse.ArgumentParser(description='Query a TAStm32 device for its infoblock')
    parser.add_argument('--serial', help='Preselect the serial port')
    parser.add_argument('--verbose', '-v', help='Increase verbosity', action='store_true')
    args = parser.parse_args()

    if args.serial == None:
        dev = tastm32.TAStm32(serial_helper.select_serial_port())
    else:
        dev = tastm32.TAStm32(args.serial)

    _verbose = args.verbose

    print("--- Sending command dump info block")

    dev.write(b'I')
    readUntil(dev, b'I')
    fields = readVarInt(dev)
    vPrint(f"--- fields: {fields}")
    vPrint("--- reading headers")
    headers = readVarArray(dev)
    vPrint("--- reading values")
    values = readVarArray(dev)
    fields = dict([*zip(headers, values)])
    print(json.dumps(fields, indent=2))

if __name__ == "__main__":
    main()