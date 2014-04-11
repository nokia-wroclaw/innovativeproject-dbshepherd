import pytest

class TestExample:
    
  def testMultiply2And3Properly(self):
    # given
    x = 2
    y = 3

    # when
    c = x * y
    
    # then
    assert c == 6
