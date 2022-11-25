"""
Romote Connection

Part of code borrowed from RV-2022: term.py
"""

import re
import socket
import sys
from typing import Union
import time
from utils import *
import os
import os.path as osp

CHAR_INTERVAL = 0.1

def to_host_port(host_port: str):
    ValidIpAddressRegex = re.compile(
        "^((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])):(\d+)$")
    ValidHostnameRegex = re.compile(
        "^((([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])):(\d+)$")

    if ValidIpAddressRegex.search(host_port) is None and \
            ValidHostnameRegex.search(host_port) is None:
        return False

    match = ValidIpAddressRegex.search(host_port) or ValidHostnameRegex.search(host_port)
    groups = match.groups()
    return groups[0], int(groups[4])

class Terminal:
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        print("Socket connected to %s:%d" % (host, port))

    def read(self, encoding='utf-8') -> bytes:
        while True:
            rec = self.sock.recv(1)
            yield rec

    def write(self, stream: Union[str, bytes], encoding='utf-8') -> None:
        if isinstance(stream, str):
            stream = stream.encode(encoding)
        for ch in stream:
            count = self.sock.send(bytes([ch]))
            time.sleep(CHAR_INTERVAL)
            assert count != 0, "Broken pipe"

class CPU:
    def __init__(self, name, override=True, log_dir='./pad_logs', plat=None):
        self.name = name
        self.log_dir = osp.join(log_dir, name)
        os.makedirs(self.log_dir, exist_ok=override)
        if plat is None:
            plat = Platform()

        self.plat = plat
        self.plat.hold_reset()
        self.plat.upload_rbl()
        self.term = Terminal(*to_host_port(self.plat.get_serial()))
        self.plat.upload_ucore()
        self.plat.click_reset()
        self.execute("", ["$ "], "init")
    
    def execute(self, cmd, terminal_phrase, name):
        self.term.write(cmd)
        exec_char_stream(
            "THINPAD",
            osp.join(self.log_dir, f"{name}.log"),
            self.term.read(),
            terminal_phrase
        )       

if __name__ == "__main__":
    cpu = CPU("ls", True)
    cpu.execute("ls\n", ["$ "], "main")
