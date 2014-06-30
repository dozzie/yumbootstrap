#!/usr/bin/python

import os

READ  = object() # read from
WRITE = object() # write to

#-----------------------------------------------------------------------------

def run(command, chroot = None, pipe = None):
  # FIXME: make this more robust in presence of shell metacharacters
  if isinstance(command, (tuple, list)):
    sh_cmd = ' '.join(command)
  else:
    sh_cmd = command

  if chroot is not None:
    sh_cmd = 'chroot %s %s' % (chroot, sh_cmd)

  if pipe is None:
    os.system(sh_cmd)
  elif pipe is READ:
    return os.popen(sh_cmd, 'r')
  elif pipe is WRITE:
    return os.popen(sh_cmd, 'w')

#-----------------------------------------------------------------------------
# vim:ft=python
