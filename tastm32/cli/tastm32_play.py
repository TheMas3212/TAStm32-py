#!/usr/bin/env python3
import argparse
import time

import tastm32.internal.serial_helper as serial_helper
import tastm32.internal.r08 as r08
import tastm32.internal.r16m as r16m
import tastm32.internal.m64 as m64
import tastm32.internal.dtm as dtm
import tastm32.internal.rgen as rgen
import tastm32

def main():
    parser = argparse.ArgumentParser(description='Play a run on a connected TAStm32 device')
    parser.add_argument('--serial', help='Preselect the serial port')
    parser.add_argument('--blank', help='Number of blank frames to prepend to input', type=int, default=0)
    parser.add_argument('--console', help='Set the console', choices=['n64', 'snes', 'nes', 'gc', 'genesis'], required=True)
    parser.add_argument('--players', help='Comma seperated list of players', default='1')
    parser.add_argument('--dpcm', help='Enable dpcm fix', action='store_true')
    parser.add_argument('--hardreset', help='Perform a hard/slow reset before the run begins', action='store_true')
    parser.add_argument('--softreset', help='Perform a quick/fast reset before the run begins', action='store_true')
    parser.add_argument('--relayreset', help='Perform a hard/slow reset before the run begins, driving the pin using push-pull mode', action='store_true')
    parser.add_argument('--controller', help='Disables the input buffer, ideal for behaving as a controller adapter', action='store_true')
    parser.add_argument('--clock', help='Enable clock filter. Value must be between 0 and 63. This number gets multiplied by 0.25us')
    parser.add_argument('--overread', help='Set overread value', action='store_true')
    parser.add_argument('--transition', help='Add a transition', nargs=2, action='append')
    parser.add_argument('--latchtrain', help='Configure latch train', default='')
    parser.add_argument('--nobulk', help='Disable Bulk Transfer Mode', action='store_true')
    parser.add_argument('--melee', help='Enable Super Smash Bros. Melee poll bug mitigation', action='store_true')
    parser.add_argument('movie', help='Path to the movie file to play')
    args = parser.parse_args()

    if args.transition != None:
        for transition in args.transition:
            transition[0] = int(transition[0])
            if transition[1] == 'A':
                transition[1] = b'A'
            elif transition[1] == 'N':
                transition[1] = b'N'
            elif transition[1] == 'S':
                transition[1] = b'S'
            elif transition[1] == 'H':
                transition[1] = b'H'
            elif transition[1] == 'R':
                transition[1] = b'R'

    if args.latchtrain != '':
        args.latchtrain = [int(x) for x in args.latchtrain.split(',')]

    args.players = args.players.split(',')
    for x in range(len(args.players)):
        args.players[x] = int(args.players[x])

    if args.serial == None:
        dev = tastm32.TAStm32(serial_helper.select_serial_port())
    else:
        dev = tastm32.TAStm32(args.serial)

    if args.clock != None:
        args.clock = int(args.clock)
        if args.clock < 0 or args.clock > 63:
            print('ERROR: The clock value must be in the range [0,63]! Exiting.')
            sys.exit(0)

    try:
        with open(args.movie, 'rb') as f:
            data = f.read()
    except:
        print('ERROR: the specified file (' + args.movie + ') failed to open')
        sys.exit(0)

    dev.reset()
    
    if args.relayreset:
        dev.enable_relay()
        
    if args.controller:
        dev.enable_controller()
    
    if args.hardreset or args.softreset or args.relayreset:
        dev.power_off()
        if args.hardreset or args.relayreset:
            time.sleep(2.0)
            
    run_id = dev.setup_run(args.console, args.players, args.dpcm, args.overread, args.clock)
    if run_id == None:
        raise RuntimeError('ERROR')
        sys.exit()
    if args.console == 'n64':
        buffer = m64.read_input(data, args.players)
        blankframe = b'\x00\x00\x00\x00' * len(args.players)
    elif args.console == 'snes':
        buffer = r16m.read_input(data, args.players)
        blankframe = b'\x00\x00' * len(args.players)
    elif args.console == 'nes':
        buffer = r08.read_input(data, args.players)
        blankframe = b'\x00' * len(args.players)
    elif args.console == 'gc':
        buffer = dtm.read_input(data)
        blankframe = b'\x00\x00\x00\x00\x00\x00\x00\x00' * len(args.players)
    elif args.console == 'genesis':
        buffer = rgen.read_input(data, args.players)
        blankframe = b'\x00\x00' * len(args.players)

    if args.melee:
        dev.write(b'M')

    # Transitions
    if args.transition != None:
        for transition in args.transition:
            dev.send_transition(run_id, *transition)

    # Latch trains
    if args.latchtrain != '':
        dev.send_latchtrain(run_id, args.latchtrain)

    def frame_generator():
        for blank in range(args.blank):
            yield blankframe
        for latch in range(len(buffer)):
            yield buffer[latch]
        while True:
            yield blankframe

    frame_gen = frame_generator()

    for latch in range(tastm32.int_buffer):
        dev.write(run_id + next(frame_gen))
    err = dev.read(tastm32.int_buffer)
    if err.count(b'\xB0') != 0:
        print('Buffer Overflow x{}'.format(err.count(b'\xB0')))


    print('Main Loop Start')
    if not args.nobulk:
        dev.set_bulk_data_mode(run_id, b"1")
    dev.power_on()
    dev.main_loop(run_id, blankframe, frame_gen, len(buffer))
    print('Exiting')

if __name__ == "__main__":
    main()