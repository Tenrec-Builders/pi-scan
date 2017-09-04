from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ObjectProperty, ListProperty
from kivy.vector import Vector
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics.transformation import Matrix
import camera_thread, stick, camera_chdk, camera_gphoto, preview, errorlog, preview_thread
import os, json, string, re, traceback, errno
import wiringpi

version = '1.5'
debug = False

odd = None
even = None
config = {}
gphoto = False

#########################################################################################

class CameraSide:
  def __init__(self, thread, position):
    self.thread = thread
    self.config = {}
    #if position == 'even':
    #  self.config['position'] = 'even'
    self.position = position
    self.camera = None
    self.serial = None
    self.code = camera_thread.COMPLETE
    self.message = 'Lost Connection to Camera'
    self.raw = None
    self.filename = None
    self.preview = preview.Preview()

  def start(self):
    self.thread.start()
    self.preview.start()
    self.preview.position(self.position)

  def reset(self, info):
    if info.chdk_api is not None:
      self.serial = info.serial_num
      self.camera = camera_chdk.Camera(info, self.config)
    else:
      self.serial = info.serial_num
      self.camera = camera_gphoto.Camera(info, self.config)
    self.camera.position = self.position
    self.camera.connect()

  def capture(self, newFilename, mountPoint, shouldRefocus):
    # Set the filename we will later save to using .jpg for CHDK cameras
    self.filename = newFilename + '.jpg'
    self.scan = None
    self.code = camera_thread.WAITING 
    self.message = 'Lost Connection to Camera'
    # Pass in a .jpg-less filename for gphoto cameras because they add
    # on .jpg automatically.
    self.thread.beginCapture(self.camera, shouldRefocus, mountPoint + newFilename)

  def save(self, mountPoint):
    #print 'Camera: ', self.position, ' saving image: ', self.filename
    if self.raw is not None and not isinstance(self.raw, basestring) and self.filename is not None and self.code == camera_thread.COMPLETE:
      fp = open(mountPoint + self.filename, 'w')
      fp.write(self.raw)
      fp.close()

  def update(self):
    if self.code == camera_thread.WAITING:
      result = self.thread.checkResult()
      self.code = result.code
      self.message = result.message
      if result.code == camera_thread.COMPLETE:
        self.raw = result.scan
      else:
        self.raw = None
    return self.code != camera_thread.WAITING

  def setPreview(self):
    self.preview.setImage(self.raw)

  def updatePreview(self):
    return self.preview.update()

  def showPreview(self, root):
    self.preview.redisplay(root)

  def clearDisplay(self, root):
    root.clear_widgets()

  def resetPosition(self, newPosition):
    self.position = newPosition
    self.preview.position(newPosition)
    self.camera.position = newPosition

  def loadConfig(self, source):
    mine = {}
    if self.serial in source:
      mine = source[self.serial]
    for key in mine.keys():
      self.config[key] = mine[key]

  def saveConfig(self, dest):
    mine = {}
    if self.serial in dest:
      mine = dest[self.serial]
    for key in self.config.keys():
      mine[key] = self.config[key]
    dest[self.serial] = mine

#########################################################################################

def loadConfig(mountPoint):
  global config
  config = {}
  filename = mountPoint + '/pi-scan.conf'
  jsonText = ''
  try:
    fp = open(filename, 'r')
    jsonText = fp.read()
    fp.close()
    config = json.loads(jsonText)
    odd.loadConfig(config)
    even.loadConfig(config)
  except Exception as e:
    errorlog.write('Failed to read config file: ' + str(e) + ': ' + str(e.args) + '\n\n' + jsonText)

#########################################################################################

def saveConfig(mountPoint):
  filename = mountPoint + '/pi-scan.conf'
  jsonText = json.dumps(config, sort_keys=True, indent=2, separators=(',', ': '))
  try:
    fp = open(filename, 'w')
    fp.write(jsonText)
    fp.close()
  except Exception as e:
    errorlog.write('Failed to write config file: ' + str(e) + ': ' + str(e.args))

#########################################################################################

def updateConfig():
  global config
  if odd.serial not in config:
    config[odd.serial] = {}
  odd.saveConfig(config)
  config[odd.serial]['position'] = 'odd'
  if even.serial not in config:
    config[even.serial] = {}
  even.saveConfig(config)
  config[even.serial]['position'] = 'even'

#########################################################################################

def configureSides():
  if (odd.serial in config and
      'position' in config[odd.serial] and
      config[odd.serial]['position'] != 'odd'):
    swapSides()
  elif (even.serial in config and
        'position' in config[even.serial] and
        config[even.serial]['position'] != 'even'):
    swapSides()
  else:
    updateConfig()
  
#########################################################################################

def swapSides():
  global odd, even
  tmp = odd
  odd = even
  even = tmp
  odd.resetPosition('odd')
  even.resetPosition('even')
  updateConfig()

#########################################################################################

