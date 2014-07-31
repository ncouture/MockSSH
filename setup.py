#!/usr/bin/env python

from setuptools import setup, find_packages, Command
import os
import sys

# Be sure to keep this version and the one inside MockSSH.py in sync!
__version__ = '1.3'

# Names of required packages
SETUP_PATH = os.path.dirname(os.path.abspath(__file__))
RFILE_PATH = os.path.join(SETUP_PATH, 'requirements.txt')


def _get_requirements(rfile=RFILE_PATH):
    """Read the requirements from 'requirements.txt'"""
    with open(rfile, 'r') as f:
        return f.read().splitlines()
REQUIREMENTS = _get_requirements()


class CleanCommand(Command):
    user_options = []
    def initialize_options(self):
        self.cwd = None
    def finalize_options(self):
        self.cwd = os.getcwd()
    def run(self):
        assert os.getcwd() == self.cwd, 'Must be in package root: %s' % self.cwd
        os.system ('rm -rf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')

desc = 'Mock an SSH server and define all commands it supports (Python, Twisted)'
long_desc = '''
Mock an SSH server and define all commands it supports (Python, Twisted).

MockSSH is derived from kippo, an SSH honeypot. This was developed to emulate
different operating systems running SSH servers in order to test task
automation without having access to the actual servers.
'''

setup(
    name='MockSSH',
    version=__version__,
    author='Nicolas Couture',
    author_email='nicolas.couture@gmail.com',
    #packages=find_packages(exclude=['tests']),
    py_modules=['MockSSH'],
    license='MIT', # Inherited from Twisted
    url='https://github.com/ncouture/MockSSH',
    description=desc,
    long_description=long_desc,
    install_requires=REQUIREMENTS,
    cmdclass={
        'clean': CleanCommand
    }
)
