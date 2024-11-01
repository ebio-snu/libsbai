#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 tombraid@snu.ac.kr
# All right reserved.
#

class CMDCODE:
    OFF = 0
    CHANGE_CONTROL = 2

    ON = 201
    TIMED_ON = 202

    OPEN = 301
    CLOSE = 302
    TIMED_OPEN = 303
    TIMED_CLOSE = 304

    ONCE_WATER = 401        # 대회를 위해서 적절한 명령이 아니라 사용을 권장하지 않습니다.
    JUST_WATER = 402
    NUT_WATER = 403

class STATCODE:
    READY = 0      # STOPPED
    ERROR = 1

    WORKING = 201

    OPENING = 301      
    CLOSING = 302  

    PREPARING = 401
    SUPPLYING = 402
    FINISHING = 403

class PRIVCODE:
    LOCAL = 1
    REMOTE = 2
    MANULAL = 3