# Returns a tuple of (oddFound, evenFound, tooManyCameras)
def checkCameras():
  global gphoto
  oddFound = False
  evenFound = False
  tooManyCameras = False
  cameraList = camera_chdk.search()
  if len(cameraList) == 0:
    cameraList = camera_gphoto.search()
    gphoto = True
  else:
    gphoto = False
  #cameraList = [0,0]
  try:
    if len(cameraList) > 2:
      tooManyCameras = True
    else:
      for item in cameraList:
        if item.serial_num == odd.serial:
          if odd.camera is None or not odd.camera.is_connected():
            odd.reset(item)
        elif item.serial_num == even.serial:
          if even.camera is None or not even.camera.is_connected():
            even.reset(item)
        elif odd.camera is None or not odd.camera.is_connected():
          odd.reset(item)
        elif even.camera is None or not even.camera.is_connected():
          even.reset(item)
      oddFound = odd.camera is not None and odd.camera.is_connected()
      evenFound = even.camera is not None and even.camera.is_connected()
  except Exception as e:
    errorlog.write('Failed to reset cameras: ' + str(e.args) + '\n' + traceback.format_exc())
  return (oddFound, evenFound, tooManyCameras)

#########################################################################################

def checkForDisconnected(manager):
  # Proactively detect when cameras are disconnected or crash
  if odd.camera is None or not odd.camera.is_connected():
    odd.code = camera_thread.DISCONNECTED
    odd.message = 'Lost Connection to Camera'
    errorlog.write('odd camera: ' + odd.message)
  if even.camera is None or not even.camera.is_connected():
    even.code = camera_thread.DISCONNECTED
    even.message = 'Lost Connection to Camera'
    errorlog.write('even camera: ' + even.message)
  if odd.code == camera_thread.DISCONNECTED or even.code == camera_thread.DISCONNECTED:
    manager.capturePage = 'focus-camera'
    manager.transition.direction = 'left'
    manager.current = 'debug'

#########################################################################################

def handleKeyPress(key, options):
  if key in options:
    func = options[key]
    #if not button.disabled:
    func()

#########################################################################################

class OptionSelect(RelativeLayout):
  title = StringProperty('Title')
  key = StringProperty('key')
  choice = ListProperty([])
  default = StringProperty('value')
  help = StringProperty('Help Message')
  manager = ObjectProperty(None, allownone=True)

  def keyPress(self, key):
    handleKeyPress(key,
                   { '1': self.done,
                     '3': self.test })
    self.evenControl.keyPress(key)
    self.oddControl.keyPress(key)
    self.preview.keyPress(key)

  def update(self, dt):
    checkForDisconnected(self.manager)

  def on_pre_enter(self, manager):
    try:
      self.manager = manager
      self.titleLabel.text = self.title
      self.noPreviewLabel.text = self.help
      self.updateControl(self.evenControl, even)
      self.updateControl(self.oddControl, odd)

      if self.manager.newPreview:
        self.manager.newPreview = False
        self.noPreviewLabel.opacity = 0.0
        self.preview.opacity = 1.0
      else:
        self.noPreviewLabel.opacity = 1.0
        self.preview.opacity = 0.0
    except Exception as e:
      handleCrash(e)

  def updateControl(self, control, side):
    text = self.default
    for value in self.choices:
      if self.key in side.config and side.config[self.key] == value:
        text = value
    control.set(text, self.choices)
    #control.option_cls.height = 32

  def test(self):
    try:
      odd.config[self.key] = self.oddControl.get()
      odd.camera.isReady = False
      odd.capture('/debug/preview-odd', self.manager.mountPoint, camera_thread.AUTO_FOCUS)
      even.config[self.key] = self.evenControl.get()
      even.camera.isReady = False
      even.capture('/debug/preview-even', self.manager.mountPoint, camera_thread.AUTO_FOCUS)
      self.manager.capturePage = self.manager.current
      self.manager.mustPreview = True
      self.manager.transition.direction = 'left'
      self.manager.current = 'capture-wait'
    except Exception as e:
      handleCrash(e)

  def done(self):
    try:
      odd.config[self.key] = self.oddControl.get() 
      even.config[self.key] = self.evenControl.get()
      odd.saveConfig(config)
      even.saveConfig(config)
      saveConfig(self.manager.mountPoint)
      self.manager.transition.direction = 'left'
      self.manager.current = 'configure-camera'
    except Exception as e:
      handleCrash(e)

#########################################################################################

class SettingPicker(BoxLayout):
  nextKey = StringProperty('.')
  previousKey = StringProperty(',')

  def set(self, val, options):
    self.options = options
    self.displayText.text = val
    self.updateButtons()
    self.previousButton.text = '< (' + self.previousKey + ')'
    self.nextButton.text = '> (' + self.nextKey + ')'

  def get(self):
    return self.displayText.text

  def goNext(self):
    if self.displayText.text in self.options:
      index = self.options.index(self.displayText.text)
      if index < len(self.options) - 1:
        index += 1
      self.displayText.text = self.options[index]
    self.updateButtons()

  def goPrevious(self):
    if self.displayText.text in self.options:
      index = self.options.index(self.displayText.text)
      if index > 0:
        index -= 1
      self.displayText.text = self.options[index]
    self.updateButtons()

  def updateButtons(self):
    previousDisabled = True
    nextDisabled = True
    if self.displayText.text in self.options:
      index = self.options.index(self.displayText.text)
      if index > 0:
        previousDisabled = False
      if index < len(self.options) - 1:
        nextDisabled = False
    self.previousButton.disabled = previousDisabled
    self.nextButton.disabled = nextDisabled

  def keyPress(self, key):
    handleKeyPress(key,
                   { self.previousKey: self.goPrevious,
                     self.nextKey: self.goNext })

#########################################################################################

