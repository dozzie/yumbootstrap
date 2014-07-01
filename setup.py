#!/usr/bin/python

from setuptools import setup, find_packages
from glob import glob

setup(
  name         = 'yumbootstrap',
  version      = '0.0.1',
  description  = 'chroot installer for Red Hat derivatives',
  scripts      = glob("bin/*"),
  packages     = find_packages("lib"),
  package_dir  = { "": "lib" },
)
