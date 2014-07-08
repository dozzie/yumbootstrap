#!/usr/bin/python

import os
import time
import yumbootstrap.yum

yum = yumbootstrap.yum.Yum(chroot = os.environ['TARGET'])
if os.environ['VERBOSE'] == 'true':
  print time.strftime('[%T] ') + 'fixing RPM database in target directory'

# to prevent yumbootstrap.yum.Yum from running Python in chroot $TARGET
# one may specify `expected_rpmdb_dir' manually:
#   yum.fix_rpmdb(expected_rpmdb_dir = '/var/lib/rpm')
# if /usr/bin/db_load has a different name, this also could be provided:
#   yum.fix_rpmdb(db_load = '/usr/bin/db_load')
yum.fix_rpmdb()
