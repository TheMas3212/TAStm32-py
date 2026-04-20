#!/usr/bin/env python3
import argparse
import time

import tastm32.internal.serial_helper as serial_helper
import tastm32

def main():
    parser = argparse.ArgumentParser(description='Reset the configuration of a connected TAStm32 device')
    parser.add_argument('--serial', help='Preselect the serial port')
    args = parser.parse_args()

    if args.serial == None:
        dev = tastm32.TAStm32(serial_helper.select_serial_port())
    else:
        dev = tastm32.TAStm32(args.serial)

    print("--- Sending command to reset TAStm32 device")

    dev.reset()
    time.sleep(0.1)

if __name__ == "__main__":
    main()