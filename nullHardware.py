import time
import logging


class config:
   window_size=(960, 600)
   window_size=None
   audio_extension='.ogg'

class coinDispense:
     def __init__(self):
        # Set frequency to 60hz, good for servos.
        return


     def dispenseCoin(self,number):
            logging.warn("dispense coin:"+str(number))
            for i in range(number):
              logging.warn("dispense one coin")



class hardwareButton:
     def __init__(self):
         return
     def checkButton(self):
        return False
