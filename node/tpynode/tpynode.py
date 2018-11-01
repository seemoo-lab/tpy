import subprocess
import socket
import pkg_resources
import Pyro4


class TPyNode:

    """TPyNode

    The basic module provides basic commands to interface a node
    """

    def __init__(self, pyro, **kwargs):
        self._pyro = pyro
        self._modules = dict()

    def register_module(self, module, name):
        self._modules[name] = module

    @Pyro4.expose
    def echo(self, message):
        return message

    @Pyro4.expose
    def file_read(self, file):
        with open(file, mode='r') as f:
            data = f.read()
        return data

    @Pyro4.expose
    @property
    def modules(self):
        return self._modules

    @Pyro4.expose
    def run(self, *args, **kwargs):
        return subprocess.check_output(args, kwargs).decode()

    @Pyro4.expose
    @property
    def hostname(self):
        return socket.gethostname()

    @Pyro4.expose
    def version(self):
        return pkg_resources.require('tpynode')[0].version
