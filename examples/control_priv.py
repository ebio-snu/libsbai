#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 tombraid@snu.ac.kr
# All right reserved.
#

import time
from libsbapi import SBAPIClient

def readcontrol(client):
    reg = client.read_holding_registers(201, 3, 4)
    print("register", reg)
    if reg[1] == 0:
        print("노드의 상태는 정상입니다.")
    else:
        print("노드의 상태는 비정상입니다.")

    if reg[2] == 1:
        print("노드는 지금 로컬제어 상태입니다. 인공지능으로 제어가 불가능합니다.")
    elif reg[2] == 2:
        print("노드는 지금 원격제어 상태입니다. 인공지능으로 제어가 가능합니다.")
    elif reg[2] == 3:
        print("노드는 지금 수동제어 상태입니다. 인공지능으로 제어가 불가능합니다.")
    else:
        print("노드는 제어권 상태를 확인할 수 없습니다.", reg[2])

    return reg

def changecontrol(client, opid, control):
    client.write_multiple_registers(501, [2, opid, control], 5)

client = SBAPIClient("access-key")
reg = readcontrol(client)
#changecontrol(client, reg[0] + 1, 1 if reg[2] == 2 else 2)
time.sleep(1)
reg = readcontrol(client)