class ScanRoot(ScreenManager):
  #scanPath = StringProperty('')
  #updateScanChooser = BooleanProperty(False)
  hasTransitioned = BooleanProperty(False)
  newCapture = BooleanProperty(False)
  newPreview = BooleanProperty(False)
  hasFocus = BooleanProperty(False)
  capturePage = StringProperty('')
  mustPreview = BooleanProperty(False)

  def __init__(self, a=1.0, **kwargs):
    super(ScanRoot, self).__init__(**kwargs)
    self.mountPoint = None

#########################################################################################

class StartScreen(Screen):
  syncWait = NumericProperty(0.0)

  def update(self, dt):
    title = 'Pi Scan ' + version
    if debug:
      title += ' (debug)'
    self.titleLabel.text = title
    errorlog.closeLog()
    maxWait = 60
    count = stick.searchAndUnmount(self.syncWait > maxWait)
    if count == 0:
      self.syncWait = 0.0
      self.powerOff.text = 'All disks ejected. Ok to power off or disconnect disk.'
    else:
      timeLeft = maxWait - self.syncWait
      waitString = 'Force Ejecting now. '
      if timeLeft > 0:
        waitString = 'Syncing to disk. Waiting %0.0f more seconds before force ejecting.' % timeLeft
      self.syncWait += dt
      self.powerOff.text = waitString + ' [color=ff3333]Do not power off.[/color]'
    self.manager.mountPoint = None
    if ((odd.camera is not None and odd.camera.is_connected()) or
        (even.camera is not None and even.camera.is_connected())) and not gphoto:
      self.cameraOffButton.opacity = 1.0
    else:
      self.cameraOffButton.opacity = 0.0

  def on_pre_leave(self):
    try:
      self.powerOff.text = ''
      self.manager.hasTransitioned = True
    except Exception as e:
      handleCrash(e)

  def keyPress(self, key):
    handleKeyPress(key,
                   { '1': self.beginAction,
                     '2': self.turnOffCameras,
                     '9': self.quitAction })

  def beginAction(self):
    self.manager.transition.direction = 'left'
    self.manager.current = 'configure-disk'

  def quitAction(self):
    os.system('killall run-pi-scan.sh python')
    exit()

  def turnOffCameras(self):
    if odd.camera is not None:
      odd.camera.turnOff()
      odd.camera = None
    if even.camera is not None:
      even.camera.turnOff()
      even.camera = None

#########################################################################################

class ConfigureDiskScreen(Screen):
  waitCount = NumericProperty(0.0)

  def update(self, dt):
    sticks = stick.search()
    if len(sticks) == 0:
      self.diskStatus.text = '[color=ff3333]No Storage Found.[/color] Insert removable storage to continue (USB drive or SD card).'
      self.diskNext.disabled = True
      self.spinner.opacity = 1.0
    elif len(sticks) == 1:
      mountPoint = sticks[0].get_mount_point()
      #self.manager.mountPoint = string.strip(.encode('ascii'), '\0')
      if mountPoint is None:
        mountPoint = sticks[0].mount()
      #self.manager.mountPoint = 'test'
      if mountPoint is None:
        self.manager.mountPoint = None
        self.diskStatus.text = 'Could not mount drive. Try removing and re-inserting it.'
        self.diskNext.disabled = True
        self.spinner.opacity = 1.0
        self.upgradeButton.opacity = 0.0
        self.upgradeButton.disabled = True
      else:
        self.manager.mountPoint = string.strip(mountPoint.encode('ascii'), '\0')
        failMessage = self.makeDirs()
        if failMessage is None:
          self.diskStatus.text = 'Storage Found. Click next to continue.'
          self.diskNext.disabled = False
          self.spinner.opacity = 0.0
          if self.getUpgrade() is not None:
            self.upgradeButton.opacity = 1.0
            self.upgradeButton.disabled = False
          else:
            self.upgradeButton.opacity = 0.0
            self.upgradeButton.disabled = True
        else:
          self.diskStatus.text = 'Storage Error: ' + failMessage
          self.diskNext.disabled = True
          self.spinner.opacity = 1.0
          self.upgradeButton.opacity = 0.0
          self.upgradeButton.disabled = True
    else:
      self.diskStatus.text = '[color=ff3333]Multiple Drives Found.[/color] Disconnect all but one drive to continue.'
      self.diskNext.disabled = True
      self.spinner.opacity = 1.0
      self.upgradeButton.opacity = 0.0
      self.upgradeButton.disabled = True

  def keyPress(self, key):
    handleKeyPress(key,
                   { '1': self.diskNextAction,
                     '9': self.backAction,
                     '2': self.upgradeAction })

  def on_pre_enter(self):
    try:
      self.diskStatus.text = 'Searching for storage...'
      self.diskNext.disabled = True
      self.upgradeButton.opacity = 0.0
      self.upgradeButton.disabled = True
    except Exception as e:
      handleCrash(e)

  def makeDirs(self):
    errorMessage = None
    try:
      os.mkdir(self.manager.mountPoint + '/debug')
    except OSError as e:
      errorMessage = self.makeDirError(e)
    if errorMessage is None:
      try:
        os.mkdir(self.manager.mountPoint + '/images')
      except OSError as e:
        errorMessage = self.makeDirError(e)
    return errorMessage

  def makeDirError(self, e):
    result = None
    if e.errno != errno.EEXIST:
      result = e.strerror
    return result

  def getUpgrade(self):
    result = None
    versionPattern = re.compile('^([0-9]+)\.([0-9]+)$')
    match = versionPattern.search(version)
    versionMajor = int(match.group(1))
    versionMinor = int(match.group(2))
    largestMajor = versionMajor
    largestMinor = versionMinor
    pattern = re.compile('^pi-scan-update-([0-9]+)\.([0-9]+)\.archive$')
    filenames = os.listdir(self.manager.mountPoint)
    for name in filenames:
      match = pattern.search(name)
      if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        if (major > largestMajor or
            major == largestMajor and minor > largestMinor):
          largestMajor = major
          largestMinor = minor
    if (largestMajor > versionMajor or
        largestMajor == versionMajor and largestMinor > versionMinor):
      result = (self.manager.mountPoint + '/' +
                'pi-scan-update-' + str(largestMajor) + '.' + str(largestMinor) +
                '.archive')
    return result

  def diskNextAction(self):
    if not self.diskNext.disabled:
      self.manager.transition.direction = 'left'
      self.manager.current = 'configure-camera'

  def backAction(self):
    self.manager.transition.direction = 'right'
    self.manager.current = 'start'

  def upgradeAction(self):
    try:
      upgradeFile = self.getUpgrade()
      if upgradeFile is not None:
        self.upgradeButton.disabled = True
        os.system('sudo mount -o remount,rw /')
        os.system('unzip -o ' + upgradeFile + ' -d /home_org/pi/')
        os.system('sudo mount -o remount,ro /')
        os.system('unzip -o ' + upgradeFile + ' -d /home/pi/')
        exit(0)
        #os.system('sudo reboot')
    except Exception as e:
      handleCrash(e)

