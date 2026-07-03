#!/usr/bin/env python3
import struct
import sys

frame_struct = struct.Struct('2s2s2s2s2s2s2s2s')

def read_header(data):
    return None

def read_input(data, players=[1,2,3,4,5,6,7,8]):
    frame_iter = frame_struct.iter_unpack(data)
    for frame in frame_iter:
        fd = b''
        player = 1
        for pd in frame:
            if player in players:
                fd += pd
            player += 1
        yield fd

def input_count(data, players=[1,5]):
    return len(data) / frame_struct.size
