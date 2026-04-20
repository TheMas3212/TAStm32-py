#!/usr/bin/env python3
import argparse
import time

import tastm32.internal.serial_helper as serial_helper
import tastm32

def main():
    parser = argparse.ArgumentParser(description='Instruct the TAStm32 device to control the power of a connected console')
    parser.add_argument('--serial', help='Preselect the serial port')
    parser.add_argument('--relay', help='Enable Relay Mode', action='store_true')
    parser.add_argument('mode', choices=['on', 'off'], default='on')
    args = parser.parse_args()

    if args.serial == None:
        dev = tastm32.TAStm32(serial_helper.select_serial_port())
    else:
        dev = tastm32.TAStm32(args.serial)

    if args.relay:
        dev.enable_relay()

    if args.mode == 'on':
        print("--- Sending command power the console on")
        dev.power_on()

    if args.mode =='off':
        print("--- Sending command power the console off")
        dev.power_off()

    time.sleep(0.1)

if __name__ == "__main__":
    main()
