import os
import logging
#
# without this - sound was really delayed, not sure why
#
os.environ['KIVY_AUDIO'] = 'sdl2'

import RPi.GPIO as GPIO
import time
import config

# Import the PCA9685 module.
import Adafruit_PCA9685

class coinDispense:
     def __init__(self):
        self.pwm = Adafruit_PCA9685.PCA9685()
        # Configure min and max servo pulse lengths
        self.servo_min = config.servo_min  # Min pulse length out of 4096
        self.servo_max = config.servo_max  # Max pulse length out of 4096
        # Set frequency to 60hz, good for servos.
        self.pwm.set_pwm_freq(60)

        self.next_servo = 0

     def dispenseCoin(self,number):
         logging.info("dispensing {} coins".format(number))

         for i in range(number):
           logging.info("dispense one coin on servo #{}".format(self.next_servo))
           self.pwm.set_pwm(self.next_servo, 0, self.servo_max)
           time.sleep(1)
           self.pwm.set_pwm(self.next_servo, 0, self.servo_min)
           time.sleep(1)

           self.next_servo = (self.next_servo + 1) % config.num_servos

class hardwareButton:
     def __init__(self):
       GPIO.setmode(GPIO.BCM)
       GPIO.setup(config.gpio_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

       self.debounce = False

     def checkButton(self):
        input_state = GPIO.input(config.gpio_button)
        if self.debounce == True:
          if input_state == True:
            self.debounce = False
          return False

        if input_state == False:
            logging.warn('Button Pressed')
            self.debounce = True
            return True
        return False
