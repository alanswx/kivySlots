from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scatter import ScatterPlane


class Viewport(ScatterPlane):
    def __init__(self, **kwargs):
      kwargs.setdefault('size', (1920, 1080))
      kwargs.setdefault('size_hint', (None, None))
      kwargs.setdefault('do_scale', False)
      kwargs.setdefault('do_translation', False)
      kwargs.setdefault('do_rotation', False)

      super(Viewport, self).__init__( **kwargs)
      Window.bind(system_size=self.on_window_resize)
      Clock.schedule_once(self.fit_to_window, -1)

    def on_window_resize(self, window, size):
      self.fit_to_window()

    def fit_to_window(self, *args):
      if self.width < self.height: #portrait
        if Window.width < Window.height: #so is window   
          self.scale = Window.width/float(self.width)
        else: #window is landscape..so rotate vieport
          self.scale = Window.height/float(self.width)
          self.rotation = -90
      else: #landscape
        if Window.width > Window.height: #so is window   
          self.scale = Window.width/float(self.width)
        else: #window is portrait..so rotate vieport
          self.scale = Window.height/float(self.width)
          self.rotation = -90

      self.center = Window.center
      for c in self.children:
        c.size = self.size

    def add_widget(self, w, *args, **kwargs):
      super(Viewport, self).add_widget(w, *args, **kwargs)
      w.size = self.size
