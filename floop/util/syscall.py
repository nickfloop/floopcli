import subprocess
from sys import stdout
from shlex import split
from typing import Tuple 

class SystemCallException(Exception):
    pass

def syscall(command: str, check: bool=False, verbose: bool=False) -> Tuple[str, str]:
    command = split(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    out = ''
    for line in process.stdout:
        line = line.decode('utf-8')
        out += line
        if verbose:
            stdout.write(line)
    _, err = process.communicate()
    if err is not None:
        err = err.decode('utf-8')
    if check:
        if process.returncode != 0:
            raise SystemCallException(err)
    return (out, err)
