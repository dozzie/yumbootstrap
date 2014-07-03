#!/usr/bin/python

import os
from exceptions import YBError

READ  = object() # read from
WRITE = object() # write to

#-----------------------------------------------------------------------------

def check_error(cmd, code):
  if code in (None, 0):
    return
  if code & 0xff != 0:
    raise YBError('"%s" got signal %d', cmd, code, exit = 1)
  if code >> 8 != 0:
    raise YBError('"%s" exited with code %d', cmd, code >> 8, exit = 1)

#-----------------------------------------------------------------------------

# wrapper that dies with YBError on I/O error or on non-zero exit
class OutPipe:
  def __init__(self, cmd, pipe):
    self._cmd = cmd
    self._pipe = pipe

  def __del__(self):
    if self._pipe is not None:
      self.close()

  def write(self, data):
    try:
      return self._pipe.write(data)
    except IOError:
      self.close()
      # close() probably already raised an error, but if the command did
      # exit(0), let's die
      raise YBError('"%s" exited unexpectedly', self._cmd, exit = 1)

  def sync(self):
    try:
      return self._pipe.sync()
    except IOError:
      self.close()
      # close() probably already raised an error, but if the command did
      # exit(0), let's die
      raise YBError('"%s" exited unexpectedly', self._cmd, exit = 1)

  def close(self):
    pipe = self._pipe
    self._pipe = None
    try:
      ret = pipe.close()
      check_error(self._cmd, ret)
    except IOError:
      # it would be weird if I/O error happened on close(), but it could be
      # flushing buffers or something
      raise YBError('"%s" exited unexpectedly', self._cmd, exit = 1)

#-----------------------------------------------------------------------------

def run(command, chroot = None, pipe = None):
  # FIXME: make this more robust in presence of shell metacharacters
  if isinstance(command, (tuple, list)):
    sh_cmd = ' '.join(command)
    msg_cmd = command[0]
  else:
    sh_cmd = command
    msg_cmd = command.split(' ')[0]

  if chroot is not None:
    sh_cmd = 'chroot %s %s' % (chroot, sh_cmd)

  if pipe is None:
    ret = os.system(sh_cmd)
    check_error(msg_cmd, ret)
  elif pipe is READ:
    f = os.popen(sh_cmd, 'r')
    result = f.read()
    check_error(msg_cmd, f.close())
    return result
  elif pipe is WRITE:
    return OutPipe(msg_cmd, os.popen(sh_cmd, 'w'))

#-----------------------------------------------------------------------------
# vim:ft=python
