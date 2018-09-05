#!/usr/bin/env python3
from __future__ import division

import random
import os, sys, time, math, logging, argparse, glob, subprocess

import config
from functools import partial

try:
  import piHardware as Hardware
except ImportError:
  import nullHardware as Hardware


from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.core.image import Image
from kivy.core.window import Window, Keyboard
from kivy.properties import (AliasProperty,
                             ListProperty,
                             NumericProperty,
                             ObjectProperty)
from kivy.uix.image import Image as ImageWidget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.utils import get_color_from_hex
from kivy.config import Config

import viewport

Builder.load_string('''
<StartScreen>:
    buttons: _buttons
    name: "Start Screen"
    canvas:
        Color:
            hsv: .5, .5, .3
        Rectangle:
            size: self.size
    Label:
        text: "Slots"
        font_size: '128sp'
        pos_hint: {'center_x': .5, 'center_y': .7}

    GridLayout:
        id: _buttons
        size_hint: .10, .40
        pos_hint: {'center_x': .5, 'center_y': .3}
        cols: 1

<GameScreen>:
    slots: _id_slots
    name: "Game Screen"
    FloatLayout:
        Slots:
            id: _id_slots
            canvas:
''')

# 

# should this be global?
coinDispense = Hardware.coinDispense()


class MultiAudio:
    _next = 0

    def __init__(self, filename, count):
        self.buf = [SoundLoader.load(filename)
                    for i in range(count)]

    def play(self):
        self.buf[self._next].play()
        self._next = (self._next + 1) % len(self.buf)


class Strip(Rectangle):
  def __init__(self, img, **kwargs):
    super(Strip, self).__init__(**kwargs)

    self.texture = img.texture
    self.texture.wrap = 'repeat'
    
  def add_uv(self, canvas, val):
    self.set_uv(canvas, self.tex_coords[1] - val)

  def set_uv(self, canvas, val):
    u = 0
    v = val
    w = 1
    h = -.85
    self.tex_coords = [u, v, u+w, v, u+w, v+h, u, v+h]

  def strip_pos(self):
    return int((1.18-self.tex_coords[1]) / .165) % 6

  def slot_to_uv(self, slot):
    return 1.18 - (slot * .165)

  def get_uv(self):
    return (self.tex_coords[0], self.tex_coords[1])

##  [1.100, .942, .759, .598, .444, .273]

class Slots(Widget):
    state = 'idle'
    first_stop_length=2.0
    jackpot=0

    def __init__(self, **kwargs):
      super(Slots, self).__init__(**kwargs)

      self.strips = []

    def setup(self, theme):
      for strip in self.strips:
        del strip
      self.canvas.clear()

      self.start_time=time.time()
      self.strips = []

      with self.canvas:
        bg = Rectangle()
        bg.source = os.path.join("themes", theme, "images", "background.png")
        bg.pos = (0,0)
        bg.size = (1920,1080)

        for n in range(3):
          strip = Strip(Image(os.path.join("themes", theme, "images", "stripbig1.png")))
          strip.set_uv(self, strip.slot_to_uv(0))
          self.strips.append(strip)

        Color(1,0,0)
        self.payline = Rectangle()

      self.last_time = time.time()

      ## load audio
      self.sounds = {}
      files = glob.glob(os.path.join("themes", theme, 'audio', "*" + config.audio_extension))
      files += glob.glob(os.path.join("themes", theme, 'audio', "*/*" + config.audio_extension))
      for fn in files:
        path, f = os.path.split(fn)
        f, ext = os.path.splitext(f)
        snd = SoundLoader.load(fn)
        self.sounds[f] = snd

    def on_size(self, *args):
      if len(self.strips) == 0: return

      cx = self.size[0]/2
      ns = len(self.strips)
      sw = self.size[0] / (ns*2)
      mw = 20

      sx = cx - (ns*sw+(ns-1)*mw)/2

      for n, strip in enumerate(self.strips):
        strip.pos = (sx + n*sw + (n-1)*mw, 0)
        strip.size = (sw, self.size[1])

      self.payline.pos = (50, self.size[1]/2)
      self.payline.size = (self.size[0]-100, 10)

    def start_spin(self):
        if self.state=='idle':
            self.state ='STATE_SPINNING'
            self.stopped = 0
            self.sounds['roll'].play()
            self.start_time=time.time()
            self.last_time = time.time()
            self.jackpot=0
        if self.state=='key':
            self.state ='STATE_SPINNING'
          
    def update(self):
      dt = time.time() - self.start_time
      dtt = time.time() - self.last_time
      self.last_time = time.time()

      if self.state =='idle':
        self.state='idle'
      elif self.state =='STATE_SPINNING':
        for n in range(self.stopped, len(self.strips)):
          v = .8 + (n*.1)
          self.strips[n].add_uv(self, v * dtt)

        # check time then switch to next state

        if dt > self.first_stop_length+self.stopped +random.uniform(0,0.8):  # snap to next "unit"
          slotnum = self.strips[self.stopped].strip_pos()
          self.strips[self.stopped].set_uv(self, self.strips[self.stopped].slot_to_uv(slotnum))
          # play sound for slot
          self.sounds['reel-icon-%d' % (slotnum+1)].play()
          if slotnum==5:
             logging.warn('winner on {}'.format(self.stopped+1))
             self.jackpot=self.jackpot+1
          self.stopped += 1
          if self.stopped >= len(self.strips):
            self.state = "FINAL"

      elif self.state =='FINAL':
        logging.warn('total jackpot: {}'.format(self.jackpot))
        if (self.jackpot>0): self.sounds['win'].play()
        coinDispense.dispenseCoin(self.jackpot+1)
        self.state='idle'

