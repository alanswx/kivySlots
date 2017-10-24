#!/usr/bin/env python3
from __future__ import division

import random
import os, sys, time, math, logging, argparse, glob

import config

try:
  import piHardware as Hardware
except ImportError:
  import nullHardware as Hardware


from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.image import Image
from kivy.core.window import Window, Keyboard
from kivy.properties import (AliasProperty,
                             ListProperty,
                             NumericProperty,
                             ObjectProperty)
from kivy.uix.image import Image as ImageWidget
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.utils import get_color_from_hex
from kivy.config import Config


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

      self.start_time=time.time()

      self.strips = []
      with self.canvas:
        for n in range(3):
          strip = Strip(Image(os.path.join("themes", config.theme, "images", "stripbig1.png")))
          strip.set_uv(self, strip.slot_to_uv(0))
          self.strips.append(strip)
        Color(1,0,0)
        self.payline = Rectangle()
      self.last_time = time.time()

      self.sounds = {}
      files = glob.glob(os.path.join("themes", config.theme, 'audio', "*" + config.audio_extension))
      files += glob.glob(os.path.join("themes", config.theme, 'audio', "*/*" + config.audio_extension))
      for fn in files:
        path, f = os.path.split(fn)
        f, ext = os.path.splitext(f)
        snd = SoundLoader.load(fn)
        self.sounds[f] = snd

    def on_size(self, *args):
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
          #self.strips[n].add_uv(self, v * min(.2, 100-dt/100))
          self.strips[n].add_uv(self, v * dtt)

        #print("{} {}".format(self.strips[0].strip_pos(), self.strips[0].get_uv()[1]))

        #self.state = "key"

        # check time then switch to next state

        if dt > self.first_stop_length+self.stopped +random.uniform(0,0.8):  # snap to next "unit"
          slotnum = self.strips[self.stopped].strip_pos()
          self.strips[self.stopped].set_uv(self, self.strips[self.stopped].slot_to_uv(slotnum))
          # play sound for slot
          self.sounds['reel-icon-%d' % slotnum].play()
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

class Slot(App):
    playing = False
    hardwareButton = Hardware.hardwareButton()

    def on_start(self):
        self.spacing = 0.5 * self.root.width

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

    def on_key_down(self, window, key, *args):
        if key == Keyboard.keycodes['spacebar']:
            self.user_action()

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

  Window.clearcolor = get_color_from_hex('00bfff')
  
  Slot().run()
  

if __name__ == '__main__':
  main(sys.argv, sys.stdout, os.environ)
