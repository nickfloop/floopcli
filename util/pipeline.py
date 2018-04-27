# Based on https://stackoverflow.com/questions/24306205/file-not-found-error-when-launching-a-subprocess
import subprocess
from shlex import split
from collections import namedtuple
from functools import reduce

def pipeline(*commands):
    if len(commands) < 2:
        try:
            commands = commands.split('|')
        except AttributeError:
            pass
    start_command = split(commands[0])
    start_process = subprocess.Popen(start_command, stdout=subprocess.PIPE)
    last_process = reduce(_create_pipe, map(split, commands[1:]), start_process)
    return last_process.communicate()

def _create_pipe(previous, command):
    proc = subprocess.Popen(command, stdin=previous.stdout, stdout=subprocess.PIPE)
    previous.stdout.close()
    return proc
