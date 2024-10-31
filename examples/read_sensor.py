#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 tombraid@snu.ac.kr
# All right reserved.
#

import struct
from libsbapi import SBAPIClient

def getobservation(reg1, reg2):
    return struct.unpack('f', struct.pack('HH', reg1, reg2))

cli = SBAPIClient("access-key")
reg = cli.read_holding_registers(203, 6, 3)
temp = getobservation(reg[0], reg[1])
hum = getobservation(reg[3], reg[4])
print (temp, hum)

