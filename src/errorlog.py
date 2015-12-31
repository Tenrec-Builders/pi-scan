import time

logfile = None

def openLog(mountPoint):
  global logfile
  if logfile is not None:
    logfile.close()
    logfile = None
  logfile = open(mountPoint + '/debug/error.log', 'w+')

def write(text):
  global logfile
  if logfile is not None:
    line = time.strftime('%Y-%m-%d %H:%M:%S') + ' -- ' + text + '\n'
    print line
    logfile.write(line)
    logfile.flush()

def closeLog():
  global logfile
  if logfile is not None:
    logfile.close()
    logfile = None
