import os, re, sys, traceback
import errorlog
import subprocess

zoomToFactor = {
  'Min Zoom': 0.0,
  '0.5':      0.05,
  '1':        0.1,
  '1.5':      0.15,
  '2':        0.2,
  '2.5':      0.25,
  '3':        0.3,
  '3.5':      0.35,
  '4':        0.4,
  '4.5':      0.45,
  '5':        0.5,
  '5.5':      0.55,
  '6':        0.6,
  '6.5':      0.65,
  '7':        0.7,
  '7.5':      0.75,
  '8':        0.8,
  '8.5':      0.85,
  '9':        0.9,
  '9.5':      0.95,
  'Max Zoom': 1.0
  }

shutterToFactor = {
  '1/250': 1/250.0,
  '1/125': 1/125.0,
  '1/60':  1/60.0,
  '1/30':  1/30.0,
  '1/25':  1/25.0,
  '1/20':  1/20.0,
  '1/18':  1/18.0,
  '1/16':  1/16.0,
  '1/15':  1/15.0,
  '1/14':  1/14.0,
  '1/12':  1/12.0,
  '1/10':  1/10.0,
  '1/8':   1/8.0,
  '1/6':   1/6.0,
  '1/4':   1/4.0,
  '1/3':   1/3.0,
  '1/2':   1/2.0,
  '1/1':   1/1.0
  }

class GphotoInfo:
  def __init__(self, usb_port, serial_num):
    self.gphoto = True
    self.usb_port = usb_port
    self.serial_num = serial_num
    self.chdk_api = None

def search():
  result = []
  try:
    cameraList = subprocess.check_output(['gphoto2', '--auto-detect'])
    result = parseCameras(cameraList)
  except Exception as e:
    errorlog.write('Failed to search: ' + str(e.args) + '\n' + traceback.format_exc())
  return result

def parseCameras(text):
  result = []
  lines = text.split('\n')
  for line in lines[2:]:
    if line != '':
      test = re.compile('(usb:[0-9,]+)')
      match = test.search(line)
      if match is not None:
        usb_port = match.group(1)
        serial_num = getConfig(usb_port, '/main/status/serialnumber')
        result.append(GphotoInfo(usb_port, serial_num))
      else:
        errorlog.write('Failed to parse camera line: ' + line);
  return result

