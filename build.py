#!/usr/bin/env python

import os, sys, subprocess, shutil

class Config:
  root = '.'
  src = '.'
  test = 'test'

########################################################

def removeDirsRecursive(root, filterExpr):
  for root, dirs, files in os.walk(root):
    for dir in filter(filterExpr, dirs):
      dirPath = os.path.join(root, dir)
      print 'removing : %s' % dirPath
      shutil.rmtree(dirPath)

def removeFilesRecursive(root, filterExpr):
  for root, dirs, files in os.walk(root):
    for file in filter(filterExpr, files):
      filePath = os.path.join(root, file)
      print 'removing : %s' % filePath
      os.remove(filePath)

########################################################

def test():
  return subprocess.call("py.test", shell=True)

def clean():
  removeDirsRecursive(Config.test, (lambda d: d == '__pycache__'))
  removeFilesRecursive(Config.src, (lambda f: f.endswith('.pyc') and f != 'build.pyc'))

def package():
  for root, dirs, files in os.walk(Config.src):
    if '.git' in dirs:
      dirs.remove('.git')
    for dir in dirs:
      initFile = os.path.join(root, dir, '__init__.py')
      if not os.path.isfile(initFile):
        print 'creating : %s' % initFile
        open(initFile, 'a').close()

def default():
  clean()
  package()
  test()

########################################################
def step(msg):
  span = '=' * ((80 - len(msg))/2)
  print ' '.join([span, msg, span])

if __name__ == "__main__":
  if len(sys.argv) > 1:
    for task in sys.argv[1:]:
      if task in locals():
        step(task)
        locals()[task]()
      else:
        print 'Error: task "%s" not found' % task
        sys.exit(1)
  else:
    default()
      
 