#########################################################################################

class ConfigureCameraScreen(Screen):
  def update(self, dt):
    if (odd.camera is None or
        even.camera is None or
        not odd.camera.is_connected() or
        not even.camera.is_connected()):
      (oddFound, evenFound, tooManyFound) = checkCameras()
      errorText = ' If a camera shows the date/time screen, unplug the USB cable from it, set the date/time via the keypad, then plug it back in.'
      if tooManyFound:
        self.cameraLabel.text = 'Too many cameras found. Disconnect until there are only two.'
        self.cameraNext.disabled = True
        self.searchingLayout.opacity = 1.0
        self.foundLayout.opacity = 0.0
      elif oddFound and evenFound:
        #self.cameraLabel.text = 'Found two cameras. Click next to continue.'
        self.cameraNext.disabled = False
        self.searchingLayout.opacity = 0.0
        self.foundLayout.opacity = 1.0
        self.updateFound()
      elif not oddFound and not evenFound:
        self.cameraLabel.text = 'No cameras found. Plug in or turn on the cameras.' + errorText
        self.cameraNext.disabled = True
        self.searchingLayout.opacity = 1.0
        self.foundLayout.opacity = 0.0
      elif not oddFound:
        self.cameraLabel.text = 'Odd camera not found. Plug in or turn it on.' + errorText
        self.cameraNext.disabled = True
        self.searchingLayout.opacity = 1.0
        self.foundLayout.opacity = 0.0
      elif not evenFound:
        self.cameraLabel.text = 'Even camera not found. Plug in or turn it on.' + errorText
        self.cameraNext.disabled = True
        self.searchingLayout.opacity = 1.0
        self.foundLayout.opacity = 0.0

  def updateFound(self):
    if gphoto:
      self.foundLabel.text = 'Found gphoto cameras. Remember to set all camera settings including zoom and focus before proceeding.'
      self.zoomButton.opacity = 0.0
      self.shutterButton.opacity = 0.0
      self.debugButton.opacity = 0.0
    else:
      self.foundLabel.text = 'Found two CHDK cameras. Click next to continue.'
      self.zoomButton.opacity = 1.0
      self.shutterButton.opacity = 1.0
      self.debugButton.opacity = 1.0
        
  def keyPress(self, key):
    handleKeyPress(key,
                   { '1': self.nextAction,
                     '2': self.zoom,
                     '3': self.shutter,
                     '4': self.debug,
                     '9': self.backAction })

  def on_pre_enter(self):
    try:
      errorlog.openLog(self.manager.mountPoint)
      self.cameraLabel.text = 'Searching for cameras...'
      if (odd.camera is None or
          even.camera is None or
          not odd.camera.is_connected() or
          not even.camera.is_connected()):
        self.cameraNext.disabled = True
        self.searchingLayout.opacity = 1.0
        self.foundLayout.opacity = 0.0
      else:
        self.cameraNext.disabled = False
        self.searchingLayout.opacity = 0.0
        self.foundLayout.opacity = 1.0
    except Exception as e:
      handleCrash(e)

  def zoom(self):
    try:
      loadConfig(self.manager.mountPoint)
      configureSides()
      self.manager.transition.direction = 'left'
      self.manager.current = 'zoom-camera'
    except Exception as e:
      handleCrash(e)

  def shutter(self):
    try:
      loadConfig(self.manager.mountPoint)
      configureSides()
      self.manager.transition.direction = 'left'
      self.manager.current = 'shutter-camera'
    except Exception as e:
      handleCrash(e)

  def nextAction(self):
    try:
      if not self.cameraNext.disabled:
        loadConfig(self.manager.mountPoint)
        configureSides()
        self.manager.transition.direction = 'left'
        self.manager.current = 'focus-camera'
    except Exception as e:
      handleCrash(e)

  def backAction(self):
    try:
      self.manager.transition.direction = 'right'
      self.manager.current = 'configure-disk'
    except Exception as e:
      handleCrash(e)

  def debug(self):
    try:
      self.manager.transition.direction = 'left'
      self.manager.current = 'debug'
    except Exception as e:
      handleCrash(e)

