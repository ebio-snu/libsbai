#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 tombraid@snu.ac.kr
# All right reserved.
#
import time
from libsbapi import SBAPIClient

def getremaintime(reg1, reg2):
    return struct.unpack('i', struct.pack('HH', reg1, reg2))[0]

client = SBAPIClient("access-key")

# ON
client.write_multiple_registers(504, [201, 1], 4)
time.sleep(1) # 작동 여부 확인전에 잠시 대기
reg = client.read_holding_registers(204, 2, 4)
if reg[0] == 1 and reg[1] == 201:
    print ("OPID 1번 명령으로 작동을 하고 있습니다.", reg)
else:
    print ("OPID 1번 명령으로 작동을 하지 않습니다.", reg)

# OFF
client.write_multiple_registers(504, [0, 2], 4)
time.sleep(1) # 작동 여부 확인전에 잠시 대기
reg = client.read_holding_registers(204, 2, 4)
if reg[0] == 2 and reg[1] == 0:
    print ("OPID 2번 명령으로 작동을 중지했습니다.", reg)
else:
    print ("OPID 2번 명령으로 작동을 중지하지 못했습니다.", reg)

# TIMED ON
client.write_multiple_registers(504, [201, 3, 10, 0], 4)
time.sleep(1) # 작동 여부 확인전에 잠시 대기
reg = client.read_holding_registers(204, 2, 4)
if reg[0] == 3 and reg[1] == 201:
    print ("OPID 3번 명령으로 작동을 하고 있습니다.", reg)
    while True:
        time.sleep(1) # 작동 여부 확인전에 잠시 대기
        reg = client.read_holding_registers(204, 2, 4)
        if reg[1] == 0:
            break
        print (getremaintime(reg[2], reg[3]), "초 남았습니다.")
else:
    print ("OPID 3번 명령으로 작동을 하지 않습니다.", reg)


