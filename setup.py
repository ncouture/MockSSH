#!/usr/bin/env python

import os

from setuptools import setup, find_packages, Command

__version__ = '1.4.2'


class CleanCommand(Command):
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, 'Must be in package root: %s' % (
            self.cwd)
        os.system('rm -rf ./build ./dist ./*.pyc'
                  '       ./*.tgz ./*.egg-info ./private.key ./public.key')

desc = ('MockSSH: Mock an SSH server and all commands it supports.')

long_desc = '''
MockSSH was developed to emulate operating systems behind SSH servers
in order to test task automation without having access to the real servers.

There has been interest in using MockSSH to perform end-to-end unit tests
against SSH servers and as such, a threaded version of MockSSH server is
available as of version 1.4 (thanks to Claudio Mignanti).

MockSSH is derived from kippo, an SSH honeypot.
'''

setup(
    name='MockSSH',
    version=__version__,
    url='https://github.com/ncouture/MockSSH',

    description=desc,
    long_description=long_desc,

    author='Nicolas Couture',
    author_email='nicolas.couture@gmail.com',

    py_modules=['MockSSH'],
    packages=find_packages(exclude=['tests', 'examples']),
    package_data={
        'mocksshy': ['*.hy'],
    },

    scripts=['examples/mock_cisco.py',
             'examples/mock_F5.py',
             'examples/mock.hy'],

    install_requires=['Twisted', 'pycrypto', 'paramiko', 'pyasn1', 'hy'],

    cmdclass={
        'clean': CleanCommand
    },

    license='Other',
)
