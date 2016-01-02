from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.vector import Vector
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics.transformation import Matrix
import camera_thread, stick, camera, preview, errorlog
import os, json, string, re, traceback, errno

version = '0.4'

odd = None
even = None
config = {}

#########################################################################################

class CameraSide:
  def __init__(self, thread, position):
    self.thread = thread
    self.config = json.loads('{}')
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
    self.serial = info.serial_num
    self.camera = camera.Camera(info, self.config)
    self.camera.position = self.position
    self.camera.connect()

  def capture(self, newFilename, shouldRefocus):
    self.filename = newFilename
    self.scan = None
    self.code = camera_thread.WAITING 
    self.message = 'Lost Connection to Camera'
    self.thread.beginCapture(self.camera, shouldRefocus)

  def save(self, mountPoint):
    if self.raw is not None and self.filename is not None and self.code == camera_thread.COMPLETE:
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
  config[odd.serial]['position'] = 'odd'
  if even.serial not in config:
    config[even.serial] = {}
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
  oddFound = False
  evenFound = False
  tooManyCameras = False
  cameraList = camera.search()
  #cameraList = [0,0]
  try:
    if len(cameraList) > 2:
      tooManyCameras = True
    else:
      for item in cameraList:
        if item.serial_num == odd.serial:
          if not odd.camera.is_connected():
            odd.reset(item)
        elif item.serial_num == even.serial:
          if not even.camera.is_connected():
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
    self.titleLabel.text = 'Pi Scan ' + version
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

  def on_pre_leave(self):
    try:
      self.powerOff.text = ''
      self.manager.hasTransitioned = True
    except Exception as e:
      handleCrash(e)

  def quit(self):
    os.system('killall run-pi-scan.sh')
    exit()

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
      else:
        self.manager.mountPoint = string.strip(mountPoint.encode('ascii'), '\0')
        failMessage = self.makeDirs()
        if failMessage is None:
          self.diskStatus.text = 'Storage Found. Click next to continue.'
          self.diskNext.disabled = False
          self.spinner.opacity = 0.0
        else:
          self.diskStatus.text = 'Storage Error: ' + failMessage
          self.diskNext.disabled = True
          self.spinner.opacity = 1.0
    else:
      self.diskStatus.text = '[color=ff3333]Multiple Drives Found.[/color] Disconnect all but one drive to continue.'
      self.diskNext.disabled = True
      self.spinner.opacity = 1.0

  def on_pre_enter(self):
    try:
      self.diskStatus.text = 'Searching for storage...'
      self.diskNext.disabled = True
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

#########################################################################################

class ConfigureFolderScreen(Screen):
  def update(self, dt):
    pass

#########################################################################################

class ChangeFolderScreen(Screen):
  def update(self, dt):
    if self.manager.updateScanChooser:
      self.manager.updateScanChooser = False
      self.scanChooser.path = ''
      self.scanChooser.path = self.manager.scanPath
    #self.manager.current = 'find-storage'

#########################################################################################

class NewFolderScreen(Screen):
  def update(self, dt):
    disabledState = False
    if self.folderName.text == '':
      disabledState = True
    if self.okButton.disabled != disabledState:
      self.okButton.disabled = disabledState

  def clickAddFolder(self, name):
    try:
      os.mkdir(self.manager.scanPath + '/' + name)
    except:
      # Directory exists
      pass
    self.manager.updateScanChooser = True

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
        self.spinner.opacity = 1.0
      elif oddFound and evenFound:
        self.cameraLabel.text = 'Found two cameras. Click next to continue.'
        self.cameraNext.disabled = False
        self.spinner.opacity = 0.0
      elif not oddFound and not evenFound:
        self.cameraLabel.text = 'No cameras found. Plug in or turn on the cameras.' + errorText
        self.cameraNext.disabled = True
        self.spinner.opacity = 1.0
      elif not oddFound:
        self.cameraLabel.text = 'Odd camera not found. Plug in or turn it on.' + errorText
        self.cameraNext.disabled = True
        self.spinner.opacity = 1.0
      elif not evenFound:
        self.cameraLabel.text = 'Even camera not found. Plug in or turn it on.' + errorText
        self.cameraNext.disabled = True
        self.spinner.opacity = 1.0

  def on_pre_enter(self):
    try:
      errorlog.openLog(self.manager.mountPoint)
      loadConfig(self.manager.mountPoint)
      self.cameraLabel.text = 'Searching for cameras...'
      self.cameraNext.disabled = True
    except Exception as e:
      handleCrash(e)

  def next(self):
    try:
      configureSides()
      self.manager.transition.direction = 'left'
      self.manager.current = 'focus-camera'
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
      self.manager.capturePage = 'focus-camera'
      self.manager.transition.direction = 'left'
      self.manager.current = 'debug'

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

  def next(self):
    try:
      self.done()
      self.manager.transition.direction = 'left'
      self.manager.current = 'capture'
    except Exception as e:
      handleCrash(e)

  def refocus(self):
    try:
      odd.capture('/debug/preview-odd.jpg', True)
      even.capture('/debug/preview-even.jpg', True)
      self.manager.capturePage = 'focus-camera'
      self.manager.transition.direction = 'left'
      self.manager.mustPreview = True
      self.manager.current = 'capture-wait'
    except Exception as e:
      handleCrash(e)

  def swap(self):
    try:
      swapSides()
      self.manager.newPreview = True
      self.manager.capturePage = 'focus-camera'
      self.manager.transition.direct = 'left'
      self.manager.current = 'preview-wait'
    except Exception as e:
      handleCrash(e)