class GameScreen(Screen):
  playing = False

  def start_game(self, theme):

    self.slots.setup(theme)
    self.slots.on_size()
    self.timer = Clock.schedule_interval(self.update_timer, 0.004)    

  def on_keyboard_down(self, keyboard, keycode, text, modifiers):
    if keycode[1] == "spacebar": 
      self.slots.start_spin()
    if keycode[1] == "q":
      self.manager.current = "Start Screen"

  def update_timer(self, i=None, val=None):
    if self.manager.hardwareButton.checkButton():
        self.slots.start_spin()

    self.slots.update()
    if not self.playing:
        return  # don't move bird or pipes

    if self.manager.test_game_over():
        snd_game_over.play()
        self.playing = False

class StartScreen(Screen):
  def __init__(self, **kwargs):
    super(Screen, self).__init__(**kwargs)


  def build(self):
    #manager = kwargs['manager']
    themepaths = glob.glob("themes/*")

    themes = []
    for themepath in themepaths:
      path, theme = os.path.split(themepath)
      themes.append(theme)

    gl = self.buttons
    gl.size_hint = (.2, .1*len(themes))
    #themes.remove("casablanca")

    for theme in themes:
      bl = BoxLayout(size_hint=(.3, .3))
      gl.add_widget(bl)
      b = Button(text=theme, font_size='64sp', size_hint=(.9, .9), 
                 on_press=partial(self.manager.start_game, theme))
      bl.add_widget(b)

  def on_gamepad_down(self, obj, gamepad, buttonid):
    if buttonid == 8:
      self.manager.start_game("casablanca")
    if buttonid == 9:
      self.manager.start_game("halloween")
      
  def on_keyboard_down(self, keyboard, keycode, text, modifiers):

    if keycode[1] == "1": 
      self.manager.start_game("casablanca")
    if keycode[1] == "2": 
      self.manager.start_game("halloween")

class SlotScreenManager(ScreenManager):
  hardwareButton = Hardware.hardwareButton()

  def start_game(self, theme, *args):
    self.current = "Game Screen"

    self.game_screen.start_game(theme)

class Slot(App):

    def build(self):
      self.root = viewport.Viewport(size=(1920,1080), do_scale=True)
      self.manager = SlotScreenManager()
      self.root.add_widget(self.manager)

      self.manager.start_screen = StartScreen()
      self.manager.add_widget(self.manager.start_screen)

      self.manager.game_screen = GameScreen()
      self.manager.add_widget(self.manager.game_screen)

      self._keyboard = Window.request_keyboard(self._keyboard_closed, self, "text")
      self._keyboard.bind(on_key_down=self.on_keyboard_down)

      self.current = "Start Screen"

      return self.root

    def _keyboard_closed(self):
      self._keyboard.unbind(on_key_down=self._on_keyboard_down)
      self._keyboard = None

    def on_gamepad_down(self, obj, gamepad, buttonid):
      self.manager.current_screen.on_gamepad_down(obj, gamepad, buttonid)

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
      self.manager.current_screen.on_keyboard_down(keycode, keycode, text, modifiers)

    def on_start(self):
        self.spacing = 0.5 * self.root.width
        self.manager.start_screen.build()

        if 0:
          self.slots = self.root.ids.slots
          #self.bird = self.root.ids.bird
          Clock.schedule_interval(self.update, 0.004)

          Window.bind(on_key_down=self.on_key_down)
          self.slots.on_touch_down = self.user_action

    def update(self, nap):
        if self.hardwareButton.checkButton():
            self.user_action()

        self.slots.update()
        if not self.playing:
            return  # don't move bird or pipes

        if self.test_game_over():
            snd_game_over.play()
            self.playing = False


    def user_action(self, *args):
        self.slots.start_spin()

def parse_args(argv):
  parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__)

  parser.add_argument("-t", "--test", dest="test_flag", 
                    default=False,
                    action="store_true",
                    help="Run test function")
  parser.add_argument("--log-level", type=str,
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Desired console log level")
  parser.add_argument("-d", "--debug", dest="log_level", action="store_const",
                      const="DEBUG",
                      help="Activate debugging")
  parser.add_argument("-q", "--quiet", dest="log_level", action="store_const",
                      const="CRITICAL",
                      help="Quite mode")

  args = parser.parse_args(argv[1:])

  return parser, args


def main(argv, stdout, environ):
  if sys.version_info < (3, 0): reload(sys); sys.setdefaultencoding('utf8')

  parser, args = parse_args(argv)

  logging.basicConfig(format="[%(asctime)s] %(levelname)-8s %(message)s", 
                    datefmt="%m/%d %H:%M:%S", level=args.log_level)

  #Config.set('graphics', 'show_cursor', '0')
  if config.window_size:
    Config.set('graphics', 'fullscreen', '1')
    #Window.size = config.window_size

  Window.clearcolor = get_color_from_hex(config.background)
  
  Hardware.setup()

  Slot().run()
  

if __name__ == '__main__':
  main(sys.argv, sys.stdout, os.environ)
