# Based on https://stackoverflow.com/questions/24306205/file-not-found-error-when-launching-a-subprocess
from sys import stdout
import subprocess
from shlex import split
from collections import namedtuple
from functools import reduce

import contextlib

def pipeline(*commands):
    if len(commands) < 2:
        try:
            commands = commands.split('|')
        except AttributeError:
            pass
    start_command = split(commands[0])
    start_process = subprocess.Popen(start_command, stdout=subprocess.PIPE)#, universal_newlines=True)
    #for line in unbuffered(start_process):
    #    print(line)
    last_process = reduce(_create_pipe, map(split, commands[1:]), start_process)
    return last_process.communicate()

def _create_pipe(previous, command):
    proc = subprocess.Popen(command, stdin=previous.stdout, stdout=subprocess.PIPE)
    #for line in unbuffered(proc):
    #    print(line)
    previous.stdout.close()
    return proc

# Based on http://blog.thelinuxkid.com/2013/06/get-python-subprocess-output-without.html
newlines = ['\n', '\r\n', '\r']
def unbuffered(proc, stream='stdout'):
    stream = getattr(proc, stream)
    with contextlib.closing(stream):
        while True:
            out = []
            last = stream.read(1)
            # Don't loop forever
            if last == '' and proc.poll() is not None:
                break
            while last not in newlines:
                # Don't loop forever
                if last == '' and proc.poll() is not None:
                    break
                out.append(last)
                last = stream.read(1)
            out = ''.join(out)
            yield out