#########################################################################################

class CaptureWaitScreen(Screen):

  def update(self, dt):
    oddDone = odd.update()
    evenDone = even.update()
    if oddDone and evenDone:
      if (odd.code == camera_thread.COMPLETE and
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

class PreviewWaitScreen(Screen):

  def update(self, dt):
    oddDone = odd.updatePreview()
    evenDone = even.updatePreview()
    if oddDone and evenDone:
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

#class CameraZoomScreen(Screen):
#  def update(self, dt):
#    pass

#class CameraWhiteScreen(Screen):
#  def update(self, dt):
#    pass

#########################################################################################

class CaptureScreen(Screen):
  def __init__(self, a=1.0, **kwargs):
    super(CaptureScreen, self).__init__(**kwargs)
    self.lastEvenPage = None
    self.nextEvenPage = None
    Window.bind(on_key_down=self.on_key_down)
    
  def on_key_down(self, window, scancode, codepoint, key, other):
    try:
      if self.manager.current == 'capture':
        if (key == 's' or
            key == 'c' or
            key == 'b' or
            key == ' '):
          self.capture()
        elif key == 'r' and self.lastEvenPage is not None:
          self.rescan()
    except Exception as e:
      handleCrash(e)
    return True

  def update(self, dt):
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
      self.manager.capturePage = 'focus-camera'
      self.manager.transition.direction = 'left'
      self.manager.current = 'debug'

  def on_pre_enter(self):
    try:
      if self.manager.newCapture:
        self.manager.newCapture = False
        if (odd.code == camera_thread.COMPLETE and
            even.code == camera_thread.COMPLETE):
          self.lastEvenPage = self.nextEvenPage
          self.nextEvenPage += 2
        odd.code = camera_thread.COMPLETE
        even.code = camera_thread.COMPLETE

      if self.manager.newPreview:
        self.manager.newPreview = False
        self.preview.opacity = 1.0
        self.previewButton.opacity = 0.0
        self.previewButton.disabled = True
      else:
        self.preview.opacity = 0.0
        if self.lastEvenPage is not None:
          self.previewButton.opacity = 1.0
          self.previewButton.disabled = False
        else:
          self.previewButton.opacity = 0.0
          self.previewButton.disabled = True

      if self.nextEvenPage is None:
        self.resetPages()

      if self.lastEvenPage is None:
        self.rescanButton.disabled = True
      else:
        self.rescanButton.disabled = False
    except Exception as e:
      handleCrash(e)

  def resetPages(self):
    pattern = re.compile('^([0-9]+)\.jpg$')
    largest = 0
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
      self.scanAt(self.nextEvenPage)
    except Exception as e:
      handleCrash(e)

  def rescan(self):
    try:
      self.nextEvenPage = self.lastEvenPage
      self.scanAt(self.nextEvenPage)
    except Exception as e:
      handleCrash(e)

  def scanAt(self, pageNumber):
    if pageNumber is not None:
      odd.capture(self.makeFile(pageNumber+1), False)
      even.capture(self.makeFile(pageNumber), False)
      self.manager.capturePage = 'capture'
      self.manager.mustPreview = False
      self.manager.transition.direction = 'left'
      self.manager.current = 'capture-wait'

  def makeFile(self, number):
    return '/images/%04d.jpg' % number

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
    self.updateLabel(self.evenLabel, even)
    self.updateLabel(self.oddLabel, odd)

  def updateLabel(self, label, side):
    if side.code == camera_thread.COMPLETE:
      label.text = side.position + ' camera: [color=aaffaa]Succeeded[/color]'
    else:
      label.text = side.position + ' camera: [color=ffaaaa]Failed[/color]: ' + side.message

  def on_pre_enter(self):
    try:
      self.evenLabel.text = 'Even Camera: '
      self.oddLabel.text = 'Odd Camera: '
    except Exception as e:
      handleCrash(e)

  def ok(self):
    try:
      odd.code = camera_thread.COMPLETE
      even.code = camera_thread.COMPLETE
      self.manager.transition.direction = 'left'
      self.manager.current = self.manager.capturePage
    except Exception as e:
      handleCrash(e)

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

  def updateSide(self, found, side, status, log, message):
    if found:
      status.text = '[color=aaffaa]Connected[/color]'
    else:
      status.text = '[color=ffaaaa]Disconnected[/color]'

    if side.code == camera_thread.FAILED:
      message.text = 'Failed: ' + side.message
    elif side.code == camera_thread.DISCONNECTED:
      message.text = 'Crashed: ' + side.message

    if side.code == camera_thread.DISCONNECTED and found:
      log.disabled = False
    else:
      log.disabled = True

  def on_pre_enter(self):
    try:
      self.oddMessage.text = ''
      self.evenMessage.text = ''
      self.oddStatus.text = 'Searching...'
      self.evenStatus.text = 'Searching...'
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
      self.manager.current = 'focus-camera'
    except Exception as e:
      handleCrash(e)

  def getOddLog(self):
    try:
      self.getLog(odd)
    except Exception as e:
      handleCrash(e)

  def getEvenLog(self):
    try:
      self.getLog(even)
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
    self.manager = ScanRoot()
    Clock.schedule_interval(self.update, 0.5)
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

if __name__ == '__main__':
  odd = CameraSide(camera_thread.CameraThread(), 'odd')
  even = CameraSide(camera_thread.CameraThread(), 'even')
  odd.start()
  even.start()
  ScanApp().run()
    
