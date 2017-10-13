from __future__ import division
import random

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

class MultiAudio:
    _next = 0

    def __init__(self, filename, count):
        self.buf = [SoundLoader.load(filename)
                    for i in range(count)]

    def play(self):
        self.buf[self._next].play()
        self._next = (self._next + 1) % len(self.buf)

snd_bump = SoundLoader.load('audio/roll.ogg')

class Strip(Rectangle):
  def __init__(self, name, **kwargs):
    super(Strip, self).__init__(**kwargs)

    img = Image('img/%s.png' % name) 
    self.texture = img.texture
    self.texture.wrap = 'repeat'
    
  def set_background_uv(self, canvas, val):
    u = 0
    v = (self.tex_coords[1] - val ) % canvas.height
    w = 1
    h = -.8
    self.tex_coords = [u, v, u+w, v, u+w, v+h, u, v+h]

  def strip_pos(self):
    return round(self.tex_coords[1]*6) % 6
  

class Slots(Widget):
    sw_seconds=0
    state = 'idle'
    first_stop_length=2.0
    jackpot=0

    def __init__(self, **kwargs):
        super(Slots, self).__init__(**kwargs)

        self.strips = []
        with self.canvas:
          for n in range(3):
            strip = Strip("stripbig%d" % (n+1))
            strip.set_background_uv(self, .1+n)
            self.strips.append(strip)

    def on_size(self, *args):
      cx = self.size[0]/2
      ns = len(self.strips)
      sw = self.size[0] / (ns*2)
      mw = 10

      sx = cx - (ns*sw+(ns-1)*mw)/2

      for n, strip in enumerate(self.strips):
        strip.pos = (sx + n*sw + (n-1)*mw, 0)
        strip.size = (sw, self.size[1])

    def start_spin(self):
        if self.state=='idle':
            self.state ='STATE_SPINNING'
            snd_bump.play()
            self.sw_seconds=0
            self.jackpot=0
 
    def update(self, nap):
        if self.state =='idle':
            self.state='idle'
            #
        elif self.state =='STATE_SPINNING':
            self.sw_seconds += nap
            
            for n, strip in enumerate(self.strips):
              strip.set_background_uv(self, (1+((n+1)*.2))*nap)

            # check time then switch to next state
            #print(self.sw_seconds)
            if self.sw_seconds > self.first_stop_length+random.uniform(0,0.8):  # snap to next "unit"
                self.state='STATE_SLOT1_STOP'
                slotnum = round(self.strips[0].strip_pos())
                self.strips[0].set_background_uv(self, slotnum/6)
                slotnum=slotnum+1
                if slotnum==4:
                   print('winner')
                   self.jackpot=self.jackpot+1
                print( 'pos:',slotnum)

        elif self.state =='STATE_SLOT1_STOP':
            self.sw_seconds += nap
            self.strips[1].set_background_uv(self, 1.1 * nap)
            self.strips[2].set_background_uv(self, 1.2 * nap)

            #print(self.sw_seconds)
            if self.sw_seconds > self.first_stop_length+1+random.uniform(0,0.8):  # snap to next "unit"
                self.state='STATE_SLOT2_STOP'
                slotnum = round(self.strips[1].strip_pos())
                slotnum=slotnum+1
                self.strips[1].set_background_uv(self, slotnum/6)
                if slotnum==4:
                   print('winner')
                   self.jackpot=self.jackpot+1
                print( 'pos:',slotnum)
        elif self.state =='STATE_SLOT2_STOP':
            self.sw_seconds += nap
            self.strips[2].set_background_uv(self, 1.2 * nap)
            #print(self.sw_seconds)
            if self.sw_seconds > self.first_stop_length+2+random.uniform(0,0.8):  # snap to next "unit"
                self.state='FINAL'
                slotnum = round(self.strips[2].strip_pos())
                slotnum=slotnum+1
                self.strips[2].set_background_uv(self, slotnum/6)
                if slotnum==4:
                   print('winner')
                   self.jackpot=self.jackpot+1
                print( 'pos:',slotnum)
                print('look for result')
        elif self.state =='FINAL':
                print('total jackpot:',self.jackpot)
                self.state='idle'

class Slot(App):
    playing = False

    def on_start(self):
        self.spacing = 0.5 * self.root.width

        self.slots = self.root.ids.slots
        #self.bird = self.root.ids.bird
        Clock.schedule_interval(self.update, 0.004)

        Window.bind(on_key_down=self.on_key_down)
        self.slots.on_touch_down = self.user_action

    def update(self, nap):
        self.slots.update(nap)
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

def start():
  #Config.set('graphics', 'fullscreen', '1')
  #Config.set('graphics', 'show_cursor', '0')
  Window.size = (1920, 1200)

  Window.clearcolor = get_color_from_hex('00bfff')
  
  Slot().run()
  

if __name__ == '__main__':
  start()