#########################################################################################

class PreviewOutside(RelativeLayout):
  def zoomIn(self):
    try:
      self.scatter.scale = self.scatter.scale * 1.2
    except Exception as e:
      handleCrash(e)

  def zoomOut(self):
    try:
      self.scatter.scale = self.scatter.scale / 1.2
    except Exception as e:
      handleCrash(e)

  def zoomZero(self):
    try:
      zeroScale = self.odd.height / self.scatter.height
      oldScale = self.scatter.scale
      self.scatter.transform = Matrix()
      self.scatter.scale = zeroScale
    except Exception as e:
      handleCrash(e)

  def moveUp(self):
    try:
      self.scatter.apply_transform(Matrix().translate(x=0,y=-100/self.scatter.scale,z=0))
    except Exception as e:
      handleCrash(e)

  def moveDown(self):
    try:
      self.scatter.apply_transform(Matrix().translate(x=0,y=100/self.scatter.scale,z=0))
    except Exception as e:
      handleCrash(e)

  def moveLeft(self):
    try:
      self.scatter.apply_transform(Matrix().translate(x=100/self.scatter.scale,y=0,z=0))
    except Exception as e:
      handleCrash(e)

  def moveRight(self):
    try:
      self.scatter.apply_transform(Matrix().translate(x=-100/self.scatter.scale,y=0,z=0))
    except Exception as e:
      handleCrash(e)

  def keyPress(self, key):
    handleKeyPress(key,
                   { '+': self.zoomIn,
                     '=': self.zoomIn,
                     '-': self.zoomOut,
                     '_': self.zoomOut,
                     '0': self.zoomZero,
                     ')': self.zoomZero,
                     'w': self.moveUp,
                     '8': self.moveUp,
                     'up': self.moveUp,
                     's': self.moveDown,
                     '2': self.moveDown,
                     'down': self.moveDown,
                     'a': self.moveLeft,
                     '4': self.moveLeft,
                     'left': self.moveLeft,
                     'd': self.moveRight,
                     '6': self.moveRight,
                     'right': self.moveRight
                     })

  #def on_touch_down(self, event):
  #  self.tryScroll(event)
  #  return super(PreviewOutside, self).on_touch_down(event)

  #def tryScroll(self, event):
  #  if hasattr(event, 'button'):
  #    #if self.parent.collide_point(event.x, event.y):
  #    if event.button == 'scrollup':
  #      self.scale = self.scale / 1.2
  #    elif event.button == 'scrolldown':
  #      self.scale = self.scale * 1.2

  #def on_transform_with_touch(self, event):
  #  self.wasScaled()

  #def wasScaled(self):
  #  parent = self.parent.parent
  #  child = self.parent
  #  index = parent.children.index(child)
  #  parent.remove_widget(child)
  #  parent.add_widget(child, index)

#########################################################################################

class PreviewInside(GridLayout):
  pass

#########################################################################################

class FocusCameraScreen(Screen):
  
  def update(self, dt):
    checkForDisconnected(self.manager)
    if gphoto:
      self.cameraRefocus.text = 'Test Shot (3)'
    else:
      self.cameraRefocus.text = 'Refocus (3)'

  def keyPress(self, key):
    handleKeyPress(key,
                   { '1': self.cameraNextAction,
                     '3': self.cameraRefocusAction,
                     '5': self.cameraSwapAction,
                     '9': self.backAction })
    self.preview.keyPress(key)

  def on_pre_enter(self):
    try:
      saveConfig(self.manager.mountPoint)
      if self.manager.newCapture:
        self.manager.newCapture = False
        if (odd.code == camera_thread.COMPLETE and
            even.code == camera_thread.COMPLETE):
          self.manager.hasFocus = True
        else:
          self.manager.hasFocus = False

      if self.manager.newPreview:
        self.manager.newPreview = False
        self.noPreviewLabel.opacity = 0.0
        self.preview.opacity = 1.0
      else:
        self.noPreviewLabel.opacity = 1.0
        if gphoto:
          self.noPreviewLabel.text = 'Press pages against glass and take a test shot'
        else:
          self.noPreviewLabel.text = 'Press pages against glass and tap refocus'
        self.preview.opacity = 0.0

      odd.code = camera_thread.COMPLETE
      even.code = camera_thread.COMPLETE

      if self.manager.hasFocus:
        self.cameraNext.disabled = False
        self.cameraSwap.disabled = False
        #self.cameraLabel.text = 'Tap Next to Begin Capture'
      else:
        self.cameraNext.disabled = True
        self.cameraSwap.disabled = True
        #self.cameraLabel.text = 'Press Pages Against Glass and Tap Refocus'
    except Exception as e:
      handleCrash(e)

  def done(self):
    self.preview.even.clear_widgets()
    self.preview.odd.clear_widgets()

  def cameraNextAction(self):
    try:
      if not self.cameraNext.disabled:
        self.done()
        self.manager.transition.direction = 'left'
        self.manager.current = 'capture'
    except Exception as e:
      handleCrash(e)

  def cameraRefocusAction(self):
    try:
      odd.capture('/debug/preview-odd', self.manager.mountPoint, camera_thread.LOCK_FOCUS)
      even.capture('/debug/preview-even', self.manager.mountPoint, camera_thread.LOCK_FOCUS)
      self.manager.capturePage = 'focus-camera'
      self.manager.transition.direction = 'left'
      self.manager.mustPreview = True
      self.manager.current = 'capture-wait'
    except Exception as e:
      handleCrash(e)

  def cameraSwapAction(self):
    try:
      if not self.cameraSwap.disabled:
        swapSides()
        self.manager.newPreview = True
        self.manager.capturePage = 'focus-camera'
        self.manager.transition.direct = 'left'
        self.manager.current = 'preview-wait'
    except Exception as e:
      handleCrash(e)

  def backAction(self):
    self.done()
    self.manager.transition.direction = 'right'
    self.manager.current = 'configure-camera'

