import logging
import time

#-----------------------------------------------------------------------------

class ProgressHandler(logging.Handler):
  def emit(self, record):
    print(time.strftime('[%T] ') + record.getMessage())

#-----------------------------------------------------------------------------
# vim:ft=python
