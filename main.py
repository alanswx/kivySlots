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
from kivy.utils import get_color_from_hex

class MultiAudio:
    _next = 0

    def __init__(self, filename, count):
        self.buf = [SoundLoader.load(filename)
                    for i in range(count)]

    def play(self):
        self.buf[self._next].play()
        self._next = (self._next + 1) % len(self.buf)

snd_bump = SoundLoader.load('audio/roll.ogg')

class BaseWidget(Widget):
    def load_tileable(self, name):
        print("loading:",name)
        t = Image('img/%s.png' % name).texture
        print("loading:",t)
        t.wrap = 'repeat'
        setattr(self, 'tx_%s' % name, t)

class Slots(BaseWidget):
    tx_stripbig1= ObjectProperty(None)
    tx_stripbig2= ObjectProperty(None)
    tx_stripbig3= ObjectProperty(None)
    sw_seconds=0
    state = 'idle'
    first_stop_length=2.0
    jackpot=0

    #def on_start(self):
    #    Clock.schedule_interval(self.update,0)
    def set_background_size(self, t):
        #t.uvsize = (self.width / t.width, -1)
        t.uvsize = (-1, self.height/t.height)
        t.flip_vertical()

    def set_background_uv(self, name, val):
        t = getattr(self, name)
        #t.uvpos = ((t.uvpos[0] + val) % self.width, t.uvpos[1])
        #print("set uv",val)
        t.uvpos = (t.uvpos[0] , ((t.uvpos[1] + val ) % self.height))
        #print('uvpos:',t.uvpos)
        self.property(name).dispatch(self)

    def __init__(self, **kwargs):
        super(Slots, self).__init__(**kwargs)

        for name in 'stripbig1 stripbig2 stripbig3'.split():
            self.load_tileable(name)

        #self.set_background_uv('tx_stripbig1', random.uniform(1,5))
        #self.set_background_uv('tx_stripbig2', random.uniform(1,5))
        #self.set_background_uv('tx_stripbig3', random.uniform(1,5))
        print("set uv")
        self.set_background_uv('tx_stripbig1', 0)
        self.set_background_uv('tx_stripbig2', 1/6)
        self.set_background_uv('tx_stripbig3', 2/6)

    def on_size(self, *args):
        for t in (self.tx_stripbig1,self.tx_stripbig2,self.tx_stripbig3):
            self.set_background_size(t)

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
            self.set_background_uv('tx_stripbig1', 1 * nap)
            self.set_background_uv('tx_stripbig2', 1.1 * nap)
            self.set_background_uv('tx_stripbig3', 1.2 * nap)
            # check time then switch to next state
            #print(self.sw_seconds)
            if self.sw_seconds > self.first_stop_length+random.uniform(0,0.8):  # snap to next "unit"
                self.state='STATE_SLOT1_STOP'
                print('before round',self.tx_stripbig2.uvpos[1]*6%6)
                slotnum = round(self.tx_stripbig1.uvpos[1]*6%6)
                self.set_background_uv('tx_stripbig1', slotnum/6)
                slotnum=slotnum+1
                if slotnum==4:
                   print('winner')
                   self.jackpot=self.jackpot+1
                print( 'pos:',slotnum)
        elif self.state =='STATE_SLOT1_STOP':
            self.sw_seconds += nap
            self.set_background_uv('tx_stripbig2', 1.1 * nap)
            self.set_background_uv('tx_stripbig3', 1.2 * nap)
            #print(self.sw_seconds)
            if self.sw_seconds > self.first_stop_length+1+random.uniform(0,0.8):  # snap to next "unit"
                self.state='STATE_SLOT2_STOP'
                print('before round',self.tx_stripbig2.uvpos[1]*6%6)
                slotnum = round(self.tx_stripbig2.uvpos[1]*6%6)
                slotnum=slotnum+1
                self.set_background_uv('tx_stripbig2', slotnum/6)
                if slotnum==4:
                   print('winner')
                   self.jackpot=self.jackpot+1
                print( 'pos:',slotnum)
        elif self.state =='STATE_SLOT2_STOP':
            self.sw_seconds += nap
            self.set_background_uv('tx_stripbig3', 1.2 * nap)
            #print(self.sw_seconds)
            if self.sw_seconds > self.first_stop_length+2+random.uniform(0,0.8):  # snap to next "unit"
                self.state='idle'
                print('before round',self.tx_stripbig3.uvpos[1]*6%6)
                slotnum = round(self.tx_stripbig3.uvpos[1]*6%6)
                slotnum=slotnum+1
                self.set_background_uv('tx_stripbig3', slotnum/6)
                if slotnum==4:
                   print('winner')
                   self.jackpot=self.jackpot+1
                print( 'pos:',slotnum)
                print('look for result')

class Slot(App):
    playing = False

    def on_start(self):
        self.spacing = 0.5 * self.root.width

        self.slots = self.root.ids.slots
        #self.bird = self.root.ids.bird
        Clock.schedule_interval(self.update, 0.016)

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


if __name__ == '__main__':
    Window.clearcolor = get_color_from_hex('00bfff')
    Slot().run()
