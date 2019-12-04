#!/usr/bin/python3

import os
import time
import shutil

target = os.environ['TARGET']
yumbootstrap_dir = os.environ['YUMBOOTSTRAP_DIR']
if os.environ['VERBOSE'] == 'true':
  print(time.strftime('[%T] ') + 'removing yumbootstrap directory from target')
shutil.rmtree(os.path.join(target, yumbootstrap_dir))
