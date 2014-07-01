#!/usr/bin/python

import os
import sys
import optparse

import yumbootstrap.yum
from yumbootstrap.exceptions import YBError

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
#o.add_option(
#  '--arch', # TODO
#  action = 'store', default = os.uname()[4],
#  help = 'specify target architecture',
#)
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
#o.add_option(
#  '--download-only', # TODO
#  action = 'store_const', dest = 'action', const = 'download',
#  help = "download RPMs only, don't install them",
#)
#o.add_option(
#  '--foreign', # TODO
#  action = 'store_true', dest = 'no_scripts', default = False,
#  help = "don't run post-install scripts from RPM (mainly useful for"
#         " non-matching architecture in --arch option)",
#)
#o.add_option(
#  '--second-stage', # TODO
#  action = 'store_const', dest = 'action', const = 'second_stage',
#  help = "finalize the installation started with --foreign option",
#)
#o.add_option(
#  '--make-tarball', # TODO
#  action = 'store_const', dest = 'action', const = 'tarball',
#  help = "make a tarball with RPMs instead of installing them",
#)
#o.add_option(
#  '--unpack-tarball', # TODO
#  action = 'store', dest = 'tarball', default = None,
#  help = "use RPMs from a tarball created with --make-tarball option",
#)

opts, args = o.parse_args()

if len(args) != expected_nargs[opts.action]:
  o.error("wrong number of arguments")

#-----------------------------------------------------------------------------

#-----------------------------------------------------------

def do_install(opts, suite, target):
  import yumbootstrap.suites
  from yumbootstrap.fs import touch

  (suite, version) = suite.split('-', 1)
  if suite == 'centos':
    suite = yumbootstrap.suites.CentOS(version)
  elif suite == 'redhat':
    suite = yumbootstrap.suites.RedHat(version)
  elif suite == 'fedora':
    suite = yumbootstrap.suites.Fedora(version)
  else:
    raise YBError('unrecognized suite: %s', suite)

  os.umask(022)
  # prepare target directory with an empty /etc/fstab
  touch(target, 'etc/fstab', text = '# empty fstab')
  touch(target, 'etc/mtab')

  if len(opts.repositories) > 0:
    repositories = opts.repositories
  else:
    repositories = suite.repositories()

  yum = yumbootstrap.yum.Yum(
    chroot = target,
    repos = repositories,
    interactive = opts.interactive,
  )

  # installing works also without adding key, but --nogpgcheck is passed to
  # Yum, so it's generally discouraged
  if len(opts.gpg_keys) > 0:
    yum.add_key(opts.gpg_keys)

  # TODO: support for --exclude

  # main set of packages (should already include yum and /usr/bin/db_load, so
  # `yum.fix_rpmdb()' works)
  yum.install(suite.packages())

  # requested additional packages
  if len(opts.packages) > 0:
    yum.install(opts.packages)
  if len(opts.groups) > 0:
    yum.group_install(opts.groups)

  if opts.fix_rpmdb:
    do_fix_rpmdb(opts, target, yum)

  if opts.cleanup:
    do_cleanup(opts, target, yum)

#-----------------------------------------------------------

def do_list_suites(opts):
  suites = {
    #'redhat': ['5', '6'],
    'centos': [
      '5', '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.9', '5.10',
      '6', '6.1', '6.2', '6.3', '6.4', '6.5',
    ],
    'fedora': [
      '18', '19', '20',
    ],
  }
  for dist in sorted(suites):
    for rel in suites[dist]:
      print "%s-%s" % (dist, rel)

#-----------------------------------------------------------

def do_yum_conf(opts):
  pass # TODO

#-----------------------------------------------------------

def do_fix_rpmdb(opts, target, yum = None):
  if yum is None:
    yum = yumbootstrap.yum.Yum(
      chroot = target,
      interactive = opts.interactive,
    )

  yum.fix_rpmdb()

#-----------------------------------------------------------

def do_cleanup(opts, target, yum = None):
  if yum is None:
    yum = yumbootstrap.yum.Yum(
      chroot = target,
      interactive = opts.interactive,
    )

  # TODO: remove $target/etc/yumbootstrap.chroot/yum.conf file (now it's
  # removed in yumbootstrap.yum.Yum destructor)
  yum.clean()

#-----------------------------------------------------------

#-----------------------------------------------------------------------------

try:
  if opts.action == 'install':
    do_install(opts, *args)
  elif opts.action == 'list_suites':
    do_list_suites(opts, *args)
  elif opts.action == 'yum.conf':
    do_yum_conf(opts, *args)
  elif opts.action == 'fix_rpmdb':
    do_fix_rpmdb(opts, *args)
  elif opts.action == 'cleanup':
    do_cleanup(opts, *args)
  else:
    # should never happen
    o.error("unrecognized action: %s" % (opts.action,))
except KeyboardInterrupt:
  pass
except YBError, e:
  print >>sys.stderr, e
  sys.exit(e.code)

#-----------------------------------------------------------------------------
# vim:ft=python
