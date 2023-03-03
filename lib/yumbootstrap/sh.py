#!/usr/bin/python3

import os
import subprocess
from exceptions import YBError

READ  = object() # read from
WRITE = object() # write to

#-----------------------------------------------------------------------------

def check_error(cmd, code):
  if code < 0:
    raise YBError('"%s" got signal %d', cmd, -code, exit = 1)
  if code > 0:
    raise YBError('"%s" exited with code %d', cmd, code, exit = 1)

#-----------------------------------------------------------------------------

# wrapper that dies with YBError on I/O error or on non-zero exit
class OutPipe:
  def __init__(self, cmd, proc):
    self._cmd = cmd
    self._proc = proc

  def __del__(self):
    if self._proc is not None:
      self.close()

  def write(self, data):
    try:
      return self._proc.stdin.write(data)
    except IOError:
      self.close()
      # close() probably already raised an error, but if the command did
      # exit(0), let's die
      raise YBError('"%s" exited unexpectedly', self._cmd, exit = 1)

  def sync(self):
    try:
      return self._proc.stdin.sync()
    except IOError:
      self.close()
      # close() probably already raised an error, but if the command did
      # exit(0), let's die
      raise YBError('"%s" exited unexpectedly', self._cmd, exit = 1)

  def close(self):
    proc = self._proc
    self._proc = None
    try:
      proc.communicate()
      check_error(self._cmd, proc.returncode)
    except IOError:
      # it would be weird if I/O error happened on close(), but it could be
      # flushing buffers or something
      raise YBError('"%s" exited unexpectedly', self._cmd, exit = 1)

#-----------------------------------------------------------------------------

def run(command, chroot = None, pipe = None, env = None):
  if not isinstance(command, (tuple, list)):
    command = command.split(' ')

  if chroot is not None:
    def chroot_fun(*args):
      os.chdir(chroot)
      os.chroot('.')
  else:
    chroot_fun = None

  if pipe is None:
    proc = subprocess.Popen(
      command,
      env = env,
      stdin = open('/dev/null'),
      preexec_fn = chroot_fun,
    )
    proc.wait()
    check_error(command[0], proc.returncode)
  elif pipe is READ:
    proc = subprocess.Popen(
      command,
      env = env,
      stdin = open('/dev/null'),
      stdout = subprocess.PIPE,
      preexec_fn = chroot_fun,
    )
    (result,_) = proc.communicate()
    check_error(command[0], proc.returncode)
    return result
  elif pipe is WRITE:
    proc = subprocess.Popen(
      command,
      env = env,
      stdin = subprocess.PIPE,
      preexec_fn = chroot_fun,
    )
    return OutPipe(command[0], proc)

#-----------------------------------------------------------------------------
# vim:ft=python3
