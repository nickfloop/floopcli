import subprocess
from shlex import split
from typing import Tuple 

class SystemCallException(Exception):
    pass

def syscall(command: str, check: bool=False, verbose: bool=False) -> Tuple[bytes, bytes]:
    command = split(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    out, err = process.communicate()
    if verbose:
        print((out, err))
    if check:
        if process.returncode != 0:
            raise SystemCallException(err)
    return (out, err)
