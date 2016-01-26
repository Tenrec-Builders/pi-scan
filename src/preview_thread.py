from threading import Thread, Event
from PIL import Image as PillowImage
import cStringIO as StringIO
from kivy.core.image import ImageData as CoreImageData
from kivy.graphics.texture import Texture
#from jpegtran import JPEGImage
import math
import errorlog

WAITING = 0
COMPLETE = 1
FAILED = 3
CRASHED = 4

class PreviewResult:
  def __init__(self):
    self.width = 0
    self.height = 0
    self.columnCount = 0
    self.data = []
    self.sizes = []
    self.code = WAITING
    self.message = ''

class PreviewThread:
  def __init__(self):
    self.thread = Thread(target=self.loop)
    self.thread.daemon = True
    self.previewEvent = Event()
    self.resultEvent = Event()
    self.result = PreviewResult()
    self.raw = None
    self.position = None

  def start(self):
    self.thread.start()

  def loop(self):
    try:
      while True:
        self.waitToProcess()

        result = PreviewResult()
        if self.raw:
          result = self.process(self.raw)
        else:
          result.code = FAILED
          result.message = 'No Image Found to Process'

        self.setResult(result)
    except Exception as e:
      result = PreviewResult()
      result.code = CRASHED
      result.message = 'Crash Log for Preview Thread: ' + str(e) + ': ' + str(e.args) + ':\n' + traceback.format_exc()
      self.setResult(result)

  def beginPreview(self, raw):
    self.raw = raw
    self.previewEvent.set()

  def checkResult(self):
    result = PreviewResult()
    if self.resultEvent.is_set():
      result = self.result
      self.result = PreviewResult()
      self.raw = None
      self.resultEvent.clear()
    return result

  def waitToProcess(self):
    self.previewEvent.wait()
    self.previewEvent.clear()

  def setResult(self, newResult):
    self.result = newResult
    self.resultEvent.set()

  def process(self, raw):
    result = PreviewResult()
    result.code = FAILED
    try:
      # Load full image from raw binary representation
      result.message = 'Failed to load image'
      stream = StringIO.StringIO(raw)
      full = PillowImage.open(stream)
      #full = JPEGImage(blob=raw)

      # Rotate the full image for preview
      if self.position == 'odd':
        full = full.transpose(PillowImage.ROTATE_270)
        #full = full.rotate(-90)
      elif self.position == 'even':
        full = full.transpose(PillowImage.ROTATE_90)
        #full = full.rotate(90)

      # Set size parameters based on the full image
      #result.message = 'Failed to calculate size parameters'
      result.width = full.size[0]
      #result.width = full.width
      result.height = full.size[1]
      #result.height = full.height
      result.columnCount = int(math.ceil(result.width / 2000.0))
      rowCount = int(math.ceil(result.height / 2000.0))

      # Populate the cropped core images for later preview
      result.data = []
      result.sizes = []
      for y in xrange(rowCount-1, -1, -1):
        for x in xrange(result.columnCount-1, -1, -1):
          result.message = 'Failed to crop base image'
          #width = min(result.width - x*2000, 2000)
          #height = min(result.height - y*2000, 2000)
          #croppedJpeg = full.crop(x*2000, y*2000, width, height)
          #stream = StringIO.StringIO(croppedJpeg.as_blob())
          #cropped = PillowImage.open(stream)
          right = min((x+1)*2000, result.width)
          lower = min((y+1)*2000, result.height)
          cropBox = (x*2000, y*2000, right, lower)
          cropped = full.crop(cropBox)
          result.message = 'Failed to turn cropped image into texture'
          data = CoreImageData(cropped.size[0], cropped.size[1],
                               cropped.mode.lower(), cropped.tobytes())
          result.data.append(data)
          result.sizes.append(cropped.size)
      result.code = COMPLETE
    except Exception as e:
      errorlog.write('Failed to process: ' + result.message + ': ' + str(e) + ': ' + str(e.args))
    return result
  
