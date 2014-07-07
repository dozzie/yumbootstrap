#!/usr/bin/python

import os
import time
import yumbootstrap.yum

yum = yumbootstrap.yum.Yum(chroot = os.environ['TARGET'])
if os.environ['VERBOSE'] == 'true':
  print time.strftime('[%T] ') + 'fixing RPM database in target directory'
yum.fix_rpmdb()
