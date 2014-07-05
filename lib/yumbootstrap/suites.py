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

class Section:
  def __init__(self, values):
    self._values = values

  def __iter__(self):
    return self._values.__iter__()

  def __contains__(self, name):
    return name in self._values

  def __getitem__(self, name):
    if name in self._values:
      return self.get_all(name)[0]

  def get_all(self, name):
    return self._values.get(name, [])

#-----------------------------------------------------------------------------

class Packages:
  def __init__(self):
    self.install = []
    self.groups = []
    self.exclude = []

  def add_file(self, filename):
    f = open(filename)
    while True:
      line = f.readline()
      if line == '':
        return

      line = line.strip()
      if line == '' or line.startswith("#"):
        continue

      if line.startswith('-'):
        self.exclude.append(line[1:])
      elif line.startswith('@'):
        self.groups.append(line[1:])
      else:
        self.install.append(line)

#-----------------------------------------------------------------------------

_CONFIG_LINE_RE = re.compile(
  '^(?:'
    '(?P<variable>'
      r'(?P<name>[a-zA-Z0-9_-]+)\s*(?P<set>\??=)\s*(?P<value>\S.*\S|\S|)'
    ')|(?P<section>'
      r'\[(?P<section_name>[a-zA-Z0-9_-]+)\]'
    ')|(?P<env_keep>'
      r'(?P<env_name>[a-zA-Z0-9_*]+)'
    ')'
  ')\s*$'
)

#-----------------------------------------------------------------------------

class Suite:
  def __init__(self, suite, filename):
    self._suite = suite
    self._sections = {}
    self._read(open(filename))
    if 'environment' not in self._sections:
      self._sections['environment'] = Section({})
    if 'repositories' not in self._sections:
      self._sections['repositories'] = Section({})
    self._packages = Packages()
    for f in self.get_all('packages'):
      self._packages.add_file(f)

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
    repos = self._sections['repositories']
    return dict([(name, repos[name]) for name in repos])

  @property
  def post_install(self):
    # TODO: this should be a sequence of scripts in the same order as in suite
    # file
    return self._sections['post_install']

  @property
  def environment(self):
    # TODO: this should be a hash with proper values
    return self._sections['environment']

  #---------------------------------------------------------

  def __contains__(self, name):
    return name in self._sections[None]

  def __getitem__(self, name):
    if name in self._sections[None]:
      return self._sections[None][name]

  def get_all(self, name):
    return self._sections[None].get_all(name)

  def section(self, name):
    if section in self._sections:
      return self._sections[name]

  #---------------------------------------------------------

  def _read(self, f):
    lineno = 0
    section = None
    values = {}

    def error(line):
      if section is None:
        raise YBError('Invalid config line %d: %s', lineno, line, exit = 1)
      else:
        raise YBError('Invalid config line %d (section %s): %s',
                      lineno, section, line, exit = 1)

    while True:
      line = f.readline()
      lineno += 1
      if line == '':
        self._sections[section] = Section(values)
        return
      line = line.strip()

      if line == '' or line.startswith("#"):
        continue
      match = _CONFIG_LINE_RE.match(line)
      if match is None: error(line)

      groups = match.groupdict()

      if groups['section'] is not None:
        # new section
        self._sections[section] = Section(values)
        section = groups['section_name']
        if section == 'environment':
          values = {'keep': [], 'set': {}}
        else:
          values = {}
        continue

      if section == 'environment':
        # variable and env_keep are OK, rest is not
        if groups['variable'] is not None:
          if groups['name'] not in values['set']:
            values['set'][ groups['name'] ] = []
          values['set'][ groups['name'] ].append(groups['value'])
        elif groups['env_keep'] is not None:
          values['keep'].append(groups['env_name'])
        else:
          error(line)
        continue

      if section == 'repositories' and groups['set'] != '=':
        # variable has to be non-conditional in repositories
        error(line)

      # substitute ${suite} in groups['value']
      if section not in ('repositories', 'environment'):
        groups['value'] = groups['value'].replace('${suite}', self._suite)

      if groups['set'] == '?=' and \
         not os.path.exists(groups['value'].split(' ')[0]):
        # skip conditional if the file does not exist
        continue

      # any other section
      # variable is OK, rest is not
      if groups['name'] not in values:
        values[ groups['name'] ] = []
      values[ groups['name'] ].append(groups['value'])

#-----------------------------------------------------------------------------
# vim:ft=python
