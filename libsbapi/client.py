#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 tombraid@snu.ac.kr
# All right reserved.
#

""" SmartBerry AI Client """

import logging
import random
import json
import requests
import struct
from binascii import hexlify
from dataclasses import dataclass, field
from typing import Dict

from .constants import (ENCAPSULATED_INTERFACE_TRANSPORT, EXP_DETAILS,
                        EXP_NONE, EXP_TXT, MB_CONNECT_ERR, MB_ERR_TXT,
                        MB_EXCEPT_ERR, MB_NO_ERR, MB_RECV_ERR, MB_SEND_ERR,
                        MB_SOCK_CLOSE_ERR, MB_TIMEOUT_ERR,
                        MEI_TYPE_READ_DEVICE_ID, READ_COILS,
                        READ_DISCRETE_INPUTS, READ_HOLDING_REGISTERS,
                        READ_INPUT_REGISTERS, VERSION, WRITE_MULTIPLE_COILS,
                        WRITE_MULTIPLE_REGISTERS,
                        WRITE_READ_MULTIPLE_REGISTERS, WRITE_SINGLE_COIL,
                        WRITE_SINGLE_REGISTER)
from .utils import byte_length, set_bit, valid_host

# add a logger 
logger = logging.getLogger(__name__)

class SBAPIClient:
    """Smart Berry API client."""

    class _InternalError(Exception):
        pass

    class _NetworkError(_InternalError):
        def __init__(self, code, message):
            self.code = code
            self.message = message

    class _ModbusExcept(_InternalError):
        def __init__(self, code):
            self.code = code

    def __init__(self, key, header=True, host='121.134.228.36', port=9900, timeout=30.0):
        """Constructor.

        :param host: hostname or IPv4/IPv6 address server address
        :type host: str
        :param port: TCP port number
        :type port: int
        :param timeout: socket timeout in seconds
        :type timeout: float
        :return: Object SBAPIClient
        :rtype: SBAPIClient
        """
        # private
        # internal variables
        self._key = key
        self._header = header
        self._host = None
        self._port = None
        self._timeout = None
        self._transaction_id = 0  # MBAP transaction ID
        self._version = VERSION  # this package version number
        self._last_error = MB_NO_ERR  # last error code
        self._last_except = EXP_NONE  # last except code
        self._recved = None
        self._isread = True
        # public
        # constructor arguments: validate them with property setters
        self.host = host
        self.port = port
        self.unit_id = 2
        self.timeout = timeout

    def __repr__(self):
        r_str = 'SBAPIClient(key=\'%s\', host=\'%s\', port=%d, unit_id=%d, timeout=%.2f)'
        r_str %= (self._key, self.host, self.port, self.unit_id, self.timeout)
        return r_str

    def __del__(self):
        self.close()

    @property
    def version(self):
        """Return the current package version as a str."""
        return self._version

    @property
    def last_error(self):
        """Last error code."""
        return self._last_error

    @property
    def last_error_as_txt(self):
        """Human-readable text that describe last error."""
        return MB_ERR_TXT.get(self._last_error, 'unknown error')

    @property
    def last_except(self):
        """Return the last modbus exception code."""
        return self._last_except

    @property
    def last_except_as_txt(self):
        """Short human-readable text that describe last modbus exception."""
        default_str = 'unreferenced exception 0x%X' % self._last_except
        return EXP_TXT.get(self._last_except, default_str)

    @property
    def last_except_as_full_txt(self):
        """Verbose human-readable text that describe last modbus exception."""
        default_str = 'unreferenced exception 0x%X' % self._last_except
        return EXP_DETAILS.get(self._last_except, default_str)

    @property
    def host(self):
        """Get or set the server to connect to.

        This can be any string with a valid IPv4 / IPv6 address or hostname.
        Setting host to a new value will close the current socket.
        """
        return self._host

    @host.setter
    def host(self, value):
        # check type
        if type(value) is not str:
            raise TypeError('host must be a str')
        # check value
        if valid_host(value):
            if self._host != value:
                self.close()
                self._host = value
            return
        # can't be set
        raise ValueError('host can\'t be set (not a valid IP address or hostname)')

    @property
    def port(self):
        """Get or set the current TCP port (default is 502).

        Setting port to a new value will close the current socket.
        """
        return self._port

    @port.setter
    def port(self, value):
        # check type
        if type(value) is not int:
            raise TypeError('port must be an int')
        # check validity
        if 0 < value < 65536:
            if self._port != value:
                self.close()
                self._port = value
            return
        # can't be set
        raise ValueError('port can\'t be set (valid if 0 < port < 65536)')

    @property
    def timeout(self):
        """Get or set requests timeout (default is 30 seconds).

        The argument may be a floating point number for sub-second precision.
        Setting timeout to a new value will close the current socket.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        # enforce type
        value = float(value)
        # check validity
        if 0 < value < 3600:
            if self._timeout != value:
                self.close()
                self._timeout = value
            return
        # can't be set
        raise ValueError('timeout can\'t be set (valid between 0 and 3600)')

    def open(self):
        return True

    def close(self):
        return True

    def custom_request(self, pdu):
        """Send a custom modbus request.

        :param pdu: a modbus PDU (protocol data unit)
        :type pdu: bytes
        :returns: modbus frame PDU or None if error
        :rtype: bytes or None
        """
        # make request
        try:
            return self._req_pdu(pdu)
        # handle errors during request
        except SBAPIClient._InternalError as e:
            self._req_except_handler(e)
            return None

    def read_holding_registers(self, reg_addr, reg_nb, unit_id):
        """Modbus function READ_HOLDING_REGISTERS (0x03).

        :param reg_addr: register address (0 to 65535)
        :type reg_addr: int
        :param reg_nb: number of registers to read (1 to 125)
        :type reg_nb: int
        :returns: registers list or None if fail
        :rtype: list of int or None
        """
        # check params
        if not 0 <= int(reg_addr) <= 0xffff:
            raise ValueError('reg_addr out of range (valid from 0 to 65535)')
        if not 1 <= int(reg_nb) <= 125:
            raise ValueError('reg_nb out of range (valid from 1 to 125)')
        if int(reg_addr) + int(reg_nb) > 0x10000:
            raise ValueError('read after end of modbus address space')
        # make request
        try:
            self._isread = True
            self.unit_id = unit_id
            tx_pdu = struct.pack('>BHH', READ_HOLDING_REGISTERS, reg_addr, reg_nb)
            rx_pdu = self._req_pdu(tx_pdu=tx_pdu, rx_min_len=3)
            # extract field "byte count"
            byte_count = rx_pdu[1]
            # frame with regs value
            f_regs = rx_pdu[2:]
            # check rx_byte_count: buffer size must be consistent and have at least the requested number of registers
            if byte_count < 2 * reg_nb or byte_count != len(f_regs):
                raise SBAPIClient._NetworkError(MB_RECV_ERR, 'rx byte count mismatch')
            # allocate a reg_nb size list
            registers = [0] * reg_nb
            # fill registers list with register items
            for i in range(reg_nb):
                registers[i] = struct.unpack('>H', f_regs[i * 2:i * 2 + 2])[0]
            # return registers list
            return registers
        # handle error during request
        except SBAPIClient._InternalError as e:
            self._req_except_handler(e)
            return None

    def write_multiple_registers(self, regs_addr, regs_value, unit_id):
        """Modbus function WRITE_MULTIPLE_REGISTERS (0x10).

        :param regs_addr: registers address (0 to 65535)
        :type regs_addr: int
        :param regs_value: registers values to write
        :type regs_value: list
        :returns: True if write ok
        :rtype: bool
        """
        # check params
        if not 0 <= int(regs_addr) <= 0xffff:
            raise ValueError('regs_addr out of range (valid from 0 to 65535)')
        if not 1 <= len(regs_value) <= 123:
            raise ValueError('number of registers out of range (valid from 1 to 123)')
        if int(regs_addr) + len(regs_value) > 0x10000:
            raise ValueError('write after end of modbus address space')
        # make request
        try:
            self._isread = False
            self.unit_id = unit_id
            # init PDU registers part
            pdu_regs_part = b''
            # populate it with register values
            for reg in regs_value:
                # check current register value
                if not 0 <= int(reg) <= 0xffff:
                    raise ValueError('regs_value list contains out of range values')
                # pack register for build frame
                pdu_regs_part += struct.pack('>H', reg)
            bytes_nb = len(pdu_regs_part)
            # concatenate PDU parts
            tx_pdu = struct.pack('>BHHB', WRITE_MULTIPLE_REGISTERS, regs_addr, len(regs_value), bytes_nb)
            tx_pdu += pdu_regs_part
            # make a request
            rx_pdu = self._req_pdu(tx_pdu=tx_pdu, rx_min_len=5)
            # response decode
            resp_write_addr, resp_write_count = struct.unpack('>HH', rx_pdu[1:5])
            # check response fields
            write_ok = resp_write_addr == regs_addr and resp_write_count == len(regs_value)
            return write_ok
        # handle error during request
        except SBAPIClient._InternalError as e:
            self._req_except_handler(e)
            return False

    def write_read_multiple_registers(self, write_addr, write_values, read_addr, read_nb=1):
        """Modbus function WRITE_READ_MULTIPLE_REGISTERS (0x17).

        :param write_addr: write registers address (0 to 65535)
        :type write_addr: int
        :param write_values: registers values to write
        :type write_values: list
        :param read_addr: read register address (0 to 65535)
        :type read_addr: int
        :param read_nb: number of registers to read (1 to 125)
        :type read_nb: int
        :returns: registers list or None if fail
        :rtype: list of int or None
        """
        # check params
        check_l = [(not 0 <= int(write_addr) <= 0xffff, 'write_addr out of range (valid from 0 to 65535)'),
                   (not 1 <= len(write_values) <= 121, 'number of registers out of range (valid from 1 to 121)'),
                   (int(write_addr) + len(write_values) > 0x10000, 'write after end of modbus address space'),
                   (not 0 <= int(read_addr) <= 0xffff, 'read_addr out of range (valid from 0 to 65535)'),
                   (not 1 <= int(read_nb) <= 125, 'read_nb out of range (valid from 1 to 125)'),
                   (int(read_addr) + int(read_nb) > 0x10000, 'read after end of modbus address space'), ]
        for err, msg in check_l:
            if err:
                raise ValueError(msg)
        # make request
        try:
            # init PDU registers part
            pdu_regs_part = b''
            # populate it with register values
            for reg in write_values:
                # check current register value
                if not 0 <= int(reg) <= 0xffff:
                    raise ValueError('write_values list contains out of range values')
                # pack register for build frame
                pdu_regs_part += struct.pack('>H', reg)
            bytes_nb = len(pdu_regs_part)
            # concatenate PDU parts
            tx_pdu = struct.pack('>BHHHHB', WRITE_READ_MULTIPLE_REGISTERS, read_addr, read_nb,
                                 write_addr, len(write_values), bytes_nb)
            tx_pdu += pdu_regs_part
            # make a request
            rx_pdu = self._req_pdu(tx_pdu=tx_pdu, rx_min_len=4)
            # response decode
            # extract field "byte count"
            byte_count = rx_pdu[1]
            # frame with regs value
            f_regs = rx_pdu[2:]
            # check rx_byte_count: buffer size must be consistent and have at least the requested number of registers
            if byte_count < 2 * read_nb or byte_count != len(f_regs):
                raise SBAPIClient._NetworkError(MB_RECV_ERR, 'rx byte count mismatch')
            # allocate a reg_nb size list
            registers = [0] * read_nb
            # fill registers list with register items
            for i in range(read_nb):
                registers[i] = struct.unpack('>H', f_regs[i * 2:i * 2 + 2])[0]
            # return registers list
            return registers
        # handle error during request
        except SBAPIClient._InternalError as e:
            self._req_except_handler(e)
            return

    def _send(self, frame):
        """Send frame over API.
        :param frame: modbus frame to send (MBAP + PDU)
        :type frame: bytes
        """
        # send
        try:
            self._recved = None
            url = "http://" + self._host + ":" + str(self._port) + "/" + ("read" if self._isread else "write")
            params = {"command": frame.hex()}
            headers = {"Authorization": self._key, "Content-Type": "application/json"}
            print(params)
            x = requests.post(url, headers=headers, json=params)
            print(x.text)
            tmp = x.json()
            if tmp["result"] is True:
                self._recved = bytes.fromhex(tmp["response"])
            else:
                raise SBAPIClient._NetworkError(MB_SEND_ERR, 'send error')
        except Exception as ex: 
            raise SBAPIClient._NetworkError(MB_SEND_ERR, str(ex))

    def _send_pdu(self, pdu):
        """Convert modbus PDU to frame and send it.

        :param pdu: modbus frame PDU
        :type pdu: bytes
        """
        # add MBAP header to PDU
        if self._header:
            #"""
            tx_frame = self._add_mbap(pdu)
            # send frame with error check
            self._send(tx_frame)
            # debug
            self._on_tx_rx(frame=tx_frame, is_tx=True)
            #"""
        else:
            self._send(pdu)

    def _recv(self, size):
        """Receive data over current socket.

        :param size: number of bytes to receive
        :type size: int
        :returns: receive data or None if error
        :rtype: bytes
        """
        if self._recved is None:
            raise SBAPIClient._NetworkError(MB_RECV_ERR, 'recv error')
        elif len(self._recved) < size:
            raise SBAPIClient._NetworkError(MB_RECV_ERR, 'recv error')
        else:
            ret = self._recved[:size]
            self._recved = self._recved[size:]
            return ret
            #r_buffer = b''

    def _recv_all(self, size):
        return self._recv(size)

    def _recv_pdu(self, min_len=2):
        """Receive the modbus PDU (Protocol Data Unit).

        :param min_len: minimal length of the PDU
        :type min_len: int
        :returns: modbus frame PDU or None if error
        :rtype: bytes or None
        """
        # receive 7 bytes header (MBAP)
        rx_mbap = self._recv_all(7)
        # decode MBAP
        (f_transaction_id, f_protocol_id, f_length, f_unit_id) = struct.unpack('>HHHB', rx_mbap)
        # check MBAP fields
        f_transaction_err = f_transaction_id != self._transaction_id
        f_transaction_err = False       # check 전송되는것과 돌아오는 것이 다름.
        f_protocol_err = f_protocol_id != 0
        f_length_err = f_length >= 256
        f_unit_id_err = f_unit_id != self.unit_id
        print (f_transaction_id, self._transaction_id, f_protocol_id, f_length, f_unit_id)        # check
        # checking error status of fields
        if f_transaction_err or f_protocol_err or f_length_err or f_unit_id_err:
            self.close()
            self._on_tx_rx(frame=rx_mbap, is_tx=False)
            raise SBAPIClient._NetworkError(MB_RECV_ERR, 'MBAP checking error')
        # recv PDU
        rx_pdu = self._recv_all(f_length - 1)
        # dump frame
        self._on_tx_rx(frame=rx_mbap + rx_pdu, is_tx=False)
        # body decode
        # check PDU length for global minimal frame (an except frame: func code + exp code)
        if len(rx_pdu) < 2:
            raise SBAPIClient._NetworkError(MB_RECV_ERR, 'PDU length is too short')
        # extract function code
        rx_fc = rx_pdu[0]
        # check except status
        if rx_fc >= 0x80:
            exp_code = rx_pdu[1]
            raise SBAPIClient._ModbusExcept(exp_code)
        # check PDU length for specific request set in min_len (keep this after except checking)
        if len(rx_pdu) < min_len:
            raise SBAPIClient._NetworkError(MB_RECV_ERR, 'PDU length is too short for current request')
        # if no error, return PDU
        return rx_pdu

    def _add_mbap(self, pdu):
        """Return full modbus frame with MBAP (modbus application protocol header) append to PDU.

        :param pdu: modbus PDU (protocol data unit)
        :type pdu: bytes
        :returns: full modbus frame
        :rtype: bytes
        """
        # build MBAP
        self._transaction_id = random.randint(0, 65535)
        protocol_id = 0
        length = len(pdu) + 1
        mbap = struct.pack('>HHHB', self._transaction_id, protocol_id, length, self.unit_id)
        # full modbus/TCP frame = [MBAP]PDU
        return mbap + pdu

    def _req_pdu(self, tx_pdu, rx_min_len=2):
        """Request processing (send and recv PDU).

        :param tx_pdu: modbus PDU (protocol data unit) to send
        :type tx_pdu: bytes
        :param rx_min_len: min length of receive PDU
        :type rx_min_len: int
        :returns: the receive PDU or None if error
        :rtype: bytes
        """
        # init request engine
        self._req_init()
        # send PDU
        self._send_pdu(tx_pdu)
        # return receive PDU
        return self._recv_pdu(min_len=rx_min_len)

    def _req_init(self):
        """Reset request status flags."""
        self._last_error = MB_NO_ERR
        self._last_except = EXP_NONE

    def _req_except_handler(self, _except):
        """Global handler for internal exceptions."""
        # on request network error
        if isinstance(_except, SBAPIClient._NetworkError):
            self._last_error = _except.code
            self._debug_msg(_except.message)
        # on request modbus except
        if isinstance(_except, SBAPIClient._ModbusExcept):
            self._last_error = MB_EXCEPT_ERR
            self._last_except = _except.code
            self._debug_msg(f'modbus exception (code {self.last_except} "{self.last_error_as_txt}")')

    def _debug_msg(self, msg: str):
        logger.debug(f'({self.host}:{self.port}:{self.unit_id}) {msg}')

    def _on_tx_rx(self, frame: bytes, is_tx: bool):
        # format a log message
        if logger.isEnabledFor(logging.DEBUG):
            type_s = 'Tx' if is_tx else 'Rx'
            mbap_s = hexlify(frame[0:7], sep=' ').upper().decode()
            pdu_s = hexlify(frame[7:], sep=' ').upper().decode()
            self._debug_msg(f'{type_s} [{mbap_s}] {pdu_s}')
        # notify user
        self.on_tx_rx(frame=frame, is_tx=is_tx)

    def on_tx_rx(self, frame: bytes, is_tx: bool):
        """Call for each Tx/Rx (for user purposes)."""
        pass

if __name__ == "__main__":
    client = SBAPIClient("access-key")
    reg = client.read_holding_registers(203, 6, 3)
    print(reg)
