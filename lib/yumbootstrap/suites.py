#!/usr/bin/python

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
    raise YBError('Unrecognized suite: %s', suite_name)

  suite_file = os.path.join(directory, suite_name + '.suite')

  if not os.path.isfile(suite_file):
    raise YBError('Unrecognized suite: %s', suite_name)

  try:
    return Suite(suite_name, suite_file)
  except OSError, e:
    raise YBError("Can't access %s: %s", directory, e.args[1], exit = 1)

#-----------------------------------------------------------------------------

# generic section
class Section(object):
  LINE = re.compile(
    r'^(?P<name>[a-zA-Z0-9_-]+)\s*=\s*(?P<value>\S.*|)$'
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
    r'^(?P<name>[a-zA-Z0-9_-]+)\s*(?P<set>\??=)\s*(?P<value>\S.*|)$'
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
    r'^(?P<name>[a-zA-Z0-9_-]+)\s*(?P<set>\??=)\s*(?P<value>\S.*|)$'
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
    for (name, script) in self._scripts_global:
      yield script

  def skip(self, names):
    if isinstance(names, (list, tuple, dict)):
      names = set(names)
    else:
      names = set([names])

    for (name, script) in self._scripts_global:
      if name not in names:
        yield script

  def just(self, names):
    if isinstance(names, (list, tuple, dict)):
      names = set(names)
    else:
      names = set([names])

    for (name, script) in self._scripts_global:
      if name in names:
        yield script

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
        r'(?P<name>[a-zA-Z0-9_-]+)\s*=\s*(?P<value>\S.*|)'
      ')|(?P<keep>'
        r'(?P<keep_name>[a-zA-Z0-9_*]+)'
      ')'
    ')$'
  )

  def __init__(self):
    self._set = {}
    self._keep = []

  def add(self, variable, name, value, keep, keep_name):
    if keep_name is not None:
      self._keep.append(keep_name)
    elif name not in self._set:
      self._set[name] = value
    # else silently discard (keep only the first occurrence)

  def __iter__(self):
    raise NotImplementedError() # TODO

  def __contains__(self, name):
    raise NotImplementedError() # TODO

  def __getitem__(self, name):
    raise NotImplementedError() # TODO

  def dict(self):
    raise NotImplementedError() # TODO

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
    self._directory = os.path.abspath(os.path.dirname(filename))
    self._suite = suite
    self._main = MainSection(self._directory, suite)
    self._packages = Packages()
    self._environment = EnvironmentSection()
    self._repositories = RepositorySection()
    self._post_install = ScriptSection(self._directory, suite)
    self._sections = {} # unrecognized ones
    self.read(filename)

    for f in self.get_all('packages'):
      self._packages.read(f)

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
    return self._environment.dict()

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

      if line == '' or line.startswith("#"):
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
# vim:ft=python
