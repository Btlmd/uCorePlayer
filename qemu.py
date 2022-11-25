"""
QEMU Connection
"""

import subprocess
import os
import shlex
from functools import partial
import json
import os.path as osp
from utils import *

class EMU:
    def __init__(self, name, override=True, log_dir='./emu_logs'):
        self.cwd = os.getcwd()
        with open("config.json", "r") as f:
            cfg = json.load(f)
        os.chdir(cfg['ucore_root'])
        print("launching QEMU")
        self.proc = subprocess.Popen(
            ["make", "qemu"],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            universal_newlines=True
        )
        os.chdir(self.cwd)
        self.name = name
        self.log_dir = osp.join(log_dir, name)
        os.makedirs(self.log_dir, exist_ok=override)

        self.execute("", ["$ "], "init")

    def execute(self, cmd, terminal_phrase, name):
        self.proc.stdin.write(cmd)
        self.proc.stdin.flush()
        exec_char_stream(
            "QEMU",
            osp.join(self.log_dir, f"{name}.log"),
            iter(partial(self.proc.stdout.readline, 1), ""),
            terminal_phrase
        )

if __name__ == '__main__':
    emu = EMU("ls", True)
    emu.execute("ls\n\n", ["$ "], "main")