class Camera:
  def __init__(self, info, config):
    self.whitebalance = 3
    #self.device = chdkptp.ChdkDevice(info)
    self.port = info.usb_port
    self.zoom_steps = None
    self.config = config
    self.isReady = False
    self.message = ''
    self.position = 'odd'
    self.debugCount = 3
    self.debugFail = ''
    
    # TODO Warning about unsupported cameras?

  def log(self, message):
    errorlog.write(self.position + ' camera: ' + message + ' -- self.message: ' + self.message)

  ###########################################################################

  def prepare(self):
    success = False
    if self.isReady:
      success = True
    else:
      try:
        if self.is_connected():
          #self.prepare_mode()
          #self.prepare_flash()
          #self.prepare_zoom()
          #self.prepare_iso()
          #self.prepare_aperture()
          #self.prepare_shutter()
          #self.prepare_whitebalance()
          #self.prepare_quality()
          #self.prepare_resolution()
          success = True
          self.isReady = True
        else:
          self.message = 'Lost connection before prepare capture'
          self.log('Failed while preparing: ' + self.message)
      except Exception as e:
        self.log('Failed while preparing: ' + str(e.args) + '\n' + traceback.format_exc())
    return success

  def prepare_mode(self):
    pass

  def prepare_zoom(self):
    pass

  def prepare_aperture(self):
    self.message = 'Failed to set aperture'
    setConfig(self.port, '/main/capturesettings/f-number', 'f/8')

  def prepare_iso(self):
    self.message = 'Failed to set ISO'
    setConfig(self.port, '/main/imgsettings/iso', '100')
  
  # Set whitebalance to Tungsten
  def prepare_whitebalance(self):
    self.message = 'Failed to set white balance'
    setConfig(self.port, '/main/imgsettings/whitebalance', 'Tungsten')

  def prepare_flash(self):
    self.message = 'Failed to disable flash'
    pass

  def prepare_quality(self):
    self.message = 'Failed to set quality'
    setConfig(self.port, '/main/capturesettings/imagequality2', 'JPEG Fine')

  def prepare_resolution(self):
    self.message = 'Failed to set resolution'
    setConfig(self.port, '/main/imgsettings/imagesize', 'Large')
  
  ###########################################################################

  def is_connected(self):
    return True

  def refocus(self):
    success = False
    try:
      if self.is_connected():
        self.message = 'Error during refocus'
        success = True
      else:
        self.message = 'Lost connection before refocus'
        self.log('Failed to refocus: ' + self.message)
    except Exception as e:
      self.log('Failed to refocus: ' + str(e.args) + '\n' + traceback.format_exc())
    return success

  def unlockFocus(self):
    success = False
    try:
      if self.is_connected():
        self.message = 'Error during unlock focus'
        success = True
      else:
        self.message = 'Lost connection before unlock focus'
        self.log('Failed to unlock focus: ' + self.message)
    except Exception as e:
      self.log('Failed to refocus: ' + str(e.args) + '\n' + traceback.format_exc())
    return success
    
  def connect(self):
    success = False
    try:
      self.message = 'Failed during reconnect'
      success = True
    except Exception as e:
      self.log('Failed to connect: ' + str(e.args) + '\n' + traceback.format_exc())
    return success


  ###########################################################################

  def calculate_zoom(self):
    if self.zoom_steps is None:
      self.zoom_steps = self.device.lua_execute('sleep(50); return get_zoom_steps()')
    choice = '5'
    if 'zoom' in self.config:
      choice = self.config['zoom']
    factor = 0.5
    if choice in zoomToFactor:
      factor = zoomToFactor[choice]
    return max(round(self.zoom_steps * factor) - 1, 0)

  ###########################################################################

  def calculate_shutter(self):
    choice = '1/15'
    if 'shutter' in self.config:
      choice = self.config['shutter']
    factor = 1/15.0
    if choice in shutterToFactor:
      factor = shutterToFactor[choice]
    return factor
  
  ###########################################################################

  def capture(self, filename):
    result = None
    if self.debugFail == self.position:
      self.debugCount -= 1
      if self.debugCount <= 0:
        self.debugCount = 4
        self.message = 'Testing failure'
        return None
    try:
      self.message = 'Failed before shooting'
      if self.isReady and self.is_connected():
        self.message = 'Failed while shooting'
        captureAndDownload(self.port, filename)
        return filename
    except Exception as e:
      self.log('Failed to capture: ' + str(e.args) + '\n' + traceback.format_exc())
    return result

  ###########################################################################

  def getRomLog(self, position, path):
    pass

  ###########################################################################

  def beepFail(self):
    try:
      if self.is_connected():
        pass
    except Exception as e:
      self.log('Failed to beep: ' + str(e) + ' ' + str(e.args) + '\n' + traceback.format_exc())

  ###########################################################################
      
  def turnOff(self):
    try:
      if self.is_connected():
        pass
    except Exception as e:
      self.log('Failed to power off: ' + str(e) + ' ' + str(e.args) + '\n' + traceback.format_exc())

  ###########################################################################

def getConfig(usb_port, key):
  raw = subprocess.check_output(['gphoto2',
                                 '--port=' + usb_port,
                                 '--get-config=' + key])
  test = re.compile('Current: ([^\n]+)')
  match = test.search(raw)
  if match is not None:
    return match.group(1)
  else:
    return None

def setConfig(usb_port, key, value):
  raw = subprocess.check_output(['gphoto2',
                                 '--port=' + usb_port,
                                 '--set-config=' + key + '=' + value])
  return None

def captureAndDownload(usb_port, key):
  raw = subprocess.check_output(['gphoto2',
                                 '--port=' + usb_port,
                                 '--capture-image-and-download',
                                 '--no-keep',
                                 '--force-overwrite',
                                 '--filename=' + key + '.%C'])
