#!/usr/bin/python3

#-----------------------------------------------------------------------------

# usage:
#   raise YBError('foo %d = "%s"', 10, 'nabla', exit = 3)
class YBError(Exception):
  def __init__(self, message, *args, **kwargs):
    self._fmt = message
    self._fmt_args = args
    self._exit = kwargs['exit']

  @property
  def message(self):
    return self._fmt % self._fmt_args

  @property
  def code(self):
    return self._exit

  def __str__(self):
    return str(self.message)

  def __unicode__(self):
    return unicode(self.message)

  def __repr__(self):
    return "<YBError (%d)>" % (self._exit)

#-----------------------------------------------------------------------------
# vim:ft=python3
