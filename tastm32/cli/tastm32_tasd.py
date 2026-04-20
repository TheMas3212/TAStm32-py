#!/usr/bin/env python3
import argparse
import time
import struct
import itertools

import tastm32.internal.serial_helper as serial_helper
import tastm32.internal.r08 as r08
import tastm32.internal.r16m as r16m
import tastm32.internal.m64 as m64
import tastm32.internal.dtm as dtm
import tastm32.internal.rgen as rgen
import tastm32

import tasd

def unpack_multitap(inputs, poff):
    has_p34 = sum(1 for _ in multitap_p34(inputs))
    if has_p34:
        return [x1 + x2 for (x1, x2) in zip(multitap_p12(inputs), multitap_p34(inputs))], (poff+1,poff+2,poff+3,poff+4,)
    else:
        return [x for x in multitap_p12(inputs)], (poff+1,poff+2,)

def multitap_p12(inputs):
    for latch in inputs:
        if latch[0] & 0x01:
            yield latch[1:5]

def multitap_p34(inputs):
    for latch in inputs:
        if not (latch[0] & 0x01):
            yield latch[1:5]


def main():
    parser = argparse.ArgumentParser(description='Play a tasd run on a connected TAStm32 device')
    parser.add_argument('--serial', help='Preselect the serial port')
    parser.add_argument('--blank', help='Number of blank frames to prepend to input', type=int, default=0)
    parser.add_argument('--hardreset', help='Perform a hard/slow reset before the run begins', action='store_true')
    parser.add_argument('--softreset', help='Perform a quick/fast reset before the run begins', action='store_true')
    parser.add_argument('--relayreset', help='Perform a hard/slow reset before the run begins, driving the pin using push-pull mode', action='store_true')
    parser.add_argument('--nobulk', help='Disable Bulk Transfer Mode', action='store_true')
    parser.add_argument('movie', help='Path to the movie file to play')
    args = parser.parse_args()

    if args.serial == None:
        dev = tastm32.TAStm32(serial_helper.select_serial_port())
    else:
        dev = tastm32.TAStm32(args.serial)
    dev.reset()

    try:
        with open(args.movie, 'rb') as f:
            data = f.read()
    except:
        print('ERROR: the specified file (' + args.movie + ') failed to open')
        sys.exit(0)

    transitions = []
    latchtrain = []
    ports = { 1: None, 2: None }
    inputs = { 1: [], 2: [] }
    clock_filter = 0
    latch_filter = 0
    overread = False
    blankframes = 0
    cli_blanks = args.blank

    CONSOLE_TYPE = tasd.packets.general.CONSOLE_TYPE
    PacketType = tasd.constants.PacketType
    CONTROLLER_TYPE = tasd.packets.general.CONTROLLER_TYPE

    LATCH_SIZE = {
        CONTROLLER_TYPE.NES_STANDARD_CONTROLLER: 1,
        # CONTROLLER_TYPE.NES_FOUR_SCORE: 3,
        CONTROLLER_TYPE.SNES_STANDARD_CONTROLLER: 2,
        CONTROLLER_TYPE.SNES_SUPER_MULTITAP: 5,
        CONTROLLER_TYPE.N64_STANDARD_CONTROLLER: 4,
        CONTROLLER_TYPE.GC_STANDARD_CONTROLLER: 8,
        CONTROLLER_TYPE.GENESIS_3BUTTON: 1,
    }

    tasd_run = tasd.TASD.from_bytes(data)
    for packet in tasd_run.packets:
        # General
        if packet._key == PacketType.CONSOLE_TYPE:
            if packet.console == CONSOLE_TYPE.N64:
                console = 'n64'
            if packet.console == CONSOLE_TYPE.SNES:
                console = 'snes'
            if packet.console == CONSOLE_TYPE.NES:
                console = 'nes'
            if packet.console == CONSOLE_TYPE.GC:
                console = 'gc'
            if packet.console == CONSOLE_TYPE.GENESIS:
                console = 'genesis'
        # if packet._key == CONSOLE_REGION:
            # pass
        # if packet._key == GAME_TITLE:
            # pass
        # if packet._key == ROM_NAME:
            # pass
        # if packet._key == ATTRIBUTION:
            # pass
        # if packet._key == CATEGORY:
            # pass
        # if packet._key == EMULATOR_NAME:
            # pass
        # if packet._key == EMULATOR_VERSION:
            # pass
        # if packet._key == EMULATOR_CORE:
            # pass
        # if packet._key == TAS_LAST_MODIFIED:
            # pass
        # if packet._key == DUMP_CREATED:
            # pass
        # if packet._key == DUMP_LAST_MODIFIED:
            # pass
        # if packet._key == TOTAL_FRAMES:
            # pass
        # if packet._key == RERECORDS:
            # pass
        # if packet._key == SOURCE_LINK:
            # pass
        if packet._key == PacketType.BLANK_FRAMES:
            blankframes = packet.frames
        # if packet._key == VERIFIED:
            # pass
        # if packet._key == MEMORY_INIT:
            # pass
        # if packet._key == GAME_IDENTIFIER:
            # pass
        # if packet._key == MOVIE_LICENSE:
            # pass
        # if packet._key == MOVIE_FILE:
            # pass
        if packet._key == PacketType.PORT_CONTROLLER:
            if ports[packet.port] != None:
                print('ERROR: This script does not support switching port type! Exiting.')
                sys.exit(0)
            ports[packet.port] = packet.type
        if packet._key == PacketType.PORT_OVERREAD:
            overread = packet.high

        # NES
        if packet._key == PacketType.NES_LATCH_FILTER:
            latch_filter = packet.time
        if packet._key == PacketType.NES_CLOCK_FILTER:
            clock_filter = int(packet.time / 2.5)

        # SNES
        if packet._key == PacketType.SNES_LATCH_FILTER:
            latch_filter = packet.time
        if packet._key == PacketType.SNES_CLOCK_FILTER:
            clock_filter = int(packet.time / 2.5)
        # if packet._key == SNES_GAME_GENIE_CODE:
        #     pass
        if packet._key == PacketType.SNES_LATCH_TRAIN:
            for train in packet.trains:
                latchtrain.append(train)

        # GENESIS
        # if packet._key == GENESIS_GAME_GENIE_CODE:
        #     pass

        # INPUT
        if packet._key == PacketType.INPUT_CHUNK:
            latches = []
            latchsize = LATCH_SIZE[ports[packet.port]]
            for index in range(0, len(packet.data), latchsize):
                latches.append(packet.data[index:index+latchsize])
            inputs[packet.port].extend(latches)
        # if packet._key == INPUT_MOMENT:
        #     pass
        # if packet._key == TRANSITION:
        #     pass
        # if packet._key == LAG_FRAME_CHUNK:
        #     pass
        # if packet._key == MOVIE_TRANSITION:
        #     pass
        #     if args.transition != None:
        #         for transition in args.transition:
        #             transition[0] = int(transition[0])
        #             if transition[1] == 'A':
        #                 transition[1] = b'A'
        #             elif transition[1] == 'N':
        #                 transition[1] = b'N'
        #             elif transition[1] == 'S':
        #                 transition[1] = b'S'
        #             elif transition[1] == 'H':
        #                 transition[1] = b'H'
        #             elif transition[1] == 'R':
        #                 transition[1] = b'R'

        # EXTRA
        # if packet._key == COMMENT:
        #     pass
        # if packet._key == EXPERIMENTAL:
        #     pass
        # if packet._key == UNSPECIFIED:
        #     pass

        if packet._key == PacketType.INPUT_CHUNK:
            continue
        if packet._key == PacketType.INPUT_MOMENT:
            continue
        if packet._key == PacketType.UNSPECIFIED:
            continue
        if packet._key == PacketType.MOVIE_FILE:
            print(tasd.packets.general.MovieFile(name=packet.name, data=b""))
            continue

        print(packet)

    print(len(inputs[1]), len(inputs[2]))

    oldinputs = { 1: inputs[1], 2: inputs[2] }

    players = []
    if ports[1] != None:
        if ports[1] == CONTROLLER_TYPE.SNES_SUPER_MULTITAP:
            unpacked, pcount = unpack_multitap(inputs[1], 0)
            players.extend(pcount)
            inputs[1] = unpacked
        else:
            players.extend([1])

    if ports[2] != None:
        if ports[2] == CONTROLLER_TYPE.SNES_SUPER_MULTITAP:
            unpacked, pcount = unpack_multitap(inputs[2], 4)
            players.extend(pcount)
            inputs[2] = unpacked
        else:
            players.extend([5])

    print('players', players)

    if clock_filter < 0 or clock_filter > 63:
        print('ERROR: The clock value must be in the range [0,63]! Exiting.')
        sys.exit(0)

    if args.relayreset:
        dev.enable_relay()

    if args.hardreset or args.softreset or args.relayreset:
        dev.power_off()
        if args.hardreset or args.relayreset:
            time.sleep(2.0)

    run_id = dev.setup_run(console, players, latch_filter > 0, overread, clock_filter)
    if run_id == None:
        raise RuntimeError('ERROR')
        sys.exit()
    if console == 'n64':
        # buffer = m64.read_input(data, players)
        blankframe = b'\x00\x00\x00\x00' * len(players)
    elif console == 'snes':
        # buffer = r16m.read_input(data, players)
        blankframe = b'\x00\x00' * len(players)
    elif console == 'nes':
        # buffer = r08.read_input(data, players)
        blankframe = b'\x00' * len(players)
    elif console == 'gc':
        # buffer = dtm.read_input(data)
        blankframe = b'\x00\x00\x00\x00\x00\x00\x00\x00' * len(players)
    elif console == 'genesis':
        # buffer = rgen.read_input(data, players)
        blankframe = b'\x00\x00' * len(players)

    # Transitions
    if len(transitions) > 0:
        for transition in transitions:
            dev.send_transition(run_id, *transition)

    # Latch trains
    if len(latchtrain) > 0:
        dev.send_latchtrain(run_id, latchtrain)

    def frame_generator(break_at_end = False):
        for blank in range(cli_blanks):
            yield blankframe
        for blank in range(blankframes):
            yield blankframe
        for latch in range(len(inputs[1])):
            if ports[2] == None:
                yield bytes(x ^ 0xff for x in inputs[1][latch])
            else:
                yield bytes(x ^ 0xff for x in inputs[1][latch] + inputs[2][latch])
        while not break_at_end:
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
    if args.hardreset or args.softreset or args.relayreset:
        dev.power_on()
    dev.main_loop(run_id, blankframe, frame_gen, len(inputs[1]))
    print('Exiting')

if __name__ == "__main__":
    main()