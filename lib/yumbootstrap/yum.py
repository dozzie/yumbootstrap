#!/usr/bin/python

import rpm
import os
import shutil

import bdb
import sh
import fs

#-----------------------------------------------------------------------------

def mklist(value):
  if isinstance(value, list):
    return value
  elif isinstance(value, tuple):
    return list(value)
  else:
    return [value]

#-----------------------------------------------------------------------------

# TODO:
#   * setarch
#   * multilib
class Yum:
  def __init__(self, chroot, repos = {},
               yum = '/usr/bin/yum', rpm = '/usr/bin/rpm',
               interactive = False):
    self.chroot = os.path.abspath(chroot)
    self.yum = yum
    self.rpm = rpm
    self.interactive = interactive
    self.yum_config_dir = os.path.join(self.chroot, 'etc/yumbootstrap.chroot')
    self.yum_config = os.path.join(self.yum_config_dir, 'yum.conf')
    self.has_key = False
    self.rpmdb_fixed = False

    yum_conf_main = '[main]\nexactarch=1\nobsoletes=1\n'
    yum_conf_repos = [
      '[%s]\nname = %s\nbaseurl = %s\ngpgcheck = 1\n' % (rn, rn, repos[rn])
      for rn in sorted(repos)
    ]
    yum_conf = yum_conf_main + ''.join(yum_conf_repos)
    fs.touch(self.yum_config, text = yum_conf_main + ''.join(yum_conf_repos))

  def __del__(self):
    shutil.rmtree(self.yum_config_dir, ignore_errors = True)

  def add_key(self, key_file):
    sh.run([self.rpm, '--root', self.chroot, '--import'] + mklist(key_file))
    self.has_key = True

  def _yum_call(self):
    opts = [
      self.yum, '-c', self.yum_config, '--installroot', self.chroot, '-y'
    ]

    if self.interactive:
      opts.extend(['-e', '1', '-d', '2'])
    else:
      opts.extend(['-e', '1', '-d', '1'])

    if not self.has_key:
      opts.append('--nogpgcheck')

    return opts

  def install(self, packages):
    if self.rpmdb_fixed:
      raise Exception("Can't install anything after RPM DB was fixed")

    sh.run(self._yum_call() + ['install'] + mklist(packages))

  def group_install(self, groups):
    if self.rpmdb_fixed:
      raise Exception("Can't install anything after RPM DB was fixed")

    sh.run(self._yum_call() + ['groupinstall'] + mklist(groups))

  def fix_rpmdb(self):
    current_rpmdb_dir = rpm.expandMacro('%{_dbpath}')
    expected_rpmdb_dir = sh.run(
      """python -c 'import rpm; print rpm.expandMacro("%{_dbpath}")'""",
      chroot = self.chroot,
      pipe = sh.READ,
    ).read().strip()

    # input directory
    rpmdb_dir = os.path.join(self.chroot, current_rpmdb_dir.lstrip('/'))

    for db in os.listdir(rpmdb_dir):
      if db.startswith('.'): continue
      in_file = os.path.join(rpmdb_dir, db)
      tmp_file = os.path.join(expected_rpmdb_dir, db + '.tmp')
      out_file = os.path.join(expected_rpmdb_dir, db)

      out_command = sh.run(
        ['db_load', tmp_file],
        chroot = self.chroot, pipe = sh.WRITE,
      )
      bdb.db_dump(in_file, out_command)
      out_command.close()
      os.rename(
        os.path.join(self.chroot, tmp_file.lstrip('/')),
        os.path.join(self.chroot, out_file.lstrip('/'))
      )

    if current_rpmdb_dir != expected_rpmdb_dir:
      # Red Hat under Debian; delete old directory (~/.rpmdb possibly)
      shutil.rmtree(os.path.join(self.chroot, current_rpmdb_dir.lstrip('/')))

    self.rpmdb_fixed = True

#-----------------------------------------------------------------------------
# vim:ft=python
