'''
A fork from Tomas Basham

Copyright (c) 2015 Tomas Basham

MIT License

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from math import floor

import time
import sys
import threading

def rate_limited(period = 1, every = 1.0):
  '''
  Prevent a method from being called
  if it was previously called before
  a time widows has elapsed.

  :param period: The number of method invocation allowed over a time period. Must be greater than or equal to 1.
  :param every: A factor by which to dampen the time window (in seconds). Can be any number greater than 0.
  :return function: Decorated function that will forward method invocations if the time window has elapsed.
  '''
  frequency = abs(every) / float(clamp(period))
  def decorator(func):

    # To get around issues with function local scope
    # and reassigning variables, we wrap the time
    # within a list. When updating the value we're
    # not reassigning `last_called`, which would not
    # work, but instead reassigning the value at a
    # particular index.
    last_called = [0.0]

    #add thread safety
    lock = threading.RLock()

    def wrapper(*args, **kargs):
      with lock:
        elapsed = time.time() - last_called[0]
        left_to_wait = frequency - elapsed
        if left_to_wait > 0:
          time.sleep(left_to_wait)
        ret = func(*args, **kargs)
        last_called[0] = time.time()
        return ret
    return wrapper
  return decorator

def clamp(value):
  '''
  There must be at least 1 method invocation
  made over the time period. Make sure the
  value passed is at least one and it not
  a fraction of an invocation (wtf, like???)

  :param value: The number of method invocations.
  :return int: Clamped number of invocations.
  '''
  return max(1, min(sys.maxsize, floor(value)))

__all__ = [
  'rate_limited'
]