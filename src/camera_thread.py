from threading import Thread, Event

WAITING = 0
COMPLETE = 1
DISCONNECTED = 2
FAILED = 3
CRASHED = 4

# Set AFL to 1
LOCK_FOCUS = 0
# Set AFL to 0
AUTO_FOCUS = 1
# Do not change AFL
KEEP_FOCUS = 2


class CameraResult:
  def __init__(self):
    self.scan = None
    self.code = WAITING
    self.message = ''

class CameraThread:

  def __init__(self):
    self.thread = Thread(target=self.loop)
    self.thread.daemon = True
    self.captureEvent = Event()
    self.camera = None
    self.resultEvent = Event()
    self.result = CameraResult()
    self.shouldRefocus = LOCK_FOCUS

  def start(self):
    self.thread.start()

  def loop(self):
    try:
      while True:
        self.waitToCapture()

        result = CameraResult()
        refocusGood = True
        prepareGood = self.camera.prepare()
        if prepareGood:
          if self.shouldRefocus == LOCK_FOCUS:
            refocusGood = self.camera.refocus()
          elif self.shouldRefocus == AUTO_FOCUS:
            refocusGood = self.camera.unlockFocus()
          if not refocusGood:
            result.scan = None
            result.message = 'Failed to refocus: ' + self.camera.message
            result.code = FAILED
            if not self.camera.is_connected():
              result.code = DISCONNECTED
          else:
            scan = self.camera.capture(self.filename)
            if scan is None:
              result.scan = None
              result.message = 'Failed to capture: ' + self.camera.message
              result.code = FAILED
              if not self.camera.is_connected():
                result.code = DISCONNECTED
            else:
              result.scan = scan
              result.message = ''
              result.code = COMPLETE
        else:
          result.scan = None
          result.message = 'Failed to prepare camera: ' + self.camera.message
          result.code = FAILED
          if not self.camera.is_connected():
            result.code = DISCONNECTED
        self.setResult(result)
    except Exception as e:
      result = CameraResult()
      result.code = CRASHED
      result.message = 'Crash Log for ' + self.camera.position + ' Camera Thread: ' + str(e) + ': ' + str(e.args) + ':\n' + traceback.format_exc()
      self.setResult(result)

  # Interface for outside to trigger capture and get the result
  def beginCapture(self, camera, shouldRefocus, filename):
    self.camera = camera
    self.shouldRefocus = shouldRefocus
    self.filename = filename
    self.captureEvent.set()

  def checkResult(self):
    result = CameraResult()
    if self.resultEvent.is_set():
      result = self.result
      self.result = CameraResult()
      self.resultEvent.clear()
    return result

  # Interface for inside loop to wait, capture, and set the result
  def waitToCapture(self):
    self.captureEvent.wait()
    self.captureEvent.clear()

  def setResult(self, newResult):
    self.result = newResult
    self.resultEvent.set()
