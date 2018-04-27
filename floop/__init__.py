from platform import system
from .cli import FloopCLI 

class UnsupportedOperatingSystemException(Exception):
    pass

def main():
    operating_system = system()
    if operating_system != 'Linux':
        raise UnsupportedOperatingSystemException(operating_system)
    FloopCLI()

if __name__ == '__main__':
    main()
