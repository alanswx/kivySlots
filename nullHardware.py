import time



class config:
   window_size=(960, 600)
   window_size=None
   audio_extension='.ogg'

class coinDispense:
     def __init__(self):
        # Set frequency to 60hz, good for servos.
        return


     def dispenseCoin(self,number):
            print("dispense coin:"+str(number))
            for i in range(number):
              print("dispense one coin")
              time.sleep(1)
              time.sleep(1)



class hardwareButton:
     def __init__(self):
         return
     def checkButton(self):
        return False
