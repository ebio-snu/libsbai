#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 tombraid@snu.ac.kr
# All right reserved.
#

import struct
from libsbapi import SBAPIClient, STATCODE

def getobservation(reg1, reg2):
    return struct.unpack('f', struct.pack('HH', reg1, reg2))[0]

cli = SBAPIClient("Authorization Key")

# 2번 슬레이브 212번지부터 9개의 레지스터를 읽습니다. (일사, 풍속, 풍향)
reg = cli.read_holding_registers(212, 9, 2)
if reg is None:
    print ("정보를 읽어오는데 실패했습니다.")
else:
    print (reg)
    if reg[2] == STATCODE.READY:
        rad = getobservation(reg[0], reg[1])
        print ("일사 센서의 상태는 정상이고, 관측치는 {} 입니다.".format(rad))
    else:
        print ("일사 센서의 상태가 비정상입니다.")

    if reg[5] == STATCODE.READY:
        ws = getobservation(reg[3], reg[4])
        print ("풍속 센서의 상태는 정상이고, 관측치는 {} 입니다.".format(ws))
    else:
        print ("풍속 센서의 상태가 비정상입니다.")

    if reg[8] == STATCODE.READY:
        wd = getobservation(reg[6], reg[7])
        print ("풍향 센서의 상태는 정상이고, 관측치는 {} 입니다.".format(wd))
    else:
        print ("풍향 센서의 상태가 비정상입니다.")

# 3번 슬레이브 203번지부터 6개의 레지스터를 읽습니다. (온도, 습도)
reg = cli.read_holding_registers(203, 6, 3)
if reg is None:
    print ("정보를 읽어오는데 실패했습니다.")
else:
    print (reg)
    if reg[2] == STATCODE.READY:
        temp = getobservation(reg[0], reg[1])
        print ("온도 센서의 상태는 정상이고, 관측치는 {} 입니다.".format(temp))
    else:
        print ("온도 센서의 상태가 비정상입니다.")

    if reg[5] == STATCODE.READY:
        hum = getobservation(reg[3], reg[4])
        print ("습도 센서의 상태는 정상이고, 관측치는 {} 입니다.".format(hum))
    else:
        print ("습도 센서의 상태가 비정상입니다.")

