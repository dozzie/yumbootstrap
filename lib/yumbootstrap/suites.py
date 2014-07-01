#!/usr/bin/python

#-----------------------------------------------------------------------------

class Suite(object):
  def name(self):
    raise NotImplementedError()

  def version(self):
    raise NotImplementedError()

  def repositories(self):
    raise NotImplementedError()

  def packages(self):
    # a default set of packages that are more or less required by the system
    # to operate
    # XXX: in Red Hat, package groups are "Core" and "Base"
    return [
      'coreutils', 'bash', 'grep', 'gawk', 'basesystem', 'rpm', 'yum', # @Core
      'less', 'make', 'mktemp', 'vim-minimal',                         # @Base
      '/usr/bin/db_load', 'redhat-release',
    ]

#-----------------------------------------------------------------------------

class RedHat(Suite):
  def __init__(self, version):
    # TODO: validate version
    self._version = version

  def name(self):
    return 'redhat'

  def version(self):
    return self._version

  def repositories(self):
    return None # or this? { 'redhat': None, 'redhat-updates': None }

  #def packages(self): ... # no need to change inherited default

#-----------------------------------------------------------------------------

class CentOS(Suite):
  def __init__(self, version):
    # TODO: validate version
    self._version = version

    if '.' not in version:
      # the newest release
      self._base_url = 'http://mirror.centos.org/centos'
    else:
      # might be the newest release, but that would need to be checked online
      self._base_url = 'http://vault.centos.org/'

  def name(self):
    return 'centos'

  def version(self):
    return self._version

  def repositories(self):
    version = self._version
    base_url = self._base_url
    return {
      'centos':         '%s/%s/os/$basearch/'      % (base_url, version),
      'centos-updates': '%s/%s/updates/$basearch/' % (base_url, version),
    }

  # redhat-release provided by centos-release
  #def packages(self): ... # no need to change inherited default

#-----------------------------------------------------------------------------

class Fedora(Suite):
  def __init__(self, version):
    # TODO: validate version
    self._version = version

    if int(version) >= 18:
      base_url = 'http://download.fedoraproject.org/pub/fedora/linux/releases'
    else:
      base_url = 'http://archives.fedoraproject.org/pub/archive/fedora/linux/releases'
    self._repositories = {
      # TODO: better name
      'fedora': '%s/%s/Everything/$basearch/os/' % (base_url, version),
    }

  def name(self):
    return 'fedora'

  def version(self):
    return self._version

  def repositories(self):
    return self._repositories

  # redhat-release provided by fedora-release
  #def packages(self): ... # no need to change inherited default

#-----------------------------------------------------------------------------
# vim:ft=python
