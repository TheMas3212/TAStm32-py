#!/usr/bin/env python3
import argparse
import time

import tastm32.internal.serial_helper as serial_helper
import tastm32

def main():
    parser = argparse.ArgumentParser(description='Instruct a TAStm32 device to jump to DFU mode')
    parser.add_argument('--serial', help='Preselect the serial port')
    args = parser.parse_args()

    if args.serial == None:
        dev = tastm32.TAStm32(serial_helper.select_serial_port())
    else:
        dev = tastm32.TAStm32(args.serial)

    print("--- Sending command to jump to DFU mode")

    dev.write(b'\xDF')
    time.sleep(0.1)

if __name__ == "__main__":
    main()