import subprocess
from shlex import split

class SystemCallException(Exception):
    pass

def syscall(command, check=False, verbose=False):
    command = split(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    out, err = process.communicate()
    if verbose:
        print((out, err))
    if check:
        if process.returncode != 0:
            raise SystemCallException(err)
    return (out, err)
