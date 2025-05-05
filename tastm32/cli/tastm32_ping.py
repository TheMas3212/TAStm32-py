#!/usr/bin/env python3
import serial
import time

import tastm32.internal.serial_helper as serial_helper
import tastm32.internal.argparse_helper as argparse_helper
import tastm32

def ping(dev, attempt = 0):
  if (attempt < 5):
    dev.ping()
    result = dev.waitForPong()
    if (result == 0):
        print("--- Pong Received")
    elif (result == -1):
        print("--- Ping Timeout")
        ping(dev, attempt+1)
    elif (result == -2):
        print("--- Greater than 1000 bytes read with no response")
    elif (result == -3):
        print("--- Serial Error")
    elif (result == -4):
        print("--- Keyboard Interupt")
    else:
        print("--- Unhandled Error")

def main():
    parser = argparse_helper.audio_parser()
    args = parser.parse_args()

    if args.serial == None:
        dev = tastm32.TAStm32(serial_helper.select_serial_port())
    else:
        dev = tastm32.TAStm32(args.serial)

    print("--- Sending Ping Command")
    ping(dev)

if __name__ == "__main__":
    main()
