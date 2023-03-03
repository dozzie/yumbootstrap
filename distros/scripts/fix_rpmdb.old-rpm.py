#!/usr/bin/python3

import os
import time
import logging
import yumbootstrap.yum
import yumbootstrap.log

#-----------------------------------------------------------------------------

logger = logging.getLogger()
logger.addHandler(yumbootstrap.log.ProgressHandler())
if os.environ['VERBOSE'] == 'true':
  logger.setLevel(logging.INFO)

#-----------------------------------------------------------------------------

yum = yumbootstrap.yum.Yum(chroot = os.environ['TARGET'])

# older Red Hat/CentOS releases (<=5.2) don't have rpm.expandMacro() function;
# hardcode RPM DB location to skip using the possibly-non-existing function
yum.fix_rpmdb(expected_rpmdb_dir = '/var/lib/rpm')

#-----------------------------------------------------------------------------
# vim:ft=python3
