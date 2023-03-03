#!/usr/bin/python3

import re
import os
import errno
from exceptions import YBError

#-----------------------------------------------------------------------------

def list_suites(directory):
  try:
    result = [fn[:-6] for fn in os.listdir(directory) if fn.endswith('.suite')]
    result.sort()
    return result
  except OSError, e:
    if e.errno == errno.ENOENT:
      return []
    raise YBError("Can't access %s: %s", directory, e.args[1], exit = 1)

def load_suite(directory, suite_name):
  if '/' in suite_name:
    raise YBError('Unrecognized suite: %s', suite_name, exit = 1)

  suite_file = os.path.join(directory, suite_name + '.suite')

  if not os.path.isfile(suite_file):
    raise YBError('Unrecognized suite: %s', suite_name, exit = 1)

  try:
    return Suite(suite_name, suite_file)
  except OSError, e:
    raise YBError("Can't access %s: %s", directory, e.args[1], exit = 1)

#-----------------------------------------------------------------------------

# generic section
class Section(object):
  LINE = re.compile(
    r'^(?P<name>[a-zA-Z0-9_.-]+)\s*=\s*(?P<value>\S.*|)$'
  )

  def __init__(self):
    self._values = {}

  def add(self, name, value):
    if name not in self._values:
      self._values[name] = []
    self._values[name].append(value)

  def __iter__(self):
    return self._values.__iter__()

  def __contains__(self, name):
    return (name in self._values)

  def __getitem__(self, name):
    if name in self._values:
      return self._values[name][0]

  def get_all(self, name):
    return self._values.get(name, [])

  def dict(self):
    return self._values.copy()

#-----------------------------------------------------------------------------

# top-level, unnamed section
# two keys get special treatment
class MainSection(Section):
  LINE = re.compile(
    r'^(?P<name>[a-zA-Z0-9_.-]+)\s*(?P<set>\??=)\s*(?P<value>\S.*|)$'
  )

  def __init__(self, directory, suite):
    super(MainSection, self).__init__()
    self._directory = directory
    self._suite = suite

  def add(self, name, set, value):
    if name in ('packages', 'gpg_key'):
      # expand "${suite}"
      value = value.replace('${suite}', self._suite)
      # make the file relative to suite file location
      value = os.path.normpath(os.path.join(self._directory, value))
      if set == '?=' and not os.path.exists(value):
        return
    super(MainSection, self).add(name = name, value = value)

#-----------------------------------------------------------------------------

# [repositories] section
# repos.dict() only returns first element from the list
class RepositorySection(Section):
  def dict(self):
    return dict([(name, value[0]) for (name, value) in self._values.items()])

#-----------------------------------------------------------------------------

# [post_install] section
# remembers order between all the entries, not only in group
class ScriptSection(Section):
  LINE = re.compile(
    r'^(?P<name>[a-zA-Z0-9_.-]+)\s*(?P<set>\??=)\s*(?P<value>\S.*|)$'
  )

  def __init__(self, directory, suite):
    self._scripts_global = [] # ('name', ['script', ...])
    self._scripts = {}
    self._directory = directory
    self._suite = suite

  def add(self, name, set, value):
    # expand "${suite}"
    value = value.replace('${suite}', self._suite)

    script = value.split(' ')
    # make the path relative to suite file location (if applicable)
    if '/' in script[0]:
      script[0] = os.path.normpath(os.path.join(self._directory, script[0]))

    # skip the entry if it's conditional and the target file doesn't exist
    if set == '?=' and '/' in script[0] and not os.path.exists(script[0]):
      return

    self._scripts_global.append((name, script))
    if name not in self._scripts:
      self._scripts[name] = []
    self._scripts[name].append(script)

  def names(self):
    return sorted(self._scripts.keys())

  def __iter__(self):
    return self._scripts_global.__iter__()

  def __len__(self):
    return len(self._scripts_global)

  def __contains__(self, name):
    return (name in self._scripts)

  def __getitem__(self, name):
    return self._scripts.get(name)

#-----------------------------------------------------------------------------

