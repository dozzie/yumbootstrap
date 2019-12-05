import os
import stat

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
    open(new_file, 'a')

def mkchardev(*path, **kwargs):
  new_file = os.path.join(*path)
  mkdir(os.path.dirname(new_file))
  major = kwargs["major"]
  minor = kwargs["minor"]
  mode = kwargs.get("mode", 0o666)

  try:
    info = os.stat(new_file)
  except OSError:
    info = None # assume that this was ENOENT
  if info is not None and not \
     (stat.S_ISCHR(info.st_mode) and info.st_rdev == os.makedev(major, minor)):
    # file exists, but its type or major/minor are wrong
    os.unlink(new_file) # FIXME: this will blow up on a directory
    info = None

  if info is not None:
    # character device with correct major and minor numbers; check its
    # permissions
    if stat.S_IMODE(info.st_mode) != mode:
      os.chmod(new_file, mode)
    return

  # at this point, the requested file doesn't exist
  try:
    old_umask = os.umask(0)
    os.mknod(new_file, mode | stat.S_IFCHR, os.makedev(major, minor))
  finally:
    os.umask(old_umask)

#-----------------------------------------------------------------------------
# vim:ft=python
