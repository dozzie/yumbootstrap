#!/usr/bin/python3

import rpm as rpm_mod
import os
import shutil

import bdb
import sh
import fs

import logging
logger = logging.getLogger("yum")

#-----------------------------------------------------------------------------

def mklist(value):
  if isinstance(value, list):
    return value
  elif isinstance(value, tuple):
    return list(value)
  else:
    return [value]

#-----------------------------------------------------------------------------

class YumConfig:
  def __init__(self, chroot, repos = {}, env = None):
    self.chroot = os.path.abspath(chroot)
    self.repos = repos.copy() # shallow copy is enough
    self.gpg_keys = os.path.join(self.chroot, 'yumbootstrap/RPM-GPG-KEYS')
    self.pretend_has_keys = False
    #self.multilib = False
    self.env = env

  def add_repository(self, name, url):
    self.repos[name] = url

  def add_key(self, path, pretend = False):
    if pretend:
      self.pretend_has_keys = True
    else:
      fs.touch(self.gpg_keys)
      open(self.gpg_keys, 'a').write(open(path).read())

  @property
  def config_file(self):
    return os.path.join(self.chroot, 'yumbootstrap/yum.conf')

  @property
  def root_dir(self):
    return os.path.join(self.chroot, 'yumbootstrap')

  def text(self):
    if self.pretend_has_keys or os.path.exists(self.gpg_keys):
      logger.info("GPG keys defined, adding them to repository configs")
      gpgcheck = 1
      def repo(name, url):
        return \
          '\n' \
          '[%s]\n' \
          'name = %s\n' \
          'baseurl = %s\n' \
          'gpgkey = file://%s\n' % (name, name, url, self.gpg_keys)
    else:
      logger.warn("no GPG keys defined, RPM signature verification disabled")
      gpgcheck = 0
      def repo(name, url):
        return \
          '\n' \
          '[%s]\n' \
          'name = %s\n' \
          'baseurl = %s\n' % (name, name, url)

    main = \
      '[main]\n' \
      'exactarch = 1\n' \
      'obsoletes = 1\n' \
      '#multilib_policy = all | best\n' \
      'cachedir = /yumbootstrap/cache\n' \
      'logfile  = /yumbootstrap/log/yum.log\n'
    main += 'gpgcheck = %d\n' % (gpgcheck)
    main += 'reposdir = %s/yumbootstrap/yum.repos.d\n' % (gpgcheck)

    repos = [repo(name, self.repos[name]) for name in sorted(self.repos)]

    return main + ''.join(repos)

#-----------------------------------------------------------------------------

# TODO:
#   * setarch
#   * should `chroot' go through YumConfig?
class Yum:
  def __init__(self, chroot, yum_conf = None, yum = '/usr/bin/yum',
               interactive = False):
    self.chroot = os.path.abspath(chroot)
    if yum_conf is not None:
      self.yum_conf = yum_conf
    else:
      self.yum_conf = YumConfig(chroot = chroot)
    self.yum = yum # yum from host OS
    self.interactive = interactive
    self.rpmdb_fixed = False
    # NOTE: writing yum.conf is delayed to the first operation

  def _yum_call(self):
    yum_conf = self.yum_conf.config_file

    if not os.path.exists(yum_conf):
      logger.info("%s doesn't exist, creating one", yum_conf)
      fs.touch(yum_conf, text = self.yum_conf.text())

    opts = [self.yum, '-c', yum_conf, '--installroot', self.chroot, '-y']

    if self.interactive:
      opts.extend(['-e', '1', '-d', '2'])
    else:
      opts.extend(['-e', '1', '-d', '1'])

    return opts

  def install(self, packages, exclude = []):
    if self.rpmdb_fixed:
      raise Exception("Can't install anything after RPM DB was fixed")

    exclude_opts = ["--exclude=" + pkg for pkg in exclude]

    sh.run(
      self._yum_call() + exclude_opts + ['install'] + mklist(packages),
      env = self.yum_conf.env,
    )

  def group_install(self, groups, exclude = []):
    if self.rpmdb_fixed:
      raise Exception("Can't install anything after RPM DB was fixed")

    exclude_opts = ["--exclude=" + pkg for pkg in exclude]

    sh.run(
      self._yum_call() + exclude_opts + ['groupinstall'] + mklist(groups),
      env = self.yum_conf.env,
    )

  def clean(self):
    logger.info("removing directory %s", self.yum_conf.root_dir)
    shutil.rmtree(self.yum_conf.root_dir, ignore_errors = True)

  def fix_rpmdb(self, expected_rpmdb_dir = None,
                db_load = 'db_load', rpm = 'rpm'):
    logger.info("fixing RPM database for guest")
    current_rpmdb_dir = rpm_mod.expandMacro('%{_dbpath}')
    if expected_rpmdb_dir is None:
      expected_rpmdb_dir = sh.run(
        ['python3', '-c', 'import rpm; print(rpm.expandMacro("%{_dbpath}"))'],
        chroot = self.chroot,
        pipe = sh.READ,
        env = self.yum_conf.env,
      ).strip()

    # input directory
    rpmdb_dir = os.path.join(self.chroot, current_rpmdb_dir.lstrip('/'))

    logger.info('converting "Packages" file')
    in_pkg_db = os.path.join(rpmdb_dir, 'Packages')
    tmp_pkg_db = os.path.join(expected_rpmdb_dir, 'Packages.tmp')
    out_pkg_db = os.path.join(expected_rpmdb_dir, 'Packages')
    out_command = sh.run(
      [db_load, tmp_pkg_db],
      chroot = self.chroot, pipe = sh.WRITE,
      env = self.yum_conf.env,
    )
    bdb.db_dump(in_pkg_db, out_command)
    out_command.close()
    os.rename(
      os.path.join(self.chroot, tmp_pkg_db.lstrip('/')),
      os.path.join(self.chroot, out_pkg_db.lstrip('/'))
    )

    logger.info('removing all the files except "Packages"')
    for f in os.listdir(rpmdb_dir):
      if f in ('.', '..', 'Packages'): continue
      os.unlink(os.path.join(rpmdb_dir, f))

    logger.info("running `rpm --rebuilddb'")
    sh.run(
      [rpm, '--rebuilddb'],
      chroot = self.chroot,
      env = self.yum_conf.env,
    )

    if current_rpmdb_dir != expected_rpmdb_dir:
      # Red Hat under Debian; delete old directory (~/.rpmdb possibly)
      logger.info("removing old RPM DB directory: $TARGET%s",
                  current_rpmdb_dir)
      shutil.rmtree(os.path.join(self.chroot, current_rpmdb_dir.lstrip('/')))

    self.rpmdb_fixed = True

#-----------------------------------------------------------------------------
# vim:ft=python3