# [environment] section
class EnvironmentSection(Section):
  LINE = re.compile(
    '^(?:'
      '(?P<variable>'
        r'(?P<name>[a-zA-Z0-9_.-]+)\s*=\s*(?P<value>\S.*|)'
      ')|(?P<keep>'
        r'(?P<keep_name>[a-zA-Z0-9_.*-]+)'
      ')'
    ')$'
  )

  @staticmethod
  def _re(pattern):
    return re.compile('^' + pattern.replace('*', '.*') + '$')

  def __init__(self, env = None, keep = None):
    if env is None:
      self._set = {}
    else:
      self._set = env.copy()

    if keep is None:
      self._keep_values = set()
      self._keep_wildcards = []
    else:
      self._keep_values = set([k for k in keep if '*' not in k])
      self._keep_wildcards = [
        EnvironmentSection._re(k) for k in keep if '*' in k
      ]

  def set(self, name, value):
    self._set[name] = value

  def keep(self, name):
    if '*' in name:
      self._keep_wildcards.append(EnvironmentSection._re(name))
    else:
      self._keep_values.add(name)

  def add(self, variable, name, value, keep, keep_name):
    if keep_name is not None:
      self.keep(keep_name)
    elif name not in self._set:
      self.set(name, value)
    # else silently discard (keep only the first occurrence)

  def __iter__(self):
    raise NotImplementedError() # TODO

  def __contains__(self, name):
    raise NotImplementedError() # TODO

  def __getitem__(self, name):
    raise NotImplementedError() # TODO

  def _matches_wildcard(self, name):
    for p in self._keep_wildcards:
      if p.match(name):
        return True
    return False

  def dict(self, env = {}):
    result = {}
    for e in env:
      if e in self._keep_values or self._matches_wildcard(e):
        result[e] = env[e]
    result.update(self._set)
    return result

#-----------------------------------------------------------------------------

# packages list
class Packages:
  def __init__(self):
    self.install = []
    self.groups = []
    self.exclude = []

  def read(self, filename):
    f = open(filename)
    while True:
      line = f.readline()
      if line == '':
        return
      line = line.strip()
      if line == '' or line.startswith("#"):
        continue
      self.add(line)

  def add(self, line):
    if line.startswith('-'):
      self.exclude.append(line[1:])
    elif line.startswith('@'):
      self.groups.append(line[1:])
    else:
      self.install.append(line)

#-----------------------------------------------------------------------------

class Suite:
  def __init__(self, suite, filename):
    self._suite = suite
    self._suite_file = os.path.abspath(filename)
    self._directory = os.path.dirname(self._suite_file)
    self._main = MainSection(self._directory, suite)
    self._packages = Packages()
    self._environment = EnvironmentSection()
    self._repositories = RepositorySection()
    self._post_install = ScriptSection(self._directory, suite)
    self._sections = {} # unrecognized ones
    self.read(filename)

    for f in self.get_all('packages'):
      self._packages.read(f)

    # coming from shell
    self._environment.set("PATH", "/usr/local/bin:/usr/bin:/bin")
    self._environment.set("SHELL", "/bin/sh")

    # set by yumbootstrap
    self._environment.set("SUITE",      self._suite)
    self._environment.set("SUITE_CONF", self._suite_file)
    self._environment.set("YUMBOOTSTRAP_DIR",  "yumbootstrap")
    self._environment.set("YUM_CONF",          "yumbootstrap/yum.conf")

    # coming from shell
    for e in ["SHLVL", "TERM", "HOME", "USER", "LOGNAME", "PWD"]:
      self._environment.keep(e)

    # proxy-related, coming from shell
    for e in ["http_proxy", "ftp_proxy"]:
      self._environment.keep(e)

    # set by yumbootstrap
    for e in ["TARGET", "SCRIPT_NAME", "SCRIPT_PATH", "VERBOSE"]:
      self._environment.keep(e)

  #---------------------------------------------------------

  @property
  def name(self):
    return self['name']

  @property
  def release(self):
    return self['release']

  @property
  def packages(self):
    return self._packages

  @property
  def gpg_keys(self):
    return self.get_all('gpg_key')

  @property
  def repositories(self):
    return self._repositories.dict()

  @property
  def post_install(self):
    return self._post_install

  @property
  def environment(self):
    return self._environment.dict(os.environ)

  #---------------------------------------------------------

  def __contains__(self, name):
    return (name in self._main)

  def __getitem__(self, name):
    if name in self._main:
      return self._main[name]

  def get_all(self, name):
    return self._main.get_all(name)

  def section(self, name):
    if section in self._sections:
      return self._sections[name]

  #---------------------------------------------------------

  def read(self, filename):
    f = open(filename)
    lineno = 0
    line = None
    section = self._main # start with main section
    section_name = None


    while True:
      line = f.readline()
      if line == '':
        return
      line = line.strip()
      lineno += 1

      if line == '' or line.startswith("#") or line.startswith(";"):
        continue

      if line[0] == '[' and line[-1] == ']':
        section_name = line[1:-1]
        if section_name == 'repositories':
          section = self._repositories
        elif section_name == 'environment':
          section = self._environment
        elif section_name == 'post_install':
          section = self._post_install
        elif section_name in self._sections:
          section = self._sections[section_name]
        else:
          section = self._sections[section_name] = Section()
        continue

      match = section.LINE.match(line)
      if not match:
        if section_name is None:
          raise YBError('Invalid config line %d: %s', lineno, line, exit = 1)
        else:
          raise YBError('Invalid config line %d (section %s): %s',
                        lineno, section_name, line, exit = 1)

      groups = match.groupdict()
      section.add(**groups)

#-----------------------------------------------------------------------------
# vim:ft=python3
