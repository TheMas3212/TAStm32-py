#!/usr/bin/env python3
import struct
import sys

frame_struct = struct.Struct('ss')

def read_header(data):
    return None

def read_input(data, players=[1,5]):
    frame_iter = frame_struct.iter_unpack(data)
    for frame in frame_iter:
        fd = b''
        player = 1
        for pd in frame:
            if player in players:
                fd += pd
            player += 4
        yield fd

def input_count(data, players=[1,5]):
    return len(data) / frame_struct.size
