#!/usr/bin/python

import sys
import optparse

import yumbootstrap.yum
from yumbootstrap.fs import touch

#-----------------------------------------------------------------------------

# TODO: parse command line options

root = sys.argv[1]

#-----------------------------------------------------------------------------

touch(root, 'etc/fstab', text = '# empty fstab')
touch(root, 'etc/mtab')

yum = yumbootstrap.yum.Yum(
  chroot = root,
  repos = {
    'centos':         'http://mirror.centos.org/centos/6/os/x86_64/',
    'centos-updates': 'http://mirror.centos.org/centos/6/updates/x86_64/',
  },
  interactive = True,
)

# installing works also without adding key, but --nogpgcheck is passed to Yum,
# so it's generally discouraged
yum.add_key('gpg/RPM-GPG-KEY-CentOS-6')
yum.install('redhat-release') # to show how it works

yum.install(['yum', '/usr/bin/db_load']) # needed for yum.fix_rpmdb()
yum.fix_rpmdb()

# packages:
#   core:
#     * install       coreutils bash grep gawk basesystem rpm yum
#     * groupinstall  Core
#   OS:
#     * install       less make mktemp vim-minimal
#     * groupinstall  Base
#   release:
#     * install       redhat-release | centos-release | fedora-release

#-----------------------------------------------------------------------------
# vim:ft=python
