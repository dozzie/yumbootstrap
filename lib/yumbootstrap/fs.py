#!/usr/bin/python

import os

#-----------------------------------------------------------------------------

def mkdir(*path):
  new_dir = os.path.join(*path)
  if new_dir == '':
    return
  if not os.path.exists(new_dir):
    os.makedirs(new_dir)

def touch(*path, **kwargs):
  new_file = os.path.join(*path)
  mkdir(os.path.dirname(new_file))
  if 'payload' in kwargs:
    open(new_file, 'w').write(kwargs['payload'])
  elif 'text' in kwargs and kwargs['text'].endswith('\n'):
    open(new_file, 'w').write(kwargs['text'])
  elif 'text' in kwargs:
    open(new_file, 'w').write(kwargs['text'] + '\n')
  else:
    open(new_file, 'w')

#-----------------------------------------------------------------------------
# vim:ft=python
