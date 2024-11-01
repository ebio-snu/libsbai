#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 tombraid@snu.ac.kr
# All right reserved.
#

import time
from libsbapi import SBAPIClient, STATCODE, CMDCODE, PRIVCODE

# 슬레이브 4는 구동기 노드. 슬레이브 5는 양액기 노드
slave = 5
client = SBAPIClient("Authorization Key")

def readcontrol(client, slave):
    # 슬레이브로부터 201번지에서 3개의 레지스터를 읽습니다.
    reg = client.read_holding_registers(201, 3, slave)
    if reg[0] == STATCODE.READY:
        print("노드의 상태는 정상입니다.")
    else:
        print("노드의 상태는 비정상입니다.")

    if reg[2] == PRIVCODE.LOCAL:
        print("노드는 지금 로컬제어 상태입니다. 인공지능으로 제어가 불가능합니다.")
    elif reg[2] == PRIVCODE.REMOTE:
        print("노드는 지금 원격제어 상태입니다. 인공지능으로 제어가 가능합니다.")
    elif reg[2] == PRIVCODE.MANUAL:
        print("노드는 지금 수동제어 상태입니다. 인공지능으로 제어가 불가능합니다.")
    else:
        print("노드는 제어권 상태를 확인할 수 없습니다.", reg[2])

    return reg

def changecontrol(client, opid, control, slave):
    # 슬레이브에 제어권 변경 명령을 보냅니다.
    client.write_multiple_registers(501, [CMDCODE.CHANGE_CONTROL, opid, control], slave)

reg = readcontrol(client, slave)
print ("제어권을 토글합니다.")
changecontrol(client, reg[1] + 1, PRIVCODE.LOCAL if reg[2] == PRIVCODE.REMOTE else PRIVCODE.REMOTE, slave)
time.sleep(5)
reg = readcontrol(client, slave)
