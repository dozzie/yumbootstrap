#!/usr/bin/python

import os
import sys
import bsddb

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

# poor man's BDB database dumper
# this function makes dependencies on host a little lower (BDB in Python
# should be the same as Yum/RPM use)
def db_dump(filename, outfile = sys.stdout):
  try:
    f = bsddb.hashopen(filename, 'r')
    db_type = "hash"
  except:
    f = bsddb.btopen(filename, 'r')
    db_type = "btree"

  outfile.write("VERSION=3\n") # magic
  outfile.write("format=bytevalue\n")
  outfile.write("type=%s\n" % (db_type))

  outfile.write("HEADER=END\n")
  for (key,value) in f.iteritems():
    outfile.write(" ")
    for c in key:
      outfile.write("%02x" % ord(c))
    outfile.write("\n")

    outfile.write(" ")
    for c in value:
      outfile.write("%02x" % ord(c))
    outfile.write("\n")
  outfile.write("DATA=END\n")

#-----------------------------------------------------------------------------

root = sys.argv[1]

import rpm
rpm_db = rpm.expandMacro('%{_dbpath}') # in chroot


#-----------------------------------------------------------------------------

for d in ('proc', 'sys', 'dev', 'dev/pts', 'etc'):
  mkdir(root, d)

touch(root, 'etc/fstab', text = '# empty fstab')
touch(root, 'etc/mtab')

# rpm --root $chroot --import gpg/RPM-GPG-KEY-CentOS-6
#
# setarch $arch \
#   yum -c yum/yum.conf -d 1 -e 1 -y --installroot=$chroot \
#     install ...
#
#   * "-d 1" is good for non-interactive run
#   * "-d 2" is good for interactive run (progress bars)
#   * "--nogpgcheck" if no 
#
# core:
#   * install       coreutils bash grep gawk basesystem rpm yum
#   * groupinstall  Core
# OS:
#   * install       less make mktemp vim-minimal
#   * groupinstall  Base
# release:
#   * install       redhat-release | centos-release
#
# BDB clean:
#   * yum install /usr/bin/db_load (should be pulled by yum, but just in case)
#   * db_dump($file_db, os.popen('chroot chroot db_load $file_db', 'w'))
#
# # note that this needs Yum installed already
# target_rpm_db = os.popen("chroot %s python -c 'import rpm; print rpm.expandMacro(\"%%{_dbpath}\")'" % (root)).read().strip()
#
# dbc = os.path.join(root, rpm_db.lstrip('/'))
# for p in os.listdir(dbc):
#   if p.startswith('.'): continue
#   in_file = os.path.join(dbc, p)
#   out_command = 'chroot %s db_load %s/%s' % ('chroot', target_rpm_db, p)
#   db_dump(in_file, os.popen(out_command, 'w'))
#

#-----------------------------------------------------------------------------
# vim:ft=python