#########################################################################################

class CaptureWaitScreen(Screen):

  def update(self, dt):
    global hasCrashed, crashMessage
    oddDone = odd.update()
    evenDone = even.update()
    if oddDone and evenDone:
      if odd.code == camera_thread.CRASHED:
        crashMessage = odd.message
        hasCrashed = True
      elif even.code == camera_thread.CRASHED:
        crashMessage = even.message
        hasCrashed = True
      elif (odd.code == camera_thread.COMPLETE and
          even.code == camera_thread.COMPLETE):
        self.manager.newCapture = True
        odd.save(self.manager.mountPoint)
        even.save(self.manager.mountPoint)
        self.manager.transition.direction = 'left'
        if self.manager.mustPreview:
          self.manager.current = 'preview-wait'
        else:
          self.manager.current = self.manager.capturePage
      elif (odd.code == camera_thread.DISCONNECTED or
            even.code == camera_thread.DISCONNECTED):
        self.manager.transition.direction = 'left'
        self.manager.current = 'debug'
      else:
        self.manager.transition.direction = 'left'
        self.manager.current = 'capture-fail'

  def keyPress(self, key):
    handleKeyPress(key,
                   { '0': self.restartAction })

  def restartAction(self):
    os.system('killall python')    

class PreviewWaitScreen(Screen):

  def update(self, dt):
    global hasCrashed, crashMessage
    oddDone = odd.updatePreview()
    evenDone = even.updatePreview()
    if oddDone and evenDone:
      if odd.preview.result.code == preview_thread.CRASHED:
        crashMessage = odd.preview.result.message
        hasCrashed = True
      elif even.preview.result.code == preview_thread.CRASHED:
        crashMessage = even.preview.result.message
        hasCrashed = True
      else:
        dest = self.manager.get_screen(self.manager.capturePage)
        odd.showPreview(dest.preview.odd)
        even.showPreview(dest.preview.even)
        self.manager.newPreview = True
        self.manager.transition.direction = 'left'
        self.manager.current = self.manager.capturePage

  def on_enter(self):
    try:
      odd.setPreview()
      even.setPreview()
    except Exception as e:
      handleCrash(e)

  def keyPress(self, key):
    handleKeyPress(key,
                   { '0': self.restartAction })

  def restartAction(self):
    os.system('killall python')    

#########################################################################################

class ZoomCameraScreen(Screen):
  preview = ObjectProperty(None, noneallowed=True)
  
  def update(self, dt):
    self.select.update(dt)

  def keyPress(self, key):
    self.select.keyPress(key)

  def on_pre_enter(self):
    self.preview = self.select.preview
    self.select.on_pre_enter(self.manager)

class ShutterCameraScreen(Screen):
  preview = ObjectProperty(None, noneallowed=True)

  def update(self, dt):
    self.select.update(dt)

  def keyPress(self, key):
    self.select.keyPress(key)

  def on_pre_enter(self):
    self.preview = self.select.preview
    self.select.on_pre_enter(self.manager)


#########################################################################################

#screenshotCount = 0

