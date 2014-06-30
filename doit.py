#!/usr/bin/python

import os
import sys
import optparse

import yumbootstrap.yum
from yumbootstrap.fs import touch

#-----------------------------------------------------------------------------

o = optparse.OptionParser(
  usage = '\n  %prog [options] <suite> <target>'
          '\n  %prog [options] --list-suites'
          '\n  %prog [options] --fix-rpmdb <target>'
          '\n  %prog [options] --cleanup <target>'
          '\n  %prog [options] --print-config > yum.conf'
          '',
  description = 'Install Yum-based distribution in a chroot environment.',
)

#-----------------------------------------------------------

expected_nargs = {
  'install':     2,
  'list_suites': 0,
  'yum.conf':    0,
  'fix_rpmdb':   1,
  'cleanup':     1,
  #'download':     ?,
  #'second_stage': ?,
  #'tarball':      ?,
}

o.set_defaults(
  action = 'install',
  include = [],
  exclude = [],
  groups = [],
  repositories = {},
)

def add_pkg_list(option, opt, value, parser, attr):
  getattr(parser.values, attr).extend(value.split(','))

def add_kv_list(option, opt, value, parser, attr):
  if '=' not in value:
    raise optparse.OptionValueError('"%s" is not in NAME=VALUE format' % value)
  (k,v) = value.split('=', 1)
  getattr(parser.values, attr)[k] = v

#-----------------------------------------------------------

o.add_option(
  '--list-suites',
  action = 'store_const', dest = 'action', const = 'list_suites',
  help = 'list available suites and exit',
)
o.add_option(
  '--print-config',
  action = 'store_const', dest = 'action', const = 'yum.conf',
  help = 'print Yum configuration which will be used by yumbootstrap',
)
o.add_option(
  '--fix-rpmdb',
  action = 'store_const', dest = 'action', const = 'fix_rpmdb',
  help = "fix chroot's RPM database instead of installing packages"
         " (see --skip-fix-rpmdb)",
)
o.add_option(
  '--cleanup',
  action = 'store_const', dest = 'action', const = 'cleanup',
  help = "remove yumbootstrap config from chroot instead of installing"
         " packages (see --skip-cleanup)",
)

#-----------------------------------------------------------

o.add_option(
  '--verbose',
  action = 'store_true', default = False,
  help = 'be verbose about operations',
)
o.add_option(
  '--noninteractive',
  action = 'store_false', dest = 'interactive', default = True,
  help = 'run in non-interactive mode (e.g. no progress bars)',
)
o.add_option(
  '--arch',
  action = 'store', default = os.uname()[4],
  help = 'specify target architecture',
)
o.add_option(
  '--include',
  action = 'callback', type = 'string',
  callback = add_pkg_list, callback_args = ('include',),
  help = 'include these packages (comma separated list; may be specified'
         ' multiple times)',
  metavar = 'RPMS'
)
o.add_option(
  '--exclude',
  action = 'callback', type = 'string',
  callback = add_pkg_list, callback_args = ('exclude',),
  help = 'exclude these packages (comma separated list; may be specified'
         ' multiple times)',
  metavar = 'RPMS'
)
o.add_option(
  '--groups',
  action = 'callback', type = 'string',
  callback = add_pkg_list, callback_args = ('groups',),
  help = 'install these package groups (comma separated list; may be specified'
         ' multiple times)',
)
o.add_option(
  '--gpgkey',
  action = 'append', dest = 'gpg_keys', default = [],
  help = 'add GPG key as a trusted RPM signing key (may be specified'
         ' multiple times)',
  metavar = 'KEYFILE'
)
o.add_option(
  '--repo',
  action = 'callback', type = 'string',
  callback = add_kv_list, callback_args = ('repositories',),
  help = 'use this Yum repository (may be specified multiple times)',
  metavar = 'NAME=URL'
)
o.add_option(
  '--skip-fix-rpmdb',
  action = 'store_false', dest = 'fix_rpmdb', default = True,
  help = "don't fix chroot's RPM database (`yum --installroot=...'"
         " won't break the chroot)",
)
o.add_option(
  '--skip-cleanup',
  action = 'store_false', dest = 'cleanup', default = True,
  help = "don't remove yumbootstrap config or cache from chroot",
)
# TODO
#o.add_option(
#  '--download-only',
#  action = 'store_const', dest = 'action', const = 'download',
#  help = "download RPMs only, don't install them",
#)
#o.add_option(
#  '--foreign',
#  action = 'store_true', dest = 'no_scripts', default = False,
#  help = "don't run post-install scripts from RPM (mainly useful for"
#         " non-matching architecture in --arch option)",
#)
#o.add_option(
#  '--second-stage',
#  action = 'store_const', dest = 'action', const = 'second_stage',
#  help = "finalize the installation started with --foreign option",
#)
#o.add_option(
#  '--make-tarball',
#  action = 'store_const', dest = 'action', const = 'tarball',
#  help = "make a tarball with RPMs instead of installing them",
#)
#o.add_option(
#  '--unpack-tarball',
#  action = 'store', dest = 'tarball', default = None,
#  help = "use RPMs from a tarball created with --make-tarball option",
#)

opts, args = o.parse_args()

if len(args) != expected_nargs[opts.action]:
  o.error("wrong number of arguments")

sys.exit()

#-----------------------------------------------------------------------------

touch(root, 'etc/fstab', text = '# empty fstab')
touch(root, 'etc/mtab')

# TODO: extract yum.conf out of yumbootstrap.yum.Yum class (could be
# YumConfig)
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
yum.clean()

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
