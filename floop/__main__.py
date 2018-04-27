from .cli import FloopCLI
from platform import system

class UnsupportedOperatingSystemException(Exception):
    pass

def main():
    operating_system = system()
    if operating_system != 'Linux':
        raise UnsupportedOperatingSystemException(operating_system)
    FloopCLI()

if __name__ == '__main__':
    main()
