import subprocess
from shlex import split

def syscall(command):
    command = split(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    return process.communicate()