class CaptureScreen(Screen):
  def __init__(self, a=1.0, **kwargs):
    super(CaptureScreen, self).__init__(**kwargs)
    self.lastEvenPage = None
    self.nextEvenPage = None
    self.isCapturing = True

  def beginCapture(self):
    self.capture()

  def update(self, dt):
    checkForDisconnected(self.manager)

  def keyPress(self, key):
    handleKeyPress(key,
                   { '1': self.showPreview,
                     '3': self.rescan,
                     '5': self.done, })
    self.preview.keyPress(key)

  def on_pre_leave(self):
    self.isCapturing = True

  def on_pre_enter(self):
    try:
      errorlog.write('CAPTURE: on_pre_enter')
      self.isCapturing = False
      if self.manager.newCapture:
        errorlog.write('CAPTURE: newCapture is true')
        self.manager.newCapture = False
        if (odd.code == camera_thread.COMPLETE and
            even.code == camera_thread.COMPLETE):
          errorlog.write('CAPTURE: both are COMPLETE')
          self.lastEvenPage = self.nextEvenPage
          self.nextEvenPage += 2
          self.captureLabel.text = 'Captured Pages ' + str(self.lastEvenPage) + ', ' + str(self.lastEvenPage + 1)
          self.rescanButton.disabled = False
        else:
          errorlog.write('CAPTURE: one or both are failure')
          self.captureLabel.text = 'Ready For Capture'
          self.rescanButton.disabled = True
        odd.code = camera_thread.COMPLETE
        even.code = camera_thread.COMPLETE

      if self.manager.newPreview:
        errorlog.write('CAPTURE: newPreview is true')
        self.manager.newPreview = False
        self.preview.opacity = 1.0
        self.previewButton.opacity = 0.0
        self.previewButton.disabled = True
      else:
        errorlog.write('CAPTURE: newPreview is false')
        self.preview.opacity = 0.0
        if self.lastEvenPage is not None:
          self.previewButton.opacity = 1.0
          self.previewButton.disabled = False
        else:
          self.previewButton.opacity = 0.0
          self.previewButton.disabled = True

      errorlog.write('CAPTURE: before resetPages()')
      if self.nextEvenPage is None:
        self.resetPages()
      errorlog.write('CAPTURE: on_pre_enter complete')

    except Exception as e:
      handleCrash(e)

  def resetPages(self):
    pattern = re.compile('^([0-9]+)\.jpg$')
    largest = -1
    # Search through all files in the directory
    filenames = os.listdir(self.manager.mountPoint + '/images')
    for name in filenames:
      # Find only files that are a number .jpg
      match = pattern.search(name)
      if match:
        # Turn those into a number. Find the largest filename
        num = int(match.group(1))
        largest = max(largest, num)
    # Add one to it for the next scan page
    largest += 1
    # If it isn't an even number, we skip one
    if largest % 2 != 0:
      largest += 1
    self.nextEvenPage = largest

  def capture(self):
    try:
      if not self.isCapturing:
        self.scanAt(self.nextEvenPage)
    except Exception as e:
      handleCrash(e)

  def rescan(self):
    try:
      if not self.isCapturing:
        self.nextEvenPage = self.lastEvenPage
        self.scanAt(self.nextEvenPage)
    except Exception as e:
      handleCrash(e)

  def scanAt(self, pageNumber):
    if pageNumber is not None:
      odd.capture(self.makeFile(pageNumber+1), self.manager.mountPoint, camera_thread.KEEP_FOCUS)
      even.capture(self.makeFile(pageNumber), self.manager.mountPoint, camera_thread.KEEP_FOCUS)
      self.manager.capturePage = 'capture'
      self.manager.mustPreview = False
      self.manager.transition.direction = 'left'
      self.manager.current = 'capture-wait'

  def makeFile(self, number):
    return '/images/%04d' % number

  def done(self):
    try:
      self.preview.even.clear_widgets()
      self.preview.odd.clear_widgets()
      self.manager.transition.direction = 'right'
      self.manager.current = 'start'
    except Exception as e:
      handleCrash(e)

  def showPreview(self):
    try:
      self.preview.evenLabel.text = self.makeFile(self.lastEvenPage)
      self.preview.oddLabel.text = self.makeFile(self.lastEvenPage + 1)
      self.manager.capturePage = 'capture'
      self.manager.transition.direction = 'left'
      self.manager.current = 'preview-wait'
    except Exception as e:
      handleCrash(e)

#########################################################################################

class CaptureFailScreen(Screen):
  def update(self, dt):
    if debug:
      errorlog.write('FAIL: Update')

  def updateLabel(self, label, side):
    if side.code == camera_thread.COMPLETE:
      label.text = side.position + ' camera: [color=aaffaa]Succeeded[/color]'
    else:
      label.text = side.position + ' camera: [color=ffaaaa]Failed[/color]: ' + side.message

  def on_pre_enter(self):
    try:
      if debug:
        errorlog.write('FAIL: Before labels')
      self.evenLabel.text = 'Even Camera: '
      self.oddLabel.text = 'Odd Camera: '
      self.updateLabel(self.evenLabel, even)
      self.updateLabel(self.oddLabel, odd)
      if debug:
        errorlog.write('FAIL: Before beeps')
      even.camera.beepFail()
      odd.camera.beepFail()
      errorlog.write('FAIL: After pre_enter')
    except Exception as e:
      handleCrash(e)

  def ok(self):
    try:
      #odd.code = camera_thread.COMPLETE
      #even.code = camera_thread.COMPLETE
      errorlog.write('FAIL: before ok')
      errorlog.write('FAIL: capturePage: ' + self.manager.capturePage)
      self.manager.transition.direction = 'left'
      self.manager.current = self.manager.capturePage
      errorlog.write('FAIL: after ok')
    except Exception as e:
      handleCrash(e)

  def keyPress(self, key):
    handleKeyPress(key,
                   { '1': self.ok,
                     '0': self.restartAction })

  def restartAction(self):
    os.system('killall python')    

#########################################################################################

