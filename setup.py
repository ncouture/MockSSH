#!/usr/bin/env python

import os

from setuptools import Command, find_packages, setup

NAME = "MockSSH"

URL = "https://github.com/ncouture/MockSSH"

AUTHOR = 'Nicolas Couture'

MAINTAINER = 'Nicolas Couture'

AUTHOR_EMAIL = 'nicolas.couture@gmail.com'

COPYRIGHT = 'Copyright 2013-2016, Nicolas Couture'

LICENSE = 'BSD'

VERSION = '1.4.5'

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 2.7',
    'Framework :: Twisted',
    'Environment :: Console',
    'Operating System :: POSIX',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Topic :: Software Development :: Testing',
    'Topic :: System :: Emulators'
]

PLATFORMS = ['Posix', 'MacOS X', 'Windows']

DESCRIPTION = 'MockSSH: Mock an SSH server and all commands it supports.'

LONG_DESCRIPTION = '''
MockSSH was developed to emulate operating systems behind SSH servers
in order to test task automation without having access to the real servers.

There has been interest in using MockSSH to perform end-to-end unit tests
against SSH servers and as such, a threaded version of MockSSH server is
available as of version 1.4 (thanks to Claudio Mignanti).

MockSSH is derived from kippo, an SSH honeypot.
'''

SCRIPTS = ['examples/mock_cisco.py', 'examples/mock_F5.py', 'examples/mock.hy']

PY_MODULES = ['MockSSH']

PACKAGES = find_packages(exclude=['tests', 'examples'])

PACKAGE_DATA = {'mocksshy': ['*.hy']}

INSTALL_REQUIRES = ['Twisted==16.7.0rc2', 'paramiko==2.1.6', 'hy==0.11.1']

KEYWORDS = [
    'ssh server emulation', 'ssh server testing', 'mock ssh', 'script ssh'
]


class CleanCommand(Command):
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, 'Must be in package root: {}'.format(
            self.cwd)
        os.system('rm -rf ./build ./dist ./*.pyc'
                  '       ./*.tgz ./*.egg-info ./private.key ./public.key')


CMDCLASS = {'clean': CleanCommand}

setup(
    url=URL,
    name=NAME,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    version=VERSION,
    classifiers=CLASSIFIERS,
    py_modules=PY_MODULES,
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    keywords=KEYWORDS,
    scripts=SCRIPTS,
    install_requires=INSTALL_REQUIRES,
    cmdclass=CMDCLASS,
    platforms=PLATFORMS,
    license=LICENSE)
