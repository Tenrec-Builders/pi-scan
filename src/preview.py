import preview_thread
from kivy.uix.image import Image
from kivy.graphics.texture import Texture

class Preview:
  def __init__(self):
    self.thread = preview_thread.PreviewThread()
    self.discardNext = False
    self.waitingImage = None
    self.code = preview_thread.COMPLETE
    self.result = None
    self.textures = []

  def position(self, newPosition):
    self.thread.position = newPosition

  def start(self):
    self.thread.start()

  def update(self):
    done = False
    if self.code == preview_thread.WAITING:
      self.result = self.thread.checkResult()
      self.code = self.result.code
      if self.result.code != preview_thread.WAITING:
        if not self.discardNext:
          done = True
        elif self.discardNext and self.waitingImage is not None:
          self.discardNext = False
          self.thread.beginPreview(self.waitingImage)
    else:
      done = True
    return done

  def redisplay(self, root):
    if self.result.code == preview_thread.COMPLETE:
      root.cols = self.result.columnCount
      while len(root.children) > len(self.result.data):
        root.remove_widget(root.children[-1])
      while len(root.children) < len(self.result.data):
        root.add_widget(Image())
      for i in xrange(0, len(self.result.data)):
        current = root.children[i]
        if len(self.textures) <= i:
          self.textures.append(Texture.create_from_data(self.result.data[i]))
          self.textures[i].flip_vertical()
        else:
          self.textures[i].blit_data(self.result.data[i])
        current.texture = None
        current.texture = self.textures[i]
        current.size_hint = (1.0*self.result.sizes[i][0]/self.result.width,
                             1.0*self.result.sizes[i][1]/self.result.height)
      root.width = root.height * self.result.width / self.result.height
      #root.height = root.width * self.result.height / self.result.width
    else:
      root.clear_widgets()

  def setImage(self, newImage):
    self.waitingImage = newImage
    if self.code == preview_thread.WAITING:
      self.discardNext = True
    else:
      self.thread.beginPreview(newImage)
      self.discardNext = False
      self.code = preview_thread.WAITING

