#!/usr/bin/python

import os
import time
import yumbootstrap.yum

yum = yumbootstrap.yum.Yum(chroot = os.environ['TARGET'])
if os.environ['VERBOSE'] == 'true':
  print time.strftime('[%T] ') + 'fixing RPM database in target directory'

# older Red Hat/CentOS releases (<=5.2) don't have rpm.expandMacro() function;
# hardcode RPM DB location to skip using the possibly-non-existing function
yum.fix_rpmdb(expected_rpmdb_dir = '/var/lib/rpm')