class DebugScreen(Screen):
  def update(self, dt):
    if (odd.camera is None or
        even.camera is None or
        not odd.camera.is_connected() or
        not even.camera.is_connected()):
      (oddFound, evenFound, tooManyFound) = checkCameras()
      self.updateSide(oddFound, odd, self.oddStatus, self.oddLog, self.oddMessage)
      self.updateSide(evenFound, even, self.evenStatus, self.evenLog, self.evenMessage)
    if even.camera is not None and even.camera.is_connected() and odd.camera and odd.camera.is_connected():
      self.okButton.disabled = False;
    else:
      self.okButton.disabled = True;

  def keyPress(self, key):
    handleKeyPress(key,
                   { '1': self.ok,
                     '2': self.getEvenLog,
                     '3': self.getOddLog,
                     '0': self.restartAction })

  def restartAction(self):
    os.system('killall python')    

  def updateSide(self, found, side, status, log, message):
    if found:
      status.text = '[color=aaffaa]Connected[/color]'
    else:
      status.text = '[color=ffaaaa]Disconnected[/color]'

    if side.code == camera_thread.FAILED:
      message.text = 'Failed: ' + side.message
    elif side.code == camera_thread.DISCONNECTED:
      message.text = 'Crashed: ' + side.message

    if found:
      log.disabled = False
    else:
      log.disabled = True

  def on_pre_enter(self):
    try:
      self.oddMessage.text = ''
      self.evenMessage.text = ''
      self.oddStatus.text = 'Searching...'
      self.evenStatus.text = 'Searching...'
      even.camera.beepFail()
      odd.camera.beepFail()
    except Exception as e:
      handleCrash(e)

  def ok(self):
    try:
      odd.code = camera_thread.COMPLETE
      even.code = camera_thread.COMPLETE
      odd.camera.isReady = False
      even.camera.isReady = False
      self.manager.hasFocus = False
      self.manager.transition.direction = 'left'
      self.manager.current = 'configure-camera'
    except Exception as e:
      handleCrash(e)

  def getOddLog(self):
    try:
      if not self.oddLog.disabled:
        self.oddLog.disabled = True
        self.getLog(odd)
        self.oddLog.disabled = False
    except Exception as e:
      handleCrash(e)

  def getEvenLog(self):
    try:
      if not self.evenLog.disabled:
        self.evenLog.disabled = True
        self.getLog(even)
        self.evenLog.disabled = False
    except Exception as e:
      handleCrash(e)

  def getLog(self, side):
    try:
      side.camera.getRomLog(side.position, self.manager.mountPoint)
      side.message = 'Debug log saved to ' + side.position + '-rom.log'
    except Exception as e:
      side.message = 'Could not get debug log: ' + side.camera.message + ': ' + str(e)
    
#########################################################################################

hasCrashed = False
crashMessage = None

def handleCrash(e):
  global hasCrashed, crashMessage
  crashMessage = 'Crash Log: ' + str(e) + ': ' + str(e.args) + ':\n' + traceback.format_exc()
  hasCrashed = True

def checkForCrash(manager):
  global hasCrashed
  result = False
  if hasCrashed:
    hasCrashed = False
    manager.current = 'crash'
    result = True
  return result

class CrashScreen(Screen):

  def update(self, dt):
    pass

  def on_pre_enter(self):
    self.errorLabel.text = crashMessage

  def restart(self):
    exit(1)

#########################################################################################

class ScanApp(App):
  def build(self):
    self.handlingKey = False
    self.manager = ScanRoot()

    # Set up GPIO pin for foot pedal
    os.system("gpio export 21 up")
    wiringpi.wiringPiSetupSys()
    #wiringpi.pinMode(21, 0)
    #wiringpi.pullUpDnControl(21, 2)
    self.lastPedal = 0

    Clock.schedule_interval(self.update, 0.5)
    Clock.schedule_interval(self.checkPedal, 0.05)

    Window.bind(on_key_down=self.on_key_down)
    Window.bind(on_key_up=self.on_key_up)
    return self.manager

  def update(self, dt):
    try:
      if not checkForCrash(self.manager):
        if (not self.manager.hasTransitioned or
            (self.manager.current_screen.transition_progress == 1 and
             self.manager.current_screen.transition_state == 'in')):
          self.manager.current_screen.update(dt)
    except Exception as e:
      handleCrash(e)
    return True

  def checkPedal(self, dt):
    try:
      pass
      # Only trigger a capture when the circuit goes from open to closed
      nextPedal = wiringpi.digitalRead(21)
      #print('checkPedal', nextPedal)
      if self.lastPedal == 1 and nextPedal == 0 and 'beginCapture' in dir(self.manager.current_screen):
        self.manager.current_screen.beginCapture()
      self.lastPedal = nextPedal
    except Exception as e:
      handleCrash(e)
    return True
    
  def on_key_down(self, window, scancode, codepoint, key, other):
    if not self.handlingKey:
      self.handlingKey = True
      try:
        #print 'KEY: ', scancode, codepoint, key, other
        #if key == '=':
        #  global screenshotCount
        #  filename = 'screenshot%d.png' % screenshotCount
        #  Window.screenshot(name=filename)
        #  print filename
        #  screenshotCount += 1
        if (key == 'c' or
            key == 'b' or
            key == ' '):
          if 'beginCapture' in dir(self.manager.current_screen):
            self.manager.current_screen.beginCapture()
        else:
          # (key == '0' or key == '1' or key == '2' or key == '3' or key == '4' or
          #key == '5' or key == '6' or key == '7' or key == '8' or key == '9'):
          self.manager.current_screen.keyPress(key)
      except Exception as e:
        handleCrash(e)
    return True

  def on_key_up(self, window, scancode, codepoint, key, other):
    self.handlingKey = False

if __name__ == '__main__':
  odd = CameraSide(camera_thread.CameraThread(), 'odd')
  even = CameraSide(camera_thread.CameraThread(), 'even')
  odd.start()
  even.start()
  ScanApp().run()
    
