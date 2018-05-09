from floop.dependency.os import check_os

class InstallHostDependencyException(Exception):
    pass

class HostDependency(object):
    def __init__(self):
        check_os()

    def install(self):
        raise NotImplemented('install')
