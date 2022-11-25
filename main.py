import term
import qemu
from argparse import ArgumentParser
from timeout_decorator import timeout, TimeoutError
import os
from difflib import unified_diff
from termcolor import colored

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--qemu', default=False, action='store_true')
    parser.add_argument('--remote', default=False, action='store_true')
    parser.add_argument('--compare', default=False, action='store_true')
    parser.add_argument('--timeout', default=30, type=int)
    parser.add_argument('--commit', default=None, type=str)
    args = parser.parse_args()

    if args.remote:
        assert args.commit

    with open("tests.txt", "r") as f:
        tests = f.readlines()
    # print("Found test cases", tests)

    if args.remote:
        plat = term.Platform(args.commit)

    if args.qemu or args.remote:
        for test in tests:
            name = test.strip()
            task = "main"
            print(f">>>>>>> BEGIN TEST {name} >>>>>>>")
            if args.remote:
                cpu = term.CPU(name, plat=plat)
                timeout(args.timeout)(cpu.execute)(test + "\n\n", ["$ ", "K>"], task)
            if args.qemu:
                emu = qemu.EMU(name)
                timeout(args.timeout)(emu.execute)(test + "\n\n", ["$ ", "K>"], task)
            print(f"<<<<<<< END TEST {name} <<<<<<<<")
            print()

    results = {}
    if args.compare:
        for test in tests:
            name = test.strip()
            emu_p = os.path.join("./emu_logs", name, "main.log")
            cpu_p = os.path.join("./pad_logs", name, "main.log")
            if not os.path.exists(emu_p):
                print("missing", emu_p)
                continue
            if not os.path.exists(cpu_p):
                print("missing", cpu_p)
                continue
            with open(emu_p) as f, open(cpu_p) as g:
                diff = unified_diff(f.readlines(), g.readlines(), f"QEMU/{name}", f"THINPAD/{name}")
                results[name] = "".join(diff)
    
    print("%d test cases in total" % len(tests))
    print()
    print(colored("[IDENTICAL TEST CASES]", "green"))
    for name, diff in results.items():
        if diff == "":
            print(colored(f" > [{name}]", "green"))
    
    print()        
    print(colored("[DIFFERENT TEST CASES]", "red"))
    for name, diff in results.items():
        if diff != "":
            print(colored(f" > [{name}]", "red"))
    print()     
    for name, diff in results.items():
        if diff != "":
            print(colored(f"[{name}]", "blue"))
            for line in diff.split("\n"):
                if line.startswith("-"):
                    print(colored(line, "red"))
                elif line.startswith("+"):
                    print(colored(line, "green"))
                else:
                    print(line)
            print()

        